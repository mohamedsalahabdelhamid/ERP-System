"""Platform tenant-management service (superuser only).

Responsibilities:
  - create companies with their subscription (modules, seats, status)
  - list companies and their subscription state
  - update a subscription (toggle modules, change seats, suspend/activate)
  - create tenant users (with role assignment) under the seat limit
  - manage passwords for tenant users

Seat counting: the platform-created owner does not count against the license;
only additional users created under ``max_users`` are seats.
"""

import re

from sqlalchemy import distinct, func, select
from sqlalchemy.orm import Session

from app.core.modules import MODULE_KEYS, is_valid_module
from app.core.password_policy import WeakPasswordError, validate_password
from app.core.security import hash_password
from app.modules.companies.models import Branch, Company, CompanySettings
from app.modules.inventory.models import Warehouse
from app.modules.rbac.models import (
    Permission,
    Role,
    RolePermission,
    UserRole,
)
from app.modules.rbac.seed import grant_all_to_role, sync_permissions
from app.modules.users.models import User

OWNER_ROLE_NAME = "Admin"

# Limited but functional default roles for tenant staff.
ACCOUNTANT_PERMISSIONS = [
    "companies.view",
    "users.view",
    "roles.view",
    "partners.view",
    "partners.manage",
    "categories.view",
    "units.view",
    "items.view",
    "sales.view",
    "purchases.view",
    "warehouses.view",
    "stock.view",
    "movements.view",
    "payments.view",
    "payments.manage",
    "accounts.view",
    "accounts.manage",
    "journal_entries.view",
    "journal_entries.manage",
    "accounting.view",
    "accounting.manage",
    "accounting.reports",
    "currencies.view",
    "currency_rates.view",
    "unit_conversions.view",
    "stock_takes.view",
]

EMPLOYEE_PERMISSIONS = [
    "companies.view",
    "partners.view",
    "categories.view",
    "units.view",
    "items.view",
    "sales.view",
    "purchases.view",
    "warehouses.view",
    "stock.view",
    "hr.view",
    "projects.view",
    "accounting.reports",
]


class PlatformError(ValueError):
    """Raised for recoverable platform failures (invalid input, conflicts)."""


def _validate_subdomain(subdomain: str) -> str:
    subdomain = (subdomain or "").strip().lower()
    if not re.fullmatch(r"[a-z0-9](?:[a-z0-9-]{0,97}[a-z0-9])?", subdomain):
        raise PlatformError(
            "Subdomain must be lowercase letters, digits or hyphens "
            "(e.g. 'acme')."
        )
    return subdomain


def _validate_modules(modules: list[str]) -> list[str]:
    bad = [m for m in modules if not is_valid_module(m)]
    if bad:
        raise PlatformError(f"Unknown modules: {', '.join(bad)}")
    return list(dict.fromkeys(modules))


def _sync_flags(settings: CompanySettings) -> None:
    enabled = set(settings.enabled_modules or [])
    settings.has_manufacturing = "manufacturing" in enabled
    settings.has_projects = "projects" in enabled
    settings.has_pos = "pos" in enabled


def _company_snapshot(company: Company) -> dict:
    settings = company.settings or CompanySettings(company_id=company.id)
    return {
        "id": company.id,
        "name": company.name,
        "code": company.code,
        "subdomain": company.subdomain,
        "status": company.status,
        "base_currency": company.base_currency,
        "activity_type": company.activity_type,
        "is_active": company.is_active,
        "max_users": settings.max_users,
        "modules": list(settings.enabled_modules or []),
    }


def _grant_role_permissions(
    db: Session, role: Role, codes: list[str]
) -> None:
    perm_ids = db.scalars(
        select(Permission.id).where(Permission.code.in_(codes))
    ).all()
    for pid in perm_ids:
        db.add(RolePermission(role_id=role.id, permission_id=pid))
    db.flush()


def _create_default_roles(db: Session, company_id: int) -> dict[str, Role]:
    owner = Role(company_id=company_id, name=OWNER_ROLE_NAME)
    accountant = Role(company_id=company_id, name="Accountant")
    employee = Role(company_id=company_id, name="Employee")
    db.add_all([owner, accountant, employee])
    db.flush()
    grant_all_to_role(db, owner)
    _grant_role_permissions(db, accountant, ACCOUNTANT_PERMISSIONS)
    _grant_role_permissions(db, employee, EMPLOYEE_PERMISSIONS)
    return {"Admin": owner, "Accountant": accountant, "Employee": employee}


