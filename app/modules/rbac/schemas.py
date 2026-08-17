"""Pydantic schemas for the RBAC management API."""

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class PermissionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    code: str
    description: str | None = None


class RoleCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    permissions: list[str] = Field(default_factory=list)


class RolePermissionsUpdate(BaseModel):
    permissions: list[str] = Field(default_factory=list)


class RoleRead(BaseModel):
    id: int
    name: str
    permissions: list[str] = Field(default_factory=list)


class CompanyUserCreate(BaseModel):
    email: EmailStr
    full_name: str
    password: str = Field(min_length=8)
    role_names: list[str] = Field(default_factory=list)
    branch_id: int | None = None


class CompanyUserRolesUpdate(BaseModel):
    role_names: list[str] = Field(default_factory=list)


class CompanyUserStatusUpdate(BaseModel):
    is_active: bool


class CompanyUserRead(BaseModel):
    id: int
    email: str
    full_name: str
    is_active: bool
    roles: list[str] = Field(default_factory=list)


class ClearDataRequest(BaseModel):
    confirm: str = Field(min_length=1)


class DeleteTenantRequest(BaseModel):
    confirm_code: str = Field(min_length=1)
