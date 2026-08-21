"""Pydantic schemas for Phase 4 currencies: currencies + currency_rates."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


# ---- Currencies ----
class CurrencyCreate(BaseModel):
    code: str
    name: str
    is_active: bool = True


class CurrencyUpdate(BaseModel):
    code: Optional[str] = None
    name: Optional[str] = None
    is_active: Optional[bool] = None


class CurrencyRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    company_id: int
    code: str
    name: str
    is_active: bool


# ---- Currency rates ----
class CurrencyRateCreate(BaseModel):
    currency_code: str
    rate_to_base: float
    valid_from: datetime


class CurrencyRateUpdate(BaseModel):
    currency_code: Optional[str] = None
    rate_to_base: Optional[float] = None
    valid_from: Optional[datetime] = None


class CurrencyRateRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    company_id: int
    currency_code: str
    rate_to_base: float
    valid_from: datetime
