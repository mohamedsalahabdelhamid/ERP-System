"""RBAC service: resolve a user's effective permissions within a company.

Permissions are always evaluated **within the active company** (spec: access
control is per-company). A user's effective permissions are the union of the
permissions granted to every role they hold in that company, resolved through:

    user_roles -> roles -> role_permissions -> permissions
"""

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.modules.rbac.models import Permission, Role, RolePermission, UserRole
from app.modules.users.models import User


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


# ---------------------------------------------------------------------------
# Permission catalog queries
# ---------------------------------------------------------------------------

def list_all_permissions(db: Session) -> list[Permission]:
    """Return every permission in the catalog, ordered by code."""
    return list(
        db.scalars(select(Permission).order_by(Permission.code)).all()
    )


# ---------------------------------------------------------------------------
# Role CRUD
# ---------------------------------------------------------------------------

def list_roles(db: Session, company_id: int) -> list[dict]:
    """Return roles in the company with their permission codes."""
    roles = list(
        db.scalars(
            select(Role)
            .where(Role.company_id == company_id)
            .order_by(Role.name)
        ).all()
    )
    result = []
    for role in roles:
        codes = list(
            db.scalars(
                select(Permission.code)
                .join(RolePermission, RolePermission.permission_id == Permission.id)
                .where(RolePermission.role_id == role.id)
                .order_by(Permission.code)
            ).all()
        )
        result.append({"id": role.id, "name": role.name, "permissions": codes})
    return result


def get_role(db: Session, company_id: int, role_id: int) -> Role | None:
    return db.scalar(
        select(Role).where(
            Role.id == role_id, Role.company_id == company_id
        )
    )


def create_role(db: Session, company_id: int, name: str, perm_codes: list[str]) -> Role:
    """Create a role and grant the given permission codes."""
    role = Role(company_id=company_id, name=name)
    db.add(role)
    db.flush()

    if perm_codes:
        perm_ids = db.scalars(
            select(Permission.id).where(Permission.code.in_(perm_codes))
        ).all()
        for pid in perm_ids:
            db.add(RolePermission(role_id=role.id, permission_id=pid))
        db.flush()

    return role


def set_role_permissions(db: Session, role: Role, perm_codes: list[str]) -> None:
    """Replace all permissions on a role."""
    db.execute(delete(RolePermission).where(RolePermission.role_id == role.id))
    if perm_codes:
        perm_ids = db.scalars(
            select(Permission.id).where(Permission.code.in_(perm_codes))
        ).all()
        for pid in perm_ids:
            db.add(RolePermission(role_id=role.id, permission_id=pid))
    db.flush()


def role_has_users(db: Session, role_id: int) -> bool:
    """True if at least one user is assigned to this role."""
    return db.scalar(
        select(UserRole.id).where(UserRole.role_id == role_id).limit(1)
    ) is not None


def delete_role(db: Session, role: Role) -> None:
    db.execute(
        delete(RolePermission).where(RolePermission.role_id == role.id)
    )
    db.delete(role)
    db.flush()


# ---------------------------------------------------------------------------
# Company user management (scoped to a single company)
# ---------------------------------------------------------------------------

ADMIN_ROLE_NAME = "Admin"


def list_company_users(db: Session, company_id: int) -> list[dict]:
    """Return users who belong to the company, with their role names."""
    rows = db.execute(
        select(User, Role.name)
        .join(UserRole, UserRole.user_id == User.id)
        .join(Role, Role.id == UserRole.role_id)
        .where(UserRole.company_id == company_id)
        .order_by(User.id)
    ).all()
    result: dict[int, dict] = {}
    for user, role_name in rows:
        entry = result.setdefault(
            user.id,
            {
                "id": user.id,
                "email": user.email,
                "full_name": user.full_name,
                "is_active": user.is_active,
                "roles": [],
            },
        )
        if role_name not in entry["roles"]:
            entry["roles"].append(role_name)
    return sorted(result.values(), key=lambda u: u["id"])


def _count_company_users(db: Session, company_id: int) -> int:
    from sqlalchemy import func, distinct
    return db.scalar(
        select(func.count(distinct(UserRole.user_id))).where(
            UserRole.company_id == company_id
        )
    )


def create_company_user(
    db: Session,
    company_id: int,
    email: str,
    full_name: str,
    password: str,
    role_names: list[str] | None = None,
    branch_id: int | None = None,
    max_users: int = 999,
) -> dict:
    from app.core.security import hash_password
    from app.modules.companies.models import CompanySettings

    if db.scalar(select(User.id).where(User.email == email)):
        raise ValueError(f"A user with email '{email}' already exists.")

    settings = db.get(CompanySettings, company_id)
    seats = _count_company_users(db, company_id)
    if settings and seats >= (settings.max_users or max_users):
        raise ValueError(
            f"This company has reached its user limit ({settings.max_users}). "
            "Increase max_users to add more users."
        )

    requested = role_names or ["Employee"]
    role_map = {
        r.name: r
        for r in db.scalars(
            select(Role).where(Role.company_id == company_id)
        ).all()
    }
    for name in requested:
        if name not in role_map:
            raise ValueError(f"Unknown role '{name}' in this company.")

    user = User(
        email=email,
        password_hash=hash_password(password),
        full_name=full_name,
        is_active=True,
        is_superuser=False,
    )
    db.add(user)
    db.flush()

    for name in requested:
        db.add(
            UserRole(
                user_id=user.id,
                company_id=company_id,
                role_id=role_map[name].id,
                branch_id=branch_id,
            )
        )
    db.flush()

    return {
        "id": user.id,
        "email": user.email,
        "full_name": user.full_name,
        "is_active": user.is_active,
        "roles": list(requested),
    }


def set_user_roles(
    db: Session, user_id: int, company_id: int, role_names: list[str]
) -> None:
    """Replace all roles for a user in the given company."""
    existing = list(
        db.scalars(
            select(UserRole).where(
                UserRole.user_id == user_id,
                UserRole.company_id == company_id,
            )
        ).all()
    )
    branch_id = existing[0].branch_id if existing else None

    db.execute(
        delete(UserRole).where(
            UserRole.user_id == user_id,
            UserRole.company_id == company_id,
        )
    )

    role_map = {
        r.name: r
        for r in db.scalars(
            select(Role).where(Role.company_id == company_id)
        ).all()
    }
    for name in role_names:
        if name not in role_map:
            raise ValueError(f"Unknown role '{name}' in this company.")
        db.add(
            UserRole(
                user_id=user_id,
                company_id=company_id,
                role_id=role_map[name].id,
                branch_id=branch_id,
            )
        )
    db.flush()


def set_user_active_status(
    db: Session, user_id: int, is_active: bool
) -> None:
    user = db.get(User, user_id)
    if user is None:
        raise ValueError("User not found.")
    user.is_active = is_active
    db.flush()
