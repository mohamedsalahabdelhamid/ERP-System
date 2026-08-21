"""Pydantic schemas for the auth API."""

from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.modules.companies.schemas import CompanyRead


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_at: str  # ISO-8601 timestamp


class SelectCompanyRequest(BaseModel):
    company_id: int
    branch_id: Optional[int] = None


class SessionScope(BaseModel):
    """Current scope carried by the active session."""

    current_company_id: Optional[int] = None
    current_branch_id: Optional[int] = None


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: EmailStr
    full_name: str
    is_active: bool


class MeResponse(BaseModel):
    user: UserRead
    scope: SessionScope
    companies: list[CompanyRead]
    is_superuser: bool = False
    full_name: str = ""
    email: str = ""
    permissions: list[str] = Field(default_factory=list)
