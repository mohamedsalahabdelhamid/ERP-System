"""Company API endpoints (Phase 1).

    GET /companies          -> companies the current user can access.
    GET /companies/current  -> the active company for the session.
                               Demonstrates company-scope enforcement: requires a
                               company to have been selected (409 otherwise).
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.modules.auth.dependencies import get_current_company_id, get_current_user
from app.modules.companies import service as company_service
from app.modules.companies.models import Company
from app.modules.companies.schemas import CompanyRead
from app.modules.users.models import User

router = APIRouter(prefix="/companies", tags=["companies"])


@router.get("", response_model=list[CompanyRead])
def list_my_companies(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[Company]:
    return company_service.get_user_companies(db, user.id)


@router.get("/current", response_model=CompanyRead)
def get_current_company(
    company_id: int = Depends(get_current_company_id),
    db: Session = Depends(get_db),
) -> Company:
    company = db.get(Company, company_id)
    if company is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Company not found."
        )
    return company
