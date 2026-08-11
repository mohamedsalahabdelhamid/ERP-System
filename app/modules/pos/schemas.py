from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class PosSessionCreate(BaseModel):
    branch_id: Optional[int] = None
    opening_cash: float = 0.0


class PosSessionClose(BaseModel):
    closing_cash: float = Field(ge=0)


class PosSessionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    company_id: int
    branch_id: Optional[int]
    opened_by: int
    opened_at: str
    closed_at: Optional[str]
    opening_cash: float
    closing_cash: float
    expected_cash: float
    variance: float
    status: str


class PosOrderLineCreate(BaseModel):
    item_id: int
    quantity: float = Field(gt=0)
    unit_price: float = Field(ge=0)


class PosOrderCreate(BaseModel):
    session_id: int
    partner_id: Optional[int] = None  # None = walk-in customer
    cashier_id: int = 0
    currency_code: str = "EGP"
    fx_rate: float = 1.0
    payment_method: str = "cash"
    lines: list[PosOrderLineCreate] = Field(..., min_length=1)


class PosOrderLineRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    order_id: int
    item_id: int
    quantity: float
    unit_price: float
    line_total: float


class PosOrderRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    company_id: int
    session_id: int
    invoice_id: Optional[int]
    order_number: str
    partner_id: Optional[int]
    cashier_id: int
    total: float
    status: str
