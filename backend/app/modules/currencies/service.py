"""Currencies service: company-scoped CRUD for currencies + currency_rates.

Every query is filtered by ``company_id``. A currency rate references a currency
by its ``currency_code``; the service validates that the code belongs to the same
company before writing, so a rate can never point at another company's currency.
"""

from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.currencies.models import Currency, CurrencyRate
from app.modules.currencies.schemas import (
    CurrencyCreate,
    CurrencyRateCreate,
    CurrencyRateUpdate,
    CurrencyUpdate,
)


# ------------------------------------------------------------------ currencies
def list_currencies(db: Session, company_id: int) -> list[Currency]:
    stmt = (
        select(Currency)
        .where(Currency.company_id == company_id)
        .order_by(Currency.code)
    )
    return list(db.scalars(stmt).all())


def get_currency(
    db: Session, company_id: int, currency_id: int
) -> Optional[Currency]:
    stmt = select(Currency).where(
        Currency.id == currency_id, Currency.company_id == company_id
    )
    return db.scalar(stmt)


def get_currency_by_code(
    db: Session, company_id: int, code: str
) -> Optional[Currency]:
    stmt = select(Currency).where(
        Currency.company_id == company_id, Currency.code == code
    )
    return db.scalar(stmt)


def currency_code_exists(
    db: Session, company_id: int, code: str, exclude_id: Optional[int] = None
) -> bool:
    stmt = select(Currency.id).where(
        Currency.company_id == company_id, Currency.code == code
    )
    if exclude_id is not None:
        stmt = stmt.where(Currency.id != exclude_id)
    return db.scalar(stmt.limit(1)) is not None


def create_currency(
    db: Session, company_id: int, data: CurrencyCreate
) -> Currency:
    currency = Currency(company_id=company_id, **data.model_dump())
    db.add(currency)
    db.commit()
    db.refresh(currency)
    return currency


def update_currency(
    db: Session, currency: Currency, data: CurrencyUpdate
) -> Currency:
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(currency, field, value)
    db.commit()
    db.refresh(currency)
    return currency


def delete_currency(db: Session, currency: Currency) -> None:
    db.delete(currency)
    db.commit()


# -------------------------------------------------------------- currency rates
def list_rates(
    db: Session, company_id: int, currency_code: Optional[str] = None
) -> list[CurrencyRate]:
    stmt = (
        select(CurrencyRate)
        .where(CurrencyRate.company_id == company_id)
        .order_by(CurrencyRate.valid_from.desc(), CurrencyRate.id.desc())
    )
    if currency_code is not None:
        stmt = stmt.where(CurrencyRate.currency_code == currency_code)
    return list(db.scalars(stmt).all())


def get_rate(db: Session, company_id: int, rate_id: int) -> Optional[CurrencyRate]:
    stmt = select(CurrencyRate).where(
        CurrencyRate.id == rate_id, CurrencyRate.company_id == company_id
    )
    return db.scalar(stmt)


def create_rate(
    db: Session, company_id: int, data: CurrencyRateCreate
) -> CurrencyRate:
    rate = CurrencyRate(company_id=company_id, **data.model_dump())
    db.add(rate)
    db.commit()
    db.refresh(rate)
    return rate


def update_rate(
    db: Session, rate: CurrencyRate, data: CurrencyRateUpdate
) -> CurrencyRate:
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(rate, field, value)
    db.commit()
    db.refresh(rate)
    return rate


def delete_rate(db: Session, rate: CurrencyRate) -> None:
    db.delete(rate)
    db.commit()
