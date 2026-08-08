"""Pydantic schemas for partners."""

from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict

PartnerType = Literal["customer", "supplier", "both"]


class PartnerCreate(BaseModel):
    type: PartnerType
    name: str
    code: str
    phone: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    tax_number: Optional[str] = None
    opening_balance: float = 0
    credit_limit: float = 0
    is_active: bool = True


class PartnerUpdate(BaseModel):
    """Partial update; only provided fields are changed."""

    type: Optional[PartnerType] = None
    name: Optional[str] = None
    code: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    tax_number: Optional[str] = None
    opening_balance: Optional[float] = None
    credit_limit: Optional[float] = None
    is_active: Optional[bool] = None


class PartnerRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    company_id: int
    type: str
    name: str
    code: str
    phone: Optional[str]
    email: Optional[str]
    address: Optional[str]
    tax_number: Optional[str]
    opening_balance: float
    credit_limit: float
    is_active: bool
