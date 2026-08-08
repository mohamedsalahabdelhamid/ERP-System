"""Partner model (spec section 4.1).

A partner is a customer, a supplier, or both. Always scoped to a company.
"""

from typing import Optional

from sqlalchemy import Boolean, ForeignKey, Integer, Numeric, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base_class import Base
from app.db.mixins import TimestampMixin


class Partner(TimestampMixin, Base):
    __tablename__ = "partners"
    __table_args__ = (
        UniqueConstraint("company_id", "code", name="uq_partners_company_code"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    company_id: Mapped[int] = mapped_column(
        ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True
    )
    # type: customer / supplier / both
    type: Mapped[str] = mapped_column(String(20), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    code: Mapped[str] = mapped_column(String(50), nullable=False)
    phone: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    address: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    tax_number: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    opening_balance: Mapped[float] = mapped_column(
        Numeric(18, 4), nullable=False, default=0
    )
    credit_limit: Mapped[float] = mapped_column(
        Numeric(18, 4), nullable=False, default=0
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
