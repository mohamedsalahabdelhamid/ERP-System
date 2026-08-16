from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.inventory.models import InventoryMovement, Warehouse, WarehouseStock
from app.modules.items.service import get_item
from app.modules.partners.service import get_partner
from app.modules.purchases.models import PurchaseInvoice, PurchaseInvoiceLine
from app.modules.purchases.schemas import (
    PurchaseInvoiceCreate,
    PurchaseInvoiceLineCreate,
    PurchaseInvoiceUpdate,
)
from app.modules.accounting.service import get_or_create_default_account, create_journal_entry
from app.modules.accounting.schemas import JournalEntryCreate, JournalLineCreate



def _get_line_value(line, field: str):
    return line[field] if isinstance(line, dict) else getattr(line, field)


def _calculate_line_totals(line: PurchaseInvoiceLineCreate) -> tuple[float, float, float]:
    line_total = _get_line_value(line, "quantity") * _get_line_value(line, "unit_price")
    return line_total, 0.0, 0.0


def list_invoices(db: Session, company_id: int) -> list[PurchaseInvoice]:
    stmt = (
        select(PurchaseInvoice)
        .where(PurchaseInvoice.company_id == company_id)
        .order_by(PurchaseInvoice.date.desc())
    )
    return list(db.scalars(stmt).all())


def get_invoice(db: Session, company_id: int, invoice_id: int) -> PurchaseInvoice | None:
    stmt = select(PurchaseInvoice).where(
        PurchaseInvoice.id == invoice_id, PurchaseInvoice.company_id == company_id
    )
    return db.scalar(stmt)


def invoice_number_exists(db: Session, company_id: int, number: str, exclude_id: int | None = None) -> bool:
    stmt = select(PurchaseInvoice.id).where(
        PurchaseInvoice.company_id == company_id, PurchaseInvoice.number == number
    )
    if exclude_id is not None:
        stmt = stmt.where(PurchaseInvoice.id != exclude_id)
    return db.scalar(stmt.limit(1)) is not None


def _validate_invoice_data(db: Session, company_id: int, data: dict) -> None:
    partner = get_partner(db, company_id, data["partner_id"])
    if partner is None:
        raise ValueError("partner_id not found in this company.")
    for line in data["lines"]:
        item_id = line["item_id"] if isinstance(line, dict) else line.item_id
        item = get_item(db, company_id, item_id)
        if item is None:
            raise ValueError(f"item_id {item_id} not found in this company.")


def _create_lines(db: Session, invoice: PurchaseInvoice, lines: list[PurchaseInvoiceLineCreate]) -> None:
    for line in lines:
        line_total, cost_price, total_cost = _calculate_line_totals(line)
        item_id = _get_line_value(line, "item_id")
        description = _get_line_value(line, "description")
        quantity = _get_line_value(line, "quantity")
        unit_price = _get_line_value(line, "unit_price")
        db.add(
            PurchaseInvoiceLine(
                invoice_id=invoice.id,
                item_id=item_id,
                description=description,
                quantity=quantity,
                unit_price=unit_price,
                line_total=line_total,
                cost_price=cost_price,
                total_cost=total_cost,
            )
        )


def _calculate_totals(db: Session, invoice: PurchaseInvoice) -> None:
    stmt = select(PurchaseInvoiceLine).where(PurchaseInvoiceLine.invoice_id == invoice.id)
    lines = list(db.scalars(stmt).all())
    total_amount = sum(float(line.line_total) for line in lines)
    invoice.total_amount = total_amount
    invoice.total_amount_base = total_amount * float(invoice.fx_rate)


def create_invoice(
    db: Session, company_id: int, data: PurchaseInvoiceCreate, commit: bool = True
) -> PurchaseInvoice:
    """Create an invoice (draft). ``commit=False`` lets callers compose this
    inside a single atomic transaction."""
    payload = data.model_dump()
    _validate_invoice_data(db, company_id, payload)
    invoice = PurchaseInvoice(
        company_id=company_id,
        partner_id=payload["partner_id"],
        number=payload["number"],
        date=payload["date"],
        currency_code=payload["currency_code"],
        fx_rate=payload["fx_rate"],
    )
    db.add(invoice)
    db.flush()
    db.refresh(invoice)
    _create_lines(db, invoice, payload["lines"])
    db.flush()
    _calculate_totals(db, invoice)
    db.flush()
    if commit:
        db.commit()
    db.refresh(invoice)
    return invoice