def create_company(
    db: Session,
    name: str,
    code: str,
    subdomain: str,
    owner_email: str,
    owner_name: str,
    owner_password: str,
    base_currency: str = "EGP",
    activity_type: str = "trading",
    modules: list[str] | None = None,
    max_users: int = 5,
    status: str = "active",
) -> dict:
    """Create a tenant company with its owner account and default roles."""
    modules = _validate_modules(modules or [])
    subdomain = _validate_subdomain(subdomain)
    validate_password(owner_password)

    if db.scalar(select(Company.id).where(Company.code == code)):
        raise PlatformError(f"A company with code '{code}' already exists.")
    if db.scalar(select(Company.id).where(Company.subdomain == subdomain)):
        raise PlatformError(
            f"The subdomain '{subdomain}' is already taken."
        )
    if db.scalar(select(User.id).where(User.email == owner_email)):
        raise PlatformError(f"A user with email '{owner_email}' already exists.")

    company = Company(
        name=name,
        code=code,
        subdomain=subdomain,
        status=status,
        base_currency=base_currency,
        activity_type=activity_type,
        is_active=True,
    )
    db.add(company)
    db.flush()

    branch = Branch(
        company_id=company.id,
        name="Main Branch",
        code="MAIN",
        is_active=True,
    )
    db.add(branch)

    settings = CompanySettings(
        company_id=company.id,
        enabled_modules=modules,
        cost_method="weighted_average",
        max_users=max_users,
    )
    _sync_flags(settings)
    db.add(settings)

    db.add(
        Warehouse(
            company_id=company.id,
            branch_id=branch.id,
            name="Main Warehouse",
            code="WH-1",
            is_active=True,
        )
    )

    sync_permissions(db)
    roles = _create_default_roles(db, company.id)

    owner = User(
        email=owner_email,
        password_hash=hash_password(owner_password),
        full_name=owner_name,
        is_active=True,
        is_superuser=False,
    )
    db.add(owner)
    db.flush()
    db.add(
        UserRole(
            user_id=owner.id,
            company_id=company.id,
            role_id=roles[OWNER_ROLE_NAME].id,
            branch_id=branch.id,
        )
    )

    db.commit()
    db.refresh(company)
    return _company_snapshot(company)


def list_companies(db: Session) -> list[dict]:
    return [
        _company_snapshot(c)
        for c in db.scalars(select(Company).order_by(Company.id)).all()
    ]


def get_company(db: Session, company_id: int) -> dict:
    company = db.get(Company, company_id)
    if company is None:
        raise PlatformError("Company not found.")
    return _company_snapshot(company)


def update_company(
    db: Session,
    company_id: int,
    modules: list[str] | None = None,
    max_users: int | None = None,
    status: str | None = None,
) -> dict:
    company = db.get(Company, company_id)
    if company is None:
        raise PlatformError("Company not found.")
    if company.settings is None:
        raise PlatformError("Company settings missing.")

    if modules is not None:
        company.settings.enabled_modules = _validate_modules(modules)
        _sync_flags(company.settings)
    if max_users is not None:
        if max_users < 1:
            raise PlatformError("max_users must be at least 1.")
        company.settings.max_users = max_users
    if status is not None:
        if status not in {"active", "trial", "suspended"}:
            raise PlatformError(f"Unknown status '{status}'.")
        company.status = status
        company.is_active = status != "suspended"

    db.add(company)
    db.add(company.settings)
    db.commit()
    db.refresh(company)
    return _company_snapshot(company)


def _count_company_seats(db: Session, company_id: int) -> int:
    return db.scalar(
        select(func.count(distinct(UserRole.user_id))).where(
            UserRole.company_id == company_id
        )
    )


def list_company_users(db: Session, company_id: int) -> list[dict]:
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


def create_company_user(
    db: Session,
    company_id: int,
    email: str,
    full_name: str,
    password: str,
    role_names: list[str] | None = None,
    branch_id: int | None = None,
) -> dict:
    company = db.get(Company, company_id)
    if company is None:
        raise PlatformError("Company not found.")
    validate_password(password)

    if db.scalar(select(User.id).where(User.email == email)):
        raise PlatformError(f"A user with email '{email}' already exists.")

    if branch_id is not None:
        branch = db.get(Branch, branch_id)
        if branch is None or branch.company_id != company_id:
            raise PlatformError("Branch does not belong to this company.")

    seats = _count_company_seats(db, company_id)
    max_users = company.settings.max_users if company.settings else 5
    if seats >= max_users:
        raise PlatformError(
            f"This company has reached its user limit ({max_users}). "
            "Increase max_users on the subscription to add more users."
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
            raise PlatformError(f"Unknown role '{name}' in this company.")

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

    db.commit()
    db.refresh(user)
    return {
        "id": user.id,
        "email": user.email,
        "full_name": user.full_name,
        "is_active": user.is_active,
        "roles": list(requested),
    }


def change_user_password(
    db: Session, user_id: int, new_password: str
) -> None:
    validate_password(new_password)
    user = db.get(User, user_id)
    if user is None:
        raise PlatformError("User not found.")
    user.password_hash = hash_password(new_password)
    db.add(user)
    db.commit()


def delete_company(db: Session, company_id: int, confirm_code: str) -> None:
    """Delete an entire tenant company and all its data.

    The caller must pass confirm_code matching the company's code to prevent
    accidental deletion. All company-scoped rows are removed. Users (global
    identities) are not deleted; only their UserRole links to this company are
    removed.
    """
    company = db.get(Company, company_id)
    if company is None:
        raise PlatformError("Company not found.")
    if confirm_code != company.code:
        raise PlatformError("Confirmation code does not match the company code.")

    # Enable FK cascades on SQLite so parent deletion cleans children.
    if db.bind.dialect.name == "sqlite":
        from sqlalchemy import text as _text
        db.execute(_text("PRAGMA foreign_keys=ON"))

    # The Company model has relationship cascade="all, delete-orphan" on
    # branches and settings, and every FK to companies is ON DELETE CASCADE.
    # A single delete of the Company row cascades everything in Postgres and
    # in SQLite with FK enabled.
    db.delete(company)
    db.flush()
