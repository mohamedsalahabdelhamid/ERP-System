from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.inventory.models import InventoryMovement, Warehouse, WarehouseStock
from app.modules.items.service import get_item
from app.modules.partners.service import get_partner
from app.modules.sales.models import SalesInvoice, SalesInvoiceLine
from app.modules.sales.schemas import (
    SalesInvoiceCreate,
    SalesInvoiceLineCreate,
    SalesInvoiceUpdate,
)
from app.modules.accounting.service import get_or_create_default_account, create_journal_entry
from app.modules.accounting.schemas import JournalEntryCreate, JournalLineCreate



def _get_line_value(line, field: str):
    return line[field] if isinstance(line, dict) else getattr(line, field)


def _calculate_line_totals(line: SalesInvoiceLineCreate) -> tuple[float, float, float]:
    line_total = _get_line_value(line, "quantity") * _get_line_value(line, "unit_price")
    return line_total, 0.0, 0.0


def list_invoices(db: Session, company_id: int) -> list[SalesInvoice]:
    stmt = (
        select(SalesInvoice)
        .where(SalesInvoice.company_id == company_id)
        .order_by(SalesInvoice.date.desc())
    )
    return list(db.scalars(stmt).all())


def get_invoice(db: Session, company_id: int, invoice_id: int) -> SalesInvoice | None:
    stmt = select(SalesInvoice).where(
        SalesInvoice.id == invoice_id, SalesInvoice.company_id == company_id
    )
    return db.scalar(stmt)


def invoice_number_exists(db: Session, company_id: int, number: str, exclude_id: int | None = None) -> bool:
    stmt = select(SalesInvoice.id).where(
        SalesInvoice.company_id == company_id, SalesInvoice.number == number
    )
    if exclude_id is not None:
        stmt = stmt.where(SalesInvoice.id != exclude_id)
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