def update_invoice(db: Session, invoice: PurchaseInvoice, data: PurchaseInvoiceUpdate) -> PurchaseInvoice:
    payload = data.model_dump(exclude_unset=True)
    if "partner_id" in payload:
        partner = get_partner(db, invoice.company_id, payload["partner_id"])
        if partner is None:
            raise ValueError("partner_id not found in this company.")
    if "lines" in payload:
        raise ValueError("Updating lines is not supported yet.")
    for field, value in payload.items():
        setattr(invoice, field, value)
    _calculate_totals(db, invoice)
    db.commit()
    db.refresh(invoice)
    return invoice


def delete_invoice(db: Session, invoice: PurchaseInvoice, commit: bool = True) -> None:
    if invoice.is_confirmed:
        raise ValueError(
            "Cannot delete a confirmed purchase invoice; reverse it with a debit note."
        )
    db.delete(invoice)
    if commit:
        db.commit()


def confirm_invoice(
    db: Session, invoice: PurchaseInvoice, commit: bool = True
) -> PurchaseInvoice:
    if invoice.is_confirmed:
        return invoice

    warehouse = (
        db.scalar(
            select(Warehouse).where(
                Warehouse.company_id == invoice.company_id,
                Warehouse.is_active.is_(True),
            )
        )
        or None
    )
    if warehouse is None:
        raise ValueError("No active warehouse found for this company.")

    fx_rate = float(invoice.fx_rate or 1.0)
    total_inventory_value = 0.0

    lines = list(db.scalars(select(PurchaseInvoiceLine).where(PurchaseInvoiceLine.invoice_id == invoice.id)).all())
    for line in lines:
        # FOR UPDATE: serialize concurrent receipts on the same stock row.
        stock = db.scalar(
            select(WarehouseStock)
            .where(
                WarehouseStock.company_id == invoice.company_id,
                WarehouseStock.warehouse_id == warehouse.id,
                WarehouseStock.item_id == line.item_id,
            )
            .with_for_update()
        )
        if stock is None:
            stock = WarehouseStock(
                company_id=invoice.company_id,
                warehouse_id=warehouse.id,
                item_id=line.item_id,
                quantity=0,
                average_cost=0,
            )
            db.add(stock)

        unit_cost = float(line.unit_price or 0) * fx_rate
        total_cost = float(line.line_total or 0) * fx_rate
        old_qty = float(stock.quantity or 0)
        old_cost = float(stock.average_cost or 0)
        new_qty = old_qty + float(line.quantity or 0)
        if new_qty == 0:
            new_avg_cost = 0
        else:
            new_avg_cost = ((old_qty * old_cost) + total_cost) / new_qty
        stock.quantity = new_qty
        stock.average_cost = new_avg_cost

        db.add(
            InventoryMovement(
                company_id=invoice.company_id,
                item_id=line.item_id,
                warehouse_to_id=warehouse.id,
                quantity=float(line.quantity or 0),
                movement_type="purchase_in",
                unit_cost=unit_cost,
                total_cost=total_cost,
                document_type="purchase_invoice",
                document_id=invoice.id,
            )
        )
        total_inventory_value += total_cost

    # Accounting Integration
    ap_account = get_or_create_default_account(db, invoice.company_id, "payable", "2100", "Accounts Payable")
    inv_account = get_or_create_default_account(db, invoice.company_id, "inventory", "1200", "Inventory")

    je_lines = [
        JournalLineCreate(account_id=inv_account.id, debit=total_inventory_value, credit=0.0, description="Purchase Inventory In"),
        JournalLineCreate(account_id=ap_account.id, debit=0.0, credit=float(invoice.total_amount_base or 0), description="Purchase AP")
    ]

    create_journal_entry(db, invoice.company_id, JournalEntryCreate(
        reference=f"PINV-{invoice.number}",
        entry_date=invoice.date.strftime("%Y-%m-%d %H:%M:%S"),
        notes=f"Purchase Invoice {invoice.number}",
        lines=je_lines
    ), commit=False)

    invoice.is_confirmed = True
    if commit:
        db.commit()
    db.refresh(invoice)
    return invoice
