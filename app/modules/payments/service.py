from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.accounting.schemas import JournalEntryCreate, JournalLineCreate
from app.modules.accounting.service import (
    create_journal_entry,
    get_or_create_default_account,
)
from app.modules.partners.service import get_partner
from app.modules.payments.models import Payment
from app.modules.payments.schemas import PaymentCreate
from app.modules.purchases.models import PurchaseInvoice
from app.modules.sales.models import SalesInvoice


def list_payments(db: Session, company_id: int) -> list[Payment]:
    stmt = (
        select(Payment)
        .where(Payment.company_id == company_id)
        .order_by(Payment.payment_date.desc(), Payment.id.desc())
    )
    return list(db.scalars(stmt).all())


def _invoice_rate(
    db: Session, company_id: int, document_type: str, document_id: int
) -> tuple[float, str]:
    """Return (fx_rate, kind) of the settled invoice, or (1.0, None)."""
    if document_type in ("invoice", "sale", "sales"):
        inv = db.scalar(
            select(SalesInvoice).where(
                SalesInvoice.id == document_id,
                SalesInvoice.company_id == company_id,
            )
        )
        if inv is not None:
            return float(inv.fx_rate or 1), "sale"
        return 1.0, None
    if document_type in ("purchase", "purchases"):
        inv = db.scalar(
            select(PurchaseInvoice).where(
                PurchaseInvoice.id == document_id,
                PurchaseInvoice.company_id == company_id,
            )
        )
        if inv is not None:
            return float(inv.fx_rate or 1), "purchase"
        return 1.0, None
    return 1.0, None


def create_payment(db: Session, company_id: int, data: PaymentCreate) -> Payment:
    partner = get_partner(db, company_id, data.partner_id)
    if partner is None:
        raise ValueError("partner_id not found in this company.")

    invoice_rate, kind = _invoice_rate(
        db, company_id, data.document_type, data.document_id
    )
    payment_rate = data.fx_rate_used if data.fx_rate_used else invoice_rate
    base_amount = float(data.amount) * float(payment_rate)

    gain_loss = 0.0
    if data.document_type in ("invoice", "sale", "sales") and kind == "sale":
        # Receivable: base amount above the invoiced base = realized gain.
        gain_loss = float(data.amount) * (
            float(payment_rate) - float(invoice_rate)
        )
    elif data.document_type in ("purchase", "purchases") and kind == "purchase":
        # Payable: paying less in base terms than the invoice recorded = gain.
        gain_loss = float(data.amount) * (
            float(invoice_rate) - float(payment_rate)
        )

    payment = Payment(
        company_id=company_id,
        partner_id=data.partner_id,
        reference=data.reference,
        document_type=data.document_type,
        document_id=data.document_id,
        payment_date=data.payment_date,
        amount=data.amount,
        currency_code=data.currency_code,
        fx_rate_used=payment_rate,
        base_amount=base_amount,
        fx_gain_loss=round(gain_loss, 4),
        payment_method=data.payment_method,
        notes=data.notes,
    )
    db.add(payment)
    db.flush()

    _post_fx_entry(db, company_id, payment, invoice_rate, kind)

    db.commit()
    db.refresh(payment)
    return payment


def _post_fx_entry(
    db: Session,
    company_id: int,
    payment: Payment,
    invoice_rate: float,
    kind: str,
) -> None:
    """Post a balanced journal entry for realized FX gain/loss on settlement."""
    diff = float(payment.fx_gain_loss)
    if abs(diff) < 0.005 or kind not in ("sale", "purchase"):
        return

    cash = get_or_create_default_account(
        db, company_id, "asset", "1000", "Cash"
    )
    gain = get_or_create_default_account(
        db, company_id, "income", "6100", "FX Gain"
    )
    loss = get_or_create_default_account(
        db, company_id, "expense", "6200", "FX Loss"
    )

    base_amount = float(payment.base_amount)
    invoice_base_of_paid = float(payment.amount) * float(invoice_rate)

    if kind == "sale":
        ar = get_or_create_default_account(
            db, company_id, "receivable", "1100", "Accounts Receivable"
        )
        lines = [
            JournalLineCreate(
                account_id=cash.id,
                debit=base_amount,
                credit=0.0,
                description="Payment received",
            ),
            JournalLineCreate(
                account_id=ar.id,
                debit=0.0,
                credit=invoice_base_of_paid,
                description="Settle receivable",
            ),
        ]
        if diff > 0:
            lines.append(
                JournalLineCreate(
                    account_id=gain.id, debit=0.0, credit=diff, description="FX gain"
                )
            )
        else:
            lines.append(
                JournalLineCreate(
                    account_id=loss.id,
                    debit=abs(diff),
                    credit=0.0,
                    description="FX loss",
                )
            )
    else:  # purchase
        ap = get_or_create_default_account(
            db, company_id, "payable", "2100", "Accounts Payable"
        )
        lines = [
            JournalLineCreate(
                account_id=ap.id,
                debit=invoice_base_of_paid,
                credit=0.0,
                description="Settle payable",
            ),
            JournalLineCreate(
                account_id=cash.id,
                debit=0.0,
                credit=base_amount,
                description="Payment made",
            ),
        ]
        if diff > 0:
            lines.append(
                JournalLineCreate(
                    account_id=gain.id, debit=0.0, credit=diff, description="FX gain"
                )
            )
        else:
            lines.append(
                JournalLineCreate(
                    account_id=loss.id,
                    debit=abs(diff),
                    credit=0.0,
                    description="FX loss",
                )
            )

    create_journal_entry(
        db,
        company_id,
        JournalEntryCreate(
            reference=payment.reference,
            entry_date=payment.payment_date,
            notes="FX gain/loss on settlement",
            lines=lines,
        ),
    )
