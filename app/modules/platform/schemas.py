"""Platform (tenant management) schemas.

The platform owner ("superuser") manages companies, their subscriptions
(modules + seat count) and can create/assign tenant users directly.
"""

from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class PlatformCompanyCreate(BaseModel):
    name: str
    code: str
    subdomain: str = Field(min_length=3, max_length=100)
    base_currency: str = "EGP"
    activity_type: str = "trading"
    modules: list[str] = Field(default_factory=list)
    max_users: int = Field(default=5, ge=1, le=1000)
    status: str = "active"
    owner_email: EmailStr
    owner_name: str
    owner_password: str = Field(min_length=8)


class PlatformCompanyRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    code: str
    subdomain: Optional[str] = None
    status: str
    base_currency: str
    activity_type: str
    is_active: bool
    max_users: int = 5
    modules: list[str] = Field(default_factory=list)


class PlatformCompanyUpdate(BaseModel):
    modules: Optional[list[str]] = None
    max_users: Optional[int] = Field(default=None, ge=1, le=1000)
    status: Optional[str] = None


class CompanyUserCreate(BaseModel):
    email: EmailStr
    full_name: str
    password: str = Field(min_length=8)
    role_names: list[str] = Field(default_factory=list)
    branch_id: Optional[int] = None


class CompanyUserRead(BaseModel):
    id: int
    email: EmailStr
    full_name: str
    is_active: bool
    roles: list[str] = Field(default_factory=list)


class PasswordChangeRequest(BaseModel):
    current_password: Optional[str] = None
    new_password: str = Field(min_length=8)


class ModuleInfo(BaseModel):
    key: str
    label: str
    description: str


class DeleteTenantRequest(BaseModel):
    confirm_code: str = Field(min_length=1)
