"""RBAC management API — company-scoped role and permission management.

    GET    /permissions                    -> permission catalog
    GET    /roles                          -> roles in the active company
    POST   /roles                          -> create a role
    PATCH  /roles/{role_id}/permissions    -> replace role permissions
    DELETE /roles/{role_id}                -> delete a role (not Admin)
    GET    /company-users                  -> users in the active company
    POST   /company-users                  -> create a user in the active company
    PATCH  /company-users/{user_id}/roles  -> replace a user's roles
    PATCH  /company-users/{user_id}/status -> activate / deactivate
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import (
    get_current_company_id,
    get_db,
    require_permission,
)
from app.modules.rbac import service as rbac_service
from app.modules.rbac.models import Role
from app.modules.rbac.schemas import (
    CompanyUserCreate,
    CompanyUserRolesUpdate,
    CompanyUserStatusUpdate,
    PermissionRead,
    RoleCreate,
    RolePermissionsUpdate,
    RoleRead,
)
from app.modules.users.models import User

router = APIRouter(tags=["rbac"])


# ---------------------------------------------------------------------------
# Permissions catalog
# ---------------------------------------------------------------------------

@router.get(
    "/permissions",
    response_model=list[PermissionRead],
    dependencies=[Depends(require_permission("roles.view"))],
)
def list_permissions(db: Session = Depends(get_db)) -> list[PermissionRead]:
    return [PermissionRead.model_validate(p) for p in rbac_service.list_all_permissions(db)]


# ---------------------------------------------------------------------------
# Roles
# ---------------------------------------------------------------------------

@router.get(
    "/roles",
    response_model=list[RoleRead],
    dependencies=[Depends(require_permission("roles.view"))],
)
def list_roles(
    company_id: int = Depends(get_current_company_id),
    db: Session = Depends(get_db),
) -> list[RoleRead]:
    return [RoleRead(**r) for r in rbac_service.list_roles(db, company_id)]


@router.post(
    "/roles",
    response_model=RoleRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission("roles.manage"))],
)
def create_role(
    data: RoleCreate,
    company_id: int = Depends(get_current_company_id),
    db: Session = Depends(get_db),
) -> RoleRead:
    if data.name.lower() == rbac_service.ADMIN_ROLE_NAME.lower():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot create a role named 'Admin' via this endpoint.",
        )
    role = rbac_service.create_role(db, company_id, data.name, data.permissions)
    db.commit()
    codes = data.permissions
    return RoleRead(id=role.id, name=role.name, permissions=codes)


@router.patch(
    "/roles/{role_id}/permissions",
    response_model=RoleRead,
    dependencies=[Depends(require_permission("roles.manage"))],
)
def update_role_permissions(
    role_id: int,
    data: RolePermissionsUpdate,
    company_id: int = Depends(get_current_company_id),
    db: Session = Depends(get_db),
) -> RoleRead:
    role = rbac_service.get_role(db, company_id, role_id)
    if role is None:
        raise HTTPException(status_code=404, detail="Role not found.")
    rbac_service.set_role_permissions(db, role, data.permissions)
    db.commit()
    return RoleRead(id=role.id, name=role.name, permissions=sorted(data.permissions))


@router.delete(
    "/roles/{role_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_permission("roles.manage"))],
)
def delete_role(
    role_id: int,
    company_id: int = Depends(get_current_company_id),
    db: Session = Depends(get_db),
) -> None:
    role = rbac_service.get_role(db, company_id, role_id)
    if role is None:
        raise HTTPException(status_code=404, detail="Role not found.")
    if role.name.lower() == rbac_service.ADMIN_ROLE_NAME.lower():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete the Admin role.",
        )
    if rbac_service.role_has_users(db, role_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete a role that is assigned to users.",
        )
    rbac_service.delete_role(db, role)
    db.commit()


# ---------------------------------------------------------------------------
# Company users
# ---------------------------------------------------------------------------

@router.get(
    "/company-users",
    dependencies=[Depends(require_permission("users.view"))],
)
def list_company_users(
    company_id: int = Depends(get_current_company_id),
    db: Session = Depends(get_db),
) -> list[dict]:
    return rbac_service.list_company_users(db, company_id)


@router.post(
    "/company-users",
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission("users.manage"))],
)
def create_company_user(
    data: CompanyUserCreate,
    company_id: int = Depends(get_current_company_id),
    db: Session = Depends(get_db),
) -> dict:
    try:
        result = rbac_service.create_company_user(
            db,
            company_id,
            email=str(data.email),
            full_name=data.full_name,
            password=data.password,
            role_names=data.role_names or ["Employee"],
            branch_id=data.branch_id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    db.commit()
    return result


@router.patch(
    "/company-users/{user_id}/roles",
    dependencies=[Depends(require_permission("users.manage"))],
)
def update_company_user_roles(
    user_id: int,
    data: CompanyUserRolesUpdate,
    company_id: int = Depends(get_current_company_id),
    db: Session = Depends(get_db),
) -> dict:
    try:
        rbac_service.set_user_roles(db, user_id, company_id, data.role_names)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    db.commit()
    users = rbac_service.list_company_users(db, company_id)
    match = next((u for u in users if u["id"] == user_id), None)
    if match is None:
        raise HTTPException(status_code=404, detail="User not found in this company.")
    return match


@router.patch(
    "/company-users/{user_id}/status",
    dependencies=[Depends(require_permission("users.manage"))],
)
def update_company_user_status(
    user_id: int,
    data: CompanyUserStatusUpdate,
    db: Session = Depends(get_db),
) -> dict:
    try:
        rbac_service.set_user_active_status(db, user_id, data.is_active)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404, detail=str(exc))
    db.commit()
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found.")
    return {
        "id": user.id,
        "email": user.email,
        "full_name": user.full_name,
        "is_active": user.is_active,
    }
