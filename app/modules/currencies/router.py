"""Currencies API endpoints (Phase 4) — company-scoped CRUD.

Two routers:
  - /currencies       (currencies.view / currencies.manage)
  - /currency-rates   (currency_rates.view / currency_rates.manage)

A currency rate must reference a currency that exists in the same company; the
create/update endpoints reject an unknown ``currency_code`` with 400.
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_company_id, get_db, require_permission
from app.modules.currencies import service
from app.modules.currencies.models import Currency, CurrencyRate
from app.modules.currencies.schemas import (
    CurrencyCreate,
    CurrencyRateCreate,
    CurrencyRateRead,
    CurrencyRateUpdate,
    CurrencyRead,
    CurrencyUpdate,
)

currencies_router = APIRouter(prefix="/currencies", tags=["currencies"])
rates_router = APIRouter(prefix="/currency-rates", tags=["currency-rates"])


# ==================================================================== currencies
def _get_currency_or_404(
    db: Session, company_id: int, currency_id: int
) -> Currency:
    currency = service.get_currency(db, company_id, currency_id)
    if currency is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Currency not found."
        )
    return currency


@currencies_router.get(
    "",
    response_model=list[CurrencyRead],
    dependencies=[Depends(require_permission("currencies.view"))],
)
def list_currencies(
    company_id: int = Depends(get_current_company_id),
    db: Session = Depends(get_db),
) -> list[Currency]:
    return service.list_currencies(db, company_id)


@currencies_router.post(
    "",
    response_model=CurrencyRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission("currencies.manage"))],
)
def create_currency(
    data: CurrencyCreate,
    company_id: int = Depends(get_current_company_id),
    db: Session = Depends(get_db),
) -> Currency:
    if service.currency_code_exists(db, company_id, data.code):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Currency code '{data.code}' already exists in this company.",
        )
    return service.create_currency(db, company_id, data)


@currencies_router.get(
    "/{currency_id}",
    response_model=CurrencyRead,
    dependencies=[Depends(require_permission("currencies.view"))],
)
def get_currency(
    currency_id: int,
    company_id: int = Depends(get_current_company_id),
    db: Session = Depends(get_db),
) -> Currency:
    return _get_currency_or_404(db, company_id, currency_id)


@currencies_router.patch(
    "/{currency_id}",
    response_model=CurrencyRead,
    dependencies=[Depends(require_permission("currencies.manage"))],
)
def update_currency(
    currency_id: int,
    data: CurrencyUpdate,
    company_id: int = Depends(get_current_company_id),
    db: Session = Depends(get_db),
) -> Currency:
    currency = _get_currency_or_404(db, company_id, currency_id)
    if data.code is not None and service.currency_code_exists(
        db, company_id, data.code, exclude_id=currency.id
    ):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Currency code '{data.code}' already exists in this company.",
        )
    return service.update_currency(db, currency, data)


@currencies_router.delete(
    "/{currency_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_permission("currencies.delete"))],
)
def delete_currency(
    currency_id: int,
    company_id: int = Depends(get_current_company_id),
    db: Session = Depends(get_db),
) -> None:
    currency = _get_currency_or_404(db, company_id, currency_id)
    service.delete_currency(db, currency)


# ================================================================ currency rates
def _get_rate_or_404(db: Session, company_id: int, rate_id: int) -> CurrencyRate:
    rate = service.get_rate(db, company_id, rate_id)
    if rate is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Currency rate not found."
        )
    return rate


def _require_known_currency(db: Session, company_id: int, code: str) -> None:
    if service.get_currency_by_code(db, company_id, code) is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"currency_code '{code}' not found in this company.",
        )


@rates_router.get(
    "",
    response_model=list[CurrencyRateRead],
    dependencies=[Depends(require_permission("currency_rates.view"))],
)
def list_rates(
    currency_code: Optional[str] = Query(default=None),
    company_id: int = Depends(get_current_company_id),
    db: Session = Depends(get_db),
) -> list[CurrencyRate]:
    return service.list_rates(db, company_id, currency_code)


@rates_router.post(
    "",
    response_model=CurrencyRateRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission("currency_rates.manage"))],
)
def create_rate(
    data: CurrencyRateCreate,
    company_id: int = Depends(get_current_company_id),
    db: Session = Depends(get_db),
) -> CurrencyRate:
    _require_known_currency(db, company_id, data.currency_code)
    return service.create_rate(db, company_id, data)


@rates_router.get(
    "/{rate_id}",
    response_model=CurrencyRateRead,
    dependencies=[Depends(require_permission("currency_rates.view"))],
)
def get_rate(
    rate_id: int,
    company_id: int = Depends(get_current_company_id),
    db: Session = Depends(get_db),
) -> CurrencyRate:
    return _get_rate_or_404(db, company_id, rate_id)


@rates_router.patch(
    "/{rate_id}",
    response_model=CurrencyRateRead,
    dependencies=[Depends(require_permission("currency_rates.manage"))],
)
def update_rate(
    rate_id: int,
    data: CurrencyRateUpdate,
    company_id: int = Depends(get_current_company_id),
    db: Session = Depends(get_db),
) -> CurrencyRate:
    rate = _get_rate_or_404(db, company_id, rate_id)
    if data.currency_code is not None:
        _require_known_currency(db, company_id, data.currency_code)
    return service.update_rate(db, rate, data)


@rates_router.delete(
    "/{rate_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_permission("currency_rates.delete"))],
)
def delete_rate(
    rate_id: int,
    company_id: int = Depends(get_current_company_id),
    db: Session = Depends(get_db),
) -> None:
    rate = _get_rate_or_404(db, company_id, rate_id)
    service.delete_rate(db, rate)
