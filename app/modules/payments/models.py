from typing import Optional

from sqlalchemy import ForeignKey, Integer, Numeric, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base_class import Base
from app.db.mixins import TimestampMixin


class Payment(TimestampMixin, Base):
    __tablename__ = "payments"
    __table_args__ = (
        UniqueConstraint("company_id", "reference", name="uq_payments_company_reference"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    company_id: Mapped[int] = mapped_column(
        ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True
    )
    partner_id: Mapped[int] = mapped_column(
        ForeignKey("partners.id", ondelete="CASCADE"), nullable=False, index=True
    )
    reference: Mapped[str] = mapped_column(String(100), nullable=False)
    document_type: Mapped[str] = mapped_column(String(50), nullable=False, default="invoice")
    document_id: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    payment_date: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    amount: Mapped[float] = mapped_column(Numeric(18, 4), nullable=False, default=0)
    currency_code: Mapped[str] = mapped_column(String(10), nullable=False, default="EGP")
    fx_rate_used: Mapped[float] = mapped_column(Numeric(18, 8), nullable=False, default=1)
    base_amount: Mapped[float] = mapped_column(Numeric(18, 4), nullable=False, default=0)
    fx_gain_loss: Mapped[float] = mapped_column(Numeric(18, 4), nullable=False, default=0)
    payment_method: Mapped[str] = mapped_column(String(30), nullable=False, default="cash")
    notes: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
