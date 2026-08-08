"""Seed a demo company, branch, settings, an Admin role, and an admin user.

Idempotent: running it again will not create duplicates. Intended for local
development / first-run bootstrap.

Usage (inside the web container):
    python -m scripts.seed
"""

from sqlalchemy import select

from app.core.security import hash_password
from app.db.session import SessionLocal
from app.modules.companies.models import Branch, Company, CompanySettings
from app.modules.rbac.models import Role, UserRole
from app.modules.users.models import User

DEMO_COMPANY_CODE = "DEMO"
ADMIN_EMAIL = "admin@example.com"
ADMIN_PASSWORD = "admin123"  # noqa: S105 - demo bootstrap credential only


def seed() -> None:
    db = SessionLocal()
    try:
        # --- Company ---
        company = db.scalar(
            select(Company).where(Company.code == DEMO_COMPANY_CODE)
        )
        if company is None:
            company = Company(
                name="Demo Company",
                code=DEMO_COMPANY_CODE,
                base_currency="EGP",
                activity_type="trading",
                is_active=True,
            )
            db.add(company)
            db.flush()  # assign company.id

        # --- Branch ---
        branch = db.scalar(
            select(Branch).where(
                Branch.company_id == company.id, Branch.code == "MAIN"
            )
        )
        if branch is None:
            branch = Branch(
                company_id=company.id,
                name="Main Branch",
                code="MAIN",
                is_active=True,
            )
            db.add(branch)

        # --- Company settings (1:1) ---
        settings = db.get(CompanySettings, company.id)
        if settings is None:
            settings = CompanySettings(
                company_id=company.id,
                enabled_modules=["sales", "purchases", "inventory"],
                cost_method="weighted_average",
                has_manufacturing=False,
                has_projects=False,
                has_pos=False,
            )
            db.add(settings)

        # --- Admin role ---
        role = db.scalar(
            select(Role).where(
                Role.company_id == company.id, Role.name == "Admin"
            )
        )
        if role is None:
            role = Role(company_id=company.id, name="Admin")
            db.add(role)
            db.flush()

        # --- Admin user ---
        user = db.scalar(select(User).where(User.email == ADMIN_EMAIL))
        if user is None:
            user = User(
                email=ADMIN_EMAIL,
                password_hash=hash_password(ADMIN_PASSWORD),
                full_name="System Administrator",
                is_active=True,
            )
            db.add(user)
            db.flush()

        # --- Grant the admin user the Admin role in the demo company ---
        link = db.scalar(
            select(UserRole).where(
                UserRole.user_id == user.id,
                UserRole.company_id == company.id,
                UserRole.role_id == role.id,
            )
        )
        if link is None:
            db.add(
                UserRole(
                    user_id=user.id,
                    company_id=company.id,
                    branch_id=branch.id,
                    role_id=role.id,
                )
            )

        db.commit()
        print(
            f"Seed complete. Login with {ADMIN_EMAIL} / {ADMIN_PASSWORD} "
            f"(company code: {DEMO_COMPANY_CODE})."
        )
    finally:
        db.close()


if __name__ == "__main__":
    seed()
