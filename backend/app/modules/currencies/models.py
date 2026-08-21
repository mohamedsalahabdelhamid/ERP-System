"""Currency master data (spec section 5.1).

Tables:
  - currencies      : per-company list of currencies the company deals with
                      (code, name). The company's own ``base_currency`` lives on
                      the companies table; these are the *foreign* currencies plus
                      optionally the base one.
  - currency_rates  : time-stamped exchange rate of a currency to the company's
                      base currency (``rate_to_base`` at ``valid_from``).

Both tables are scoped to a company. ``currency_rates`` references a currency by
its code within the same company (composite FK to currencies(company_id, code)),
so a rate can never point at another company's currency.

Document-level FX fields (document_currency, fx_rate_used, ...) live on the
financial documents themselves and are added in Phase 5 (Sales & Purchases).
"""

from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    ForeignKeyConstraint,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base_class import Base
from app.db.mixins import TimestampMixin


class Currency(TimestampMixin, Base):
    __tablename__ = "currencies"
    __table_args__ = (
        UniqueConstraint("company_id", "code", name="uq_currencies_company_code"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    company_id: Mapped[int] = mapped_column(
        ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True
    )
    # ISO-style code, e.g. "EGP", "USD".
    code: Mapped[str] = mapped_column(String(10), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)


class CurrencyRate(TimestampMixin, Base):
    __tablename__ = "currency_rates"
    __table_args__ = (
        # Rate must reference a currency that exists in the same company.
        ForeignKeyConstraint(
            ["company_id", "currency_code"],
            ["currencies.company_id", "currencies.code"],
            name="fk_currency_rates_company_currency",
            ondelete="CASCADE",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    company_id: Mapped[int] = mapped_column(
        ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True
    )
    currency_code: Mapped[str] = mapped_column(String(10), nullable=False)
    # Value of 1 unit of currency_code expressed in the company's base currency.
    rate_to_base: Mapped[float] = mapped_column(Numeric(18, 8), nullable=False)
    valid_from: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
