from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class SalesInvoiceLineCreate(BaseModel):
    item_id: int
    description: Optional[str] = None
    quantity: float = 1
    unit_price: float = 0


class SalesInvoiceLineRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    invoice_id: int
    item_id: int
    description: Optional[str]
    quantity: float
    unit_price: float
    line_total: float
    cost_price: float
    total_cost: float


class SalesInvoiceCreate(BaseModel):
    partner_id: int
    number: str
    date: datetime
    currency_code: str
    fx_rate: float = 1
    lines: list[SalesInvoiceLineCreate]


class SalesInvoiceUpdate(BaseModel):
    partner_id: Optional[int] = None
    number: Optional[str] = None
    date: Optional[datetime] = None
    currency_code: Optional[str] = None
    fx_rate: Optional[float] = None
    lines: Optional[list[SalesInvoiceLineCreate]] = None


class SalesInvoiceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    company_id: int
    partner_id: int
    number: str
    date: datetime
    currency_code: str
    fx_rate: float
    total_amount: float
    total_amount_base: float
    is_confirmed: bool
