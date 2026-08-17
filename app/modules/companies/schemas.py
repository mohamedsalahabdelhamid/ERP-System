"""Pydantic schemas for companies (read models used by the auth/company APIs)."""

from typing import Optional

from pydantic import BaseModel, ConfigDict


class CompanyCreate(BaseModel):
    name: str
    code: str
    base_currency: str = "EGP"
    activity_type: str = "trading"
    is_active: bool = True


class BranchCreate(BaseModel):
    name: str
    # Optional: auto-generated per company when omitted (BR-###).
    code: Optional[str] = None
    is_active: bool = True


class BranchRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    company_id: int
    name: str
    code: str
    is_active: bool


class CompanyRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    code: str
    subdomain: Optional[str] = None
    status: str
    base_currency: str
    activity_type: str
    is_active: bool
    branch_id: Optional[int] = None


class CompanySettingsRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    company_id: int
    enabled_modules: list = []
    cost_method: str
    max_users: int
    has_manufacturing: bool
    has_projects: bool
    has_pos: bool
    low_stock_threshold: float = 0
    alert_emails: Optional[str] = None
    block_negative_stock: bool = True


class CompanySettingsUpdate(BaseModel):
    low_stock_threshold: Optional[float] = None
    alert_emails: Optional[str] = None  # comma-separated emails
    block_negative_stock: Optional[bool] = None
