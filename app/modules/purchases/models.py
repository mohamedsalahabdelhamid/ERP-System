from typing import Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base_class import Base
from app.db.mixins import TimestampMixin


class PurchaseInvoice(TimestampMixin, Base):
    __tablename__ = "purchase_invoices"
    __table_args__ = (
        UniqueConstraint("company_id", "number", name="uq_purchase_invoices_company_number"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    company_id: Mapped[int] = mapped_column(
        ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True
    )
    partner_id: Mapped[int] = mapped_column(
        ForeignKey("partners.id", ondelete="SET NULL"), nullable=False, index=True
    )
    number: Mapped[str] = mapped_column(String(50), nullable=False)
    date: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=False)
    currency_code: Mapped[str] = mapped_column(String(10), nullable=False)
    fx_rate: Mapped[float] = mapped_column(Numeric(18, 8), nullable=False, default=1)
    total_amount: Mapped[float] = mapped_column(Numeric(18, 4), nullable=False, default=0)
    total_amount_base: Mapped[float] = mapped_column(Numeric(18, 4), nullable=False, default=0)
    is_confirmed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)


class PurchaseInvoiceLine(TimestampMixin, Base):
    __tablename__ = "purchase_invoice_lines"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    invoice_id: Mapped[int] = mapped_column(
        ForeignKey("purchase_invoices.id", ondelete="CASCADE"), nullable=False, index=True
    )
    item_id: Mapped[int] = mapped_column(
        ForeignKey("items.id", ondelete="SET NULL"), nullable=False, index=True
    )
    description: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    quantity: Mapped[float] = mapped_column(Numeric(18, 4), nullable=False, default=1)
    unit_price: Mapped[float] = mapped_column(Numeric(18, 4), nullable=False, default=0)
    line_total: Mapped[float] = mapped_column(Numeric(18, 4), nullable=False, default=0)
    cost_price: Mapped[float] = mapped_column(Numeric(18, 4), nullable=False, default=0)
    total_cost: Mapped[float] = mapped_column(Numeric(18, 4), nullable=False, default=0)