def _create_lines(db: Session, invoice: SalesInvoice, lines: list[SalesInvoiceLineCreate]) -> None:
    for line in lines:
        line_total, cost_price, total_cost = _calculate_line_totals(line)
        item_id = _get_line_value(line, "item_id")
        description = _get_line_value(line, "description")
        quantity = _get_line_value(line, "quantity")
        unit_price = _get_line_value(line, "unit_price")
        db.add(
            SalesInvoiceLine(
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


def _calculate_totals(db: Session, invoice: SalesInvoice) -> None:
    stmt = select(SalesInvoiceLine).where(SalesInvoiceLine.invoice_id == invoice.id)
    lines = list(db.scalars(stmt).all())
    total_amount = sum(float(line.line_total) for line in lines)
    invoice.total_amount = total_amount
    invoice.total_amount_base = total_amount * float(invoice.fx_rate)


def create_invoice(
    db: Session, company_id: int, data: SalesInvoiceCreate, commit: bool = True
) -> SalesInvoice:
    """Create an invoice (draft). ``commit=False`` lets callers (e.g. POS)
    compose this inside a single atomic transaction."""
    payload = data.model_dump()
    _validate_invoice_data(db, company_id, payload)
    invoice = SalesInvoice(
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


def update_invoice(db: Session, invoice: SalesInvoice, data: SalesInvoiceUpdate) -> SalesInvoice:
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


def delete_invoice(db: Session, invoice: SalesInvoice, commit: bool = True) -> None:
    if invoice.is_confirmed:
        raise ValueError(
            "Cannot delete a confirmed sales invoice; reverse it with a credit note."
        )
    db.delete(invoice)
    if commit:
        db.commit()


def confirm_invoice(
    db: Session, invoice: SalesInvoice, commit: bool = True
) -> SalesInvoice:
    if invoice.is_confirmed:
        return invoice

    # Load company settings for stock control
    from app.modules.companies.models import CompanySettings, Company
    company_settings = db.get(CompanySettings, invoice.company_id)
    company = db.get(Company, invoice.company_id)
    block_negative = (company_settings.block_negative_stock if company_settings else True)

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

    lines = list(db.scalars(select(SalesInvoiceLine).where(SalesInvoiceLine.invoice_id == invoice.id)).all())

    # ---- Pre-flight: check all lines have sufficient stock ----
    if block_negative:
        for line in lines:
            stock = db.scalar(
                select(WarehouseStock).where(
                    WarehouseStock.company_id == invoice.company_id,
                    WarehouseStock.warehouse_id == warehouse.id,
                    WarehouseStock.item_id == line.item_id,
                )
            )
            available = float(stock.quantity) if stock else 0.0
            if available < float(line.quantity or 0):
                from app.modules.items.models import Item
                item = db.get(Item, line.item_id)
                item_name = item.name if item else f"Item#{line.item_id}"
                raise ValueError(
                    f"Insufficient stock for '{item_name}': "
                    f"available {available:.2f}, requested {float(line.quantity):.2f}. "
                    f"Cannot sell below zero stock."
                )

    total_cogs = 0.0
    low_stock_alerts = []  # collect items that need alerts after commit

    for line in lines:
        # FOR UPDATE: serialize concurrent confirmations on the same stock row,
        # then re-verify stock after acquiring the lock so two parallel sales
        # can never push the quantity negative.
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

        old_qty = float(stock.quantity or 0)
        old_cost = float(stock.average_cost or 0)
        unit_cost = old_cost
        total_cost = float(line.quantity or 0) * unit_cost
        new_qty = old_qty - float(line.quantity or 0)
        if block_negative and new_qty < 0:
            from app.modules.items.models import Item
            item = db.get(Item, line.item_id)
            item_name = item.name if item else f"Item#{line.item_id}"
            raise ValueError(
                f"Insufficient stock for '{item_name}': "
                f"available {old_qty:.2f}, requested {float(line.quantity):.2f}. "
                f"Cannot sell below zero stock."
            )
        new_avg_cost = old_cost if new_qty != 0 else 0
        stock.quantity = new_qty
        stock.average_cost = new_avg_cost

        db.add(
            InventoryMovement(
                company_id=invoice.company_id,
                item_id=line.item_id,
                warehouse_from_id=warehouse.id,
                quantity=float(line.quantity or 0),
                movement_type="sale_out",
                unit_cost=unit_cost,
                total_cost=total_cost,
                document_type="sales_invoice",
                document_id=invoice.id,
            )
        )
        total_cogs += total_cost

        # Check low-stock threshold for alert
        if company_settings:
            from app.modules.items.models import Item
            item = db.get(Item, line.item_id)
            # Use item-level threshold if set, else company-level threshold
            threshold = float(item.min_stock_level or 0) if item else 0.0
            if threshold == 0:
                threshold = float(company_settings.low_stock_threshold or 0)
            if threshold > 0 and new_qty <= threshold:
                low_stock_alerts.append({
                    "item_name": item.name if item else f"Item#{line.item_id}",
                    "item_code": item.code if item else "",
                    "current_qty": new_qty,
                    "threshold_qty": threshold,
                    "warehouse_name": warehouse.name,
                })

    # Accounting Integration
    ar_account = get_or_create_default_account(db, invoice.company_id, "receivable", "1100", "Accounts Receivable")
    rev_account = get_or_create_default_account(db, invoice.company_id, "revenue", "4100", "Sales Revenue")
    cogs_account = get_or_create_default_account(db, invoice.company_id, "cogs", "5100", "Cost of Goods Sold")
    inv_account = get_or_create_default_account(db, invoice.company_id, "inventory", "1200", "Inventory")

    je_lines = [
        JournalLineCreate(account_id=ar_account.id, debit=float(invoice.total_amount_base or 0), credit=0.0, description="Sale AR"),
        JournalLineCreate(account_id=rev_account.id, debit=0.0, credit=float(invoice.total_amount_base or 0), description="Sale Revenue")
    ]
    if total_cogs > 0:
        je_lines.append(JournalLineCreate(account_id=cogs_account.id, debit=total_cogs, credit=0.0, description="COGS"))
        je_lines.append(JournalLineCreate(account_id=inv_account.id, debit=0.0, credit=total_cogs, description="Inventory out"))

    create_journal_entry(db, invoice.company_id, JournalEntryCreate(
        reference=f"INV-{invoice.number}",
        entry_date=invoice.date.strftime("%Y-%m-%d %H:%M:%S"),
        notes=f"Sales Invoice {invoice.number}",
        lines=je_lines
    ), commit=False)

    invoice.is_confirmed = True
    if commit:
        db.commit()
    db.refresh(invoice)

    # ---- Send low-stock alert emails (after commit, best-effort) ----
    if low_stock_alerts and company_settings and company_settings.alert_emails:
        from app.core.email_service import send_low_stock_alert
        recipients = [e.strip() for e in company_settings.alert_emails.split(",") if e.strip()]
        company_name = company.name if company else "ERP System"
        send_low_stock_alert(company_name, recipients, low_stock_alerts)

    return invoice
