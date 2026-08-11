"""Company API endpoints.

    GET /companies          -> companies the current user can access.
    GET /companies/current  -> the active company for the session.
                               Demonstrates company-scope enforcement: requires a
                               company to have been selected (409 otherwise).
    POST /companies/{id}/branches -> create a branch (companies.manage).

NOTE: company creation is exclusive to the platform owner (see
``app/modules/platform/router.py``). Tenants cannot self-provision companies.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.modules.auth.dependencies import get_current_company_id, get_current_session, get_current_user
from app.modules.auth.models import AuthSession
from app.modules.companies import service as company_service
from app.modules.companies.models import Branch, Company, CompanySettings
from app.modules.companies.schemas import BranchCreate, BranchRead, CompanyRead, CompanySettingsRead, CompanySettingsUpdate
from app.modules.rbac.dependencies import require_permission
from app.modules.users.models import User

router = APIRouter(prefix="/companies", tags=["companies"])


@router.get(
    "",
    response_model=list[CompanyRead],
    dependencies=[Depends(require_permission("companies.view"))],
)
def list_my_companies(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[Company]:
    return company_service.get_user_companies(db, user.id)


@router.post(
    "/{company_id}/branches",
    response_model=BranchRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission("companies.manage"))],
)
def create_branch(
    company_id: int,
    data: BranchCreate,
    session: AuthSession = Depends(get_current_session),
    db: Session = Depends(get_db),
) -> Branch:
    branch = company_service.create_branch(db, company_id, data)
    session.current_company_id = company_id
    session.current_branch_id = branch.id
    db.add(session)
    db.commit()
    db.refresh(session)
    return branch


@router.get(
    "/current",
    response_model=CompanyRead,
    dependencies=[Depends(require_permission("companies.view"))],
)
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


@router.get(
    "/settings",
    response_model=CompanySettingsRead,
    dependencies=[Depends(require_permission("companies.view"))],
)
def get_company_settings(
    company_id: int = Depends(get_current_company_id),
    db: Session = Depends(get_db),
) -> CompanySettings:
    from app.modules.companies.models import CompanySettings  # avoid circular at top
    settings = db.get(CompanySettings, company_id)
    if settings is None:
        raise HTTPException(status_code=404, detail="Company settings not found.")
    return settings


@router.patch(
    "/settings",
    response_model=CompanySettingsRead,
    dependencies=[Depends(require_permission("companies.manage"))],
)
def update_company_settings(
    data: CompanySettingsUpdate,
    company_id: int = Depends(get_current_company_id),
    db: Session = Depends(get_db),
) -> CompanySettings:
    from app.modules.companies.models import CompanySettings
    settings = db.get(CompanySettings, company_id)
    if settings is None:
        raise HTTPException(status_code=404, detail="Company settings not found.")
    if data.low_stock_threshold is not None:
        settings.low_stock_threshold = data.low_stock_threshold
    if data.alert_emails is not None:
        settings.alert_emails = data.alert_emails
    if data.block_negative_stock is not None:
        settings.block_negative_stock = data.block_negative_stock
    db.add(settings)
    db.commit()
    db.refresh(settings)
    return settings
