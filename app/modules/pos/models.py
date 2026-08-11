from typing import Optional

from sqlalchemy import ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base_class import Base
from app.db.mixins import TimestampMixin


class PosSession(TimestampMixin, Base):
    """A cashier's open/shift at a POS register (spec 6.3)."""

    __tablename__ = "pos_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    company_id: Mapped[int] = mapped_column(
        ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True
    )
    branch_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("branches.id", ondelete="SET NULL"), nullable=True
    )
    opened_by: Mapped[int] = mapped_column(Integer, nullable=False)
    opened_at: Mapped[str] = mapped_column(String(30), nullable=False)
    closed_at: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    opening_cash: Mapped[float] = mapped_column(
        Numeric(18, 4), nullable=False, default=0
    )
    closing_cash: Mapped[float] = mapped_column(
        Numeric(18, 4), nullable=False, default=0
    )
    expected_cash: Mapped[float] = mapped_column(
        Numeric(18, 4), nullable=False, default=0
    )
    variance: Mapped[float] = mapped_column(
        Numeric(18, 4), nullable=False, default=0
    )
    # status: open / closed
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="open")


class PosOrder(TimestampMixin, Base):
    """A completed POS sale. Links to a sales invoice for back-office traceability."""

    __tablename__ = "pos_orders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    company_id: Mapped[int] = mapped_column(
        ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True
    )
    session_id: Mapped[int] = mapped_column(
        ForeignKey("pos_sessions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    invoice_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("sales_invoices.id", ondelete="SET NULL"), nullable=True
    )
    order_number: Mapped[str] = mapped_column(String(50), nullable=False)
    partner_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("partners.id", ondelete="SET NULL"), nullable=True
    )
    cashier_id: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total: Mapped[float] = mapped_column(Numeric(18, 4), nullable=False, default=0)
    # status: completed / void
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="completed")


class PosOrderLine(TimestampMixin, Base):
    __tablename__ = "pos_order_lines"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    order_id: Mapped[int] = mapped_column(
        ForeignKey("pos_orders.id", ondelete="CASCADE"), nullable=False, index=True
    )
    item_id: Mapped[int] = mapped_column(
        ForeignKey("items.id", ondelete="CASCADE"), nullable=False, index=True
    )
    quantity: Mapped[float] = mapped_column(Numeric(18, 4), nullable=False, default=1)
    unit_price: Mapped[float] = mapped_column(
        Numeric(18, 4), nullable=False, default=0
    )
    line_total: Mapped[float] = mapped_column(
        Numeric(18, 4), nullable=False, default=0
    )
