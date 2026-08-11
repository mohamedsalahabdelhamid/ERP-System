"""Platform management API (superuser only).

  - GET    /platform/modules                  catalog of sellable modules
  - GET    /platform/companies                list tenants + subscriptions
  - POST   /platform/companies                create a tenant (owner + roles)
  - GET    /platform/companies/{id}           single tenant detail
  - PATCH  /platform/companies/{id}           update subscription/status
  - GET    /platform/companies/{id}/users     tenant users with roles
  - POST   /platform/companies/{id}/users     create a tenant user (seats)
  - POST   /platform/users/{id}/password      reset a tenant user password
"""

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import get_current_superuser, get_db
from app.core.modules import AVAILABLE_MODULES
from app.modules.platform import service
from app.modules.platform.schemas import (
    CompanyUserCreate,
    CompanyUserRead,
    ModuleInfo,
    PasswordChangeRequest,
    PlatformCompanyCreate,
    PlatformCompanyRead,
    PlatformCompanyUpdate,
)

router = APIRouter(
    prefix="/platform",
    tags=["platform"],
    dependencies=[Depends(get_current_superuser)],
)


@router.get("/modules", response_model=list[ModuleInfo])
def list_modules() -> list[ModuleInfo]:
    return [
        ModuleInfo(key=m.key, label=m.label, description=m.description)
        for m in AVAILABLE_MODULES
    ]


@router.get("/companies", response_model=list[PlatformCompanyRead])
def list_tenants(db=Depends(get_db)) -> list[dict]:
    return service.list_companies(db)


@router.post("/companies", response_model=PlatformCompanyRead, status_code=201)
def create_tenant(data: PlatformCompanyCreate, db=Depends(get_db)) -> dict:
    try:
        return service.create_company(
            db,
            name=data.name,
            code=data.code,
            subdomain=data.subdomain,
            owner_email=str(data.owner_email),
            owner_name=data.owner_name,
            owner_password=data.owner_password,
            base_currency=data.base_currency,
            activity_type=data.activity_type,
            modules=data.modules,
            max_users=data.max_users,
            status=data.status,
        )
    except service.PlatformError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.get("/companies/{company_id}", response_model=PlatformCompanyRead)
def get_tenant(company_id: int, db=Depends(get_db)) -> dict:
    try:
        return service.get_company(db, company_id)
    except service.PlatformError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.patch("/companies/{company_id}", response_model=PlatformCompanyRead)
def update_tenant(
    company_id: int, data: PlatformCompanyUpdate, db=Depends(get_db)
) -> dict:
    try:
        return service.update_company(
            db,
            company_id,
            modules=data.modules,
            max_users=data.max_users,
            status=data.status,
        )
    except service.PlatformError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.get(
    "/companies/{company_id}/users", response_model=list[CompanyUserRead]
)
def list_tenant_users(company_id: int, db=Depends(get_db)) -> list[dict]:
    try:
        return service.list_company_users(db, company_id)
    except service.PlatformError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.post(
    "/companies/{company_id}/users",
    response_model=CompanyUserRead,
    status_code=201,
)
def create_tenant_user(
    company_id: int, data: CompanyUserCreate, db=Depends(get_db)
) -> dict:
    try:
        return service.create_company_user(
            db,
            company_id,
            email=str(data.email),
            full_name=data.full_name,
            password=data.password,
            role_names=data.role_names,
            branch_id=data.branch_id,
        )
    except service.PlatformError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/users/{user_id}/password", status_code=204)
def reset_user_password(
    user_id: int, data: PasswordChangeRequest, db=Depends(get_db)
) -> None:
    try:
        service.change_user_password(db, user_id, data.new_password)
    except service.PlatformError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
