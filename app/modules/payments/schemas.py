from typing import Optional

from pydantic import BaseModel, Field


class PaymentCreate(BaseModel):
    partner_id: int
    reference: str = Field(..., min_length=1)
    document_type: str = "invoice"
    document_id: int = 0
    payment_date: Optional[str] = None
    amount: float = Field(ge=0)
    currency_code: str = "EGP"
    fx_rate_used: Optional[float] = None
    payment_method: str = "cash"
    notes: Optional[str] = None


class PaymentRead(PaymentCreate):
    id: int
    base_amount: float = 0.0
    fx_gain_loss: float = 0.0
