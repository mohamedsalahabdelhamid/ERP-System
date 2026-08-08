"""Partner API endpoints (Phase 3) — company-scoped CRUD.

    GET    /partners        -> list partners in the active company
    POST   /partners        -> create a partner
    GET    /partners/{id}    -> read one partner
    PATCH  /partners/{id}    -> update a partner
    DELETE /partners/{id}    -> delete a partner

Read routes require ``partners.view``; write routes require ``partners.manage``.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_company_id, get_db, require_permission
from app.modules.partners import service
from app.modules.partners.models import Partner
from app.modules.partners.schemas import PartnerCreate, PartnerRead, PartnerUpdate

router = APIRouter(prefix="/partners", tags=["partners"])


def _get_or_404(db: Session, company_id: int, partner_id: int) -> Partner:
    partner = service.get_partner(db, company_id, partner_id)
    if partner is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Partner not found."
        )
    return partner


@router.get(
    "",
    response_model=list[PartnerRead],
    dependencies=[Depends(require_permission("partners.view"))],
)
def list_partners(
    company_id: int = Depends(get_current_company_id),
    db: Session = Depends(get_db),
) -> list[Partner]:
    return service.list_partners(db, company_id)


@router.post(
    "",
    response_model=PartnerRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission("partners.manage"))],
)
def create_partner(
    data: PartnerCreate,
    company_id: int = Depends(get_current_company_id),
    db: Session = Depends(get_db),
) -> Partner:
    if service.code_exists(db, company_id, data.code):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Partner code '{data.code}' already exists in this company.",
        )
    return service.create_partner(db, company_id, data)


@router.get(
    "/{partner_id}",
    response_model=PartnerRead,
    dependencies=[Depends(require_permission("partners.view"))],
)
def get_partner(
    partner_id: int,
    company_id: int = Depends(get_current_company_id),
    db: Session = Depends(get_db),
) -> Partner:
    return _get_or_404(db, company_id, partner_id)


@router.patch(
    "/{partner_id}",
    response_model=PartnerRead,
    dependencies=[Depends(require_permission("partners.manage"))],
)
def update_partner(
    partner_id: int,
    data: PartnerUpdate,
    company_id: int = Depends(get_current_company_id),
    db: Session = Depends(get_db),
) -> Partner:
    partner = _get_or_404(db, company_id, partner_id)
    if data.code is not None and service.code_exists(
        db, company_id, data.code, exclude_id=partner.id
    ):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Partner code '{data.code}' already exists in this company.",
        )
    return service.update_partner(db, partner, data)


@router.delete(
    "/{partner_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_permission("partners.manage"))],
)
def delete_partner(
    partner_id: int,
    company_id: int = Depends(get_current_company_id),
    db: Session = Depends(get_db),
) -> None:
    partner = _get_or_404(db, company_id, partner_id)
    service.delete_partner(db, partner)
