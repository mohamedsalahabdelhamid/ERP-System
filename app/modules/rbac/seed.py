"""RBAC seeding helpers (Phase 2).

- ``sync_permissions``      : upserts the default permission catalog into the
                              ``permissions`` table (idempotent).
- ``grant_all_to_role``     : links a role to every known permission.
- ``grant_all_to_admin_roles`` : convenience — grants all permissions to every
                              role named "Admin" (across companies).

No new tables are created; these only populate existing RBAC tables.
"""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.permissions import ALL_PERMISSION_CODES, DEFAULT_PERMISSIONS
from app.modules.rbac.models import Permission, Role, RolePermission

ADMIN_ROLE_NAME = "Admin"


def sync_permissions(db: Session) -> dict[str, int]:
    """Ensure all default permissions exist. Returns {code: permission_id}."""
    existing = {
        p.code: p for p in db.scalars(select(Permission)).all()
    }
    for pdef in DEFAULT_PERMISSIONS:
        perm = existing.get(pdef.code)
        if perm is None:
            perm = Permission(code=pdef.code, description=pdef.description)
            db.add(perm)
            existing[pdef.code] = perm
        elif perm.description != pdef.description:
            perm.description = pdef.description  # keep descriptions in sync
    db.flush()
    return {code: existing[code].id for code in existing}


def grant_all_to_role(db: Session, role: Role) -> None:
    """Link the given role to every known permission (idempotent)."""
    perm_ids = db.scalars(
        select(Permission.id).where(Permission.code.in_(ALL_PERMISSION_CODES))
    ).all()
    already = set(
        db.scalars(
            select(RolePermission.permission_id).where(
                RolePermission.role_id == role.id
            )
        ).all()
    )
    for pid in perm_ids:
        if pid not in already:
            db.add(RolePermission(role_id=role.id, permission_id=pid))
    db.flush()


def grant_all_to_admin_roles(db: Session) -> int:
    """Grant all permissions to every role named 'Admin'. Returns role count."""
    admin_roles = db.scalars(
        select(Role).where(Role.name == ADMIN_ROLE_NAME)
    ).all()
    for role in admin_roles:
        grant_all_to_role(db, role)
    return len(admin_roles)
