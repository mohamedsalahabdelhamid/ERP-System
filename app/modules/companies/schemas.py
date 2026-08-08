"""Pydantic schemas for companies (read models used by the auth/company APIs)."""

from pydantic import BaseModel, ConfigDict


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
    base_currency: str
    activity_type: str
    is_active: bool
