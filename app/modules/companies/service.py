"""Company access helpers.

Resolves which companies/branches a user may access, based on ``user_roles``.
Used during login and company selection to enforce that a user can only pick a
company they have been granted a role in.
"""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.companies.models import Branch, Company
from app.modules.rbac.models import UserRole


def get_user_companies(db: Session, user_id: int) -> list[Company]:
    """Return the active companies the user has any role in."""
    stmt = (
        select(Company)
        .join(UserRole, UserRole.company_id == Company.id)
        .where(UserRole.user_id == user_id, Company.is_active.is_(True))
        .distinct()
        .order_by(Company.name)
    )
    return list(db.scalars(stmt).all())


def user_can_access_company(db: Session, user_id: int, company_id: int) -> bool:
    """True if the user has at least one role in the given company."""
    stmt = select(UserRole.id).where(
        UserRole.user_id == user_id, UserRole.company_id == company_id
    ).limit(1)
    return db.scalar(stmt) is not None


def branch_belongs_to_company(db: Session, branch_id: int, company_id: int) -> bool:
    """True if the branch exists and belongs to the given company."""
    stmt = select(Branch.id).where(
        Branch.id == branch_id, Branch.company_id == company_id
    ).limit(1)
    return db.scalar(stmt) is not None
