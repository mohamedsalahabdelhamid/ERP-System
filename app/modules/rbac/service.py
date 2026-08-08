"""RBAC service: resolve a user's effective permissions within a company.

Permissions are always evaluated **within the active company** (spec: access
control is per-company). A user's effective permissions are the union of the
permissions granted to every role they hold in that company, resolved through:

    user_roles -> roles -> role_permissions -> permissions
"""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.rbac.models import Permission, Role, RolePermission, UserRole


def get_user_permissions(db: Session, user_id: int, company_id: int) -> set[str]:
    """Return the set of permission codes the user has in the given company."""
    stmt = (
        select(Permission.code)
        .join(RolePermission, RolePermission.permission_id == Permission.id)
        .join(Role, Role.id == RolePermission.role_id)
        .join(UserRole, UserRole.role_id == Role.id)
        .where(
            UserRole.user_id == user_id,
            UserRole.company_id == company_id,
            Role.company_id == company_id,
        )
        .distinct()
    )
    return set(db.scalars(stmt).all())


def user_has_permission(
    db: Session, user_id: int, company_id: int, code: str
) -> bool:
    """True if the user holds ``code`` in the given company."""
    stmt = (
        select(Permission.id)
        .join(RolePermission, RolePermission.permission_id == Permission.id)
        .join(Role, Role.id == RolePermission.role_id)
        .join(UserRole, UserRole.role_id == Role.id)
        .where(
            UserRole.user_id == user_id,
            UserRole.company_id == company_id,
            Role.company_id == company_id,
            Permission.code == code,
        )
        .limit(1)
    )
    return db.scalar(stmt) is not None
