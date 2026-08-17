"""Partner service: company-scoped CRUD.

Every query is filtered by ``company_id`` so data never leaks across companies
(spec: "all business queries must be filtered by company_id").
"""

from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.numbering import generate_code
from app.modules.partners.models import Partner
from app.modules.partners.schemas import PartnerCreate, PartnerUpdate

# (kind, prefix) per partner type; matches the seeded CUS-### / SUP-### style.
_PARTNER_SEQ = {
    "customer": ("partner_customer", "CUS"),
    "supplier": ("partner_supplier", "SUP"),
    "both": ("partner_both", "PTN"),
}


def list_partners(db: Session, company_id: int) -> list[Partner]:
    stmt = (
        select(Partner)
        .where(Partner.company_id == company_id)
        .order_by(Partner.name)
    )
    return list(db.scalars(stmt).all())


def get_partner(db: Session, company_id: int, partner_id: int) -> Optional[Partner]:
    stmt = select(Partner).where(
        Partner.id == partner_id, Partner.company_id == company_id
    )
    return db.scalar(stmt)


def code_exists(
    db: Session, company_id: int, code: str, exclude_id: Optional[int] = None
) -> bool:
    stmt = select(Partner.id).where(
        Partner.company_id == company_id, Partner.code == code
    )
    if exclude_id is not None:
        stmt = stmt.where(Partner.id != exclude_id)
    return db.scalar(stmt.limit(1)) is not None


def create_partner(db: Session, company_id: int, data: PartnerCreate) -> Partner:
    values = data.model_dump()
    if not values.get("code"):
        kind, prefix = _PARTNER_SEQ[values["type"]]
        values["code"] = generate_code(
            db, company_id, kind, prefix, Partner, "code"
        )
    partner = Partner(company_id=company_id, **values)
    db.add(partner)
    db.commit()
    db.refresh(partner)
    return partner


def update_partner(db: Session, partner: Partner, data: PartnerUpdate) -> Partner:
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(partner, field, value)
    db.commit()
    db.refresh(partner)
    return partner


def delete_partner(db: Session, partner: Partner) -> None:
    db.delete(partner)
    db.commit()
