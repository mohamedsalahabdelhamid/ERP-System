from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.modules.items.service import get_item
from app.modules.partners.service import get_partner
from app.modules.payments.models import Payment
from app.modules.pos.models import PosOrder, PosOrderLine, PosSession
from app.modules.pos.schemas import PosOrderCreate, PosSessionClose, PosSessionCreate
from app.modules.sales import service as sales_service
from app.modules.sales.schemas import SalesInvoiceCreate, SalesInvoiceLineCreate


def _now_str() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def list_sessions(db: Session, company_id: int) -> list[PosSession]:
    stmt = (
        select(PosSession)
        .where(PosSession.company_id == company_id)
        .order_by(PosSession.id.desc())
    )
    return list(db.scalars(stmt).all())


def get_session(db: Session, company_id: int, session_id: int) -> PosSession | None:
    return db.scalar(
        select(PosSession).where(
            PosSession.id == session_id, PosSession.company_id == company_id
        )
    )


def open_session(
    db: Session, company_id: int, user_id: int, data: PosSessionCreate
) -> PosSession:
    session = PosSession(
        company_id=company_id,
        branch_id=data.branch_id,
        opened_by=user_id,
        opened_at=_now_str(),
        opening_cash=data.opening_cash,
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


def close_session(
    db: Session, session: PosSession, data: PosSessionClose
) -> PosSession:
    if session.status == "closed":
        raise ValueError("Session is already closed.")

    total_sales = db.scalar(
        select(func.coalesce(func.sum(PosOrder.total), 0)).where(
            PosOrder.session_id == session.id, PosOrder.status == "completed"
        )
    )
    expected = float(session.opening_cash or 0) + float(total_sales or 0)
    closing = float(data.closing_cash or 0)

    session.expected_cash = expected
    session.closing_cash = closing
    session.variance = closing - expected
    session.closed_at = _now_str()
    session.status = "closed"
    db.commit()
    db.refresh(session)
    return session


def list_orders(
    db: Session, company_id: int, session_id: int | None = None
) -> list[PosOrder]:
    stmt = (
        select(PosOrder)
        .where(PosOrder.company_id == company_id)
        .order_by(PosOrder.id.desc())
    )
    if session_id is not None:
        stmt = stmt.where(PosOrder.session_id == session_id)
    return list(db.scalars(stmt).all())


def create_order(
    db: Session, company_id: int, user_id: int, data: PosOrderCreate
) -> PosOrder:
    session = get_session(db, company_id, data.session_id)
    if session is None:
        raise ValueError("POS session not found in this company.")
    if session.status != "open":
        raise ValueError("POS session is not open.")

    # Resolve partner: use provided partner or fall back to a walk-in partner.
    partner_id = data.partner_id
    if partner_id is None:
        # Get or create the walk-in customer for this company
        from sqlalchemy import select as _select
        from app.modules.partners.models import Partner
        walkin = db.scalar(
            _select(Partner).where(
                Partner.company_id == company_id,
                Partner.code == "WALKIN",
            )
        )
        if walkin is None:
            walkin = Partner(
                company_id=company_id,
                name="Walk-in Customer",
                code="WALKIN",
                type="customer",
                is_active=True,
            )
            db.add(walkin)
            db.flush()
        partner_id = walkin.id
    else:
        partner = get_partner(db, company_id, partner_id)
        if partner is None:
            raise ValueError("partner_id not found in this company.")

    # Validate items and compute the total.
    total = 0.0
    for line in data.lines:
        item = get_item(db, company_id, line.item_id)
        if item is None:
            raise ValueError(f"item_id {line.item_id} not found in this company.")
        total += float(line.quantity) * float(line.unit_price)

    seq = (
        db.scalar(
            select(func.count(PosOrder.id)).where(PosOrder.session_id == session.id)
        )
        or 0
    ) + 1
    order_number = f"POS-{session.id}-{seq}"

    # Post a confirmed sales invoice for full back-office traceability.
    invoice = sales_service.create_invoice(
        db,
        company_id,
        SalesInvoiceCreate(
            partner_id=partner_id,
            number=order_number,
            date=datetime.now(),
            currency_code=data.currency_code,
            fx_rate=data.fx_rate,
            lines=[
                SalesInvoiceLineCreate(
                    item_id=line.item_id,
                    description=f"POS order {order_number}",
                    quantity=line.quantity,
                    unit_price=line.unit_price,
                )
                for line in data.lines
            ],
        ),
    )
    invoice = sales_service.confirm_invoice(db, invoice)

    order = PosOrder(
        company_id=company_id,
        session_id=session.id,
        invoice_id=invoice.id,
        order_number=order_number,
        partner_id=partner_id,
        cashier_id=data.cashier_id or user_id,
        total=total,
    )
    db.add(order)
    db.flush()

    for line in data.lines:
        line_total = float(line.quantity) * float(line.unit_price)
        db.add(
            PosOrderLine(
                order_id=order.id,
                item_id=line.item_id,
                quantity=line.quantity,
                unit_price=line.unit_price,
                line_total=line_total,
            )
        )

    if data.payment_method and total > 0:
        db.add(
            Payment(
                company_id=company_id,
                partner_id=partner_id,
                reference=f"PAY-{order_number}",
                document_type="sales_invoice",
                document_id=invoice.id,
                payment_date=_now_str(),
                amount=total,
                currency_code=data.currency_code,
                payment_method=data.payment_method,
                notes=f"POS order {order_number}",
            )
        )

    db.commit()
    db.refresh(order)
    return order
