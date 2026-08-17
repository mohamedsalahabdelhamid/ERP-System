from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_company_id, get_db, require_permission
from app.modules.payments.schemas import PaymentCreate, PaymentRead
from app.modules.payments.service import (
    create_payment,
    list_payments,
    payment_reference_exists,
)

router = APIRouter(prefix="/payments", tags=["payments"])


@router.get("", response_model=list[PaymentRead], dependencies=[Depends(require_permission("payments.view"))])
def list_payments_endpoint(
    company_id: int = Depends(get_current_company_id),
    db: Session = Depends(get_db),
) -> list[PaymentRead]:
    return list_payments(db, company_id)


@router.post("", response_model=PaymentRead, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_permission("payments.manage"))])
def create_payment_endpoint(
    data: PaymentCreate,
    company_id: int = Depends(get_current_company_id),
    db: Session = Depends(get_db),
) -> PaymentRead:
    if data.reference and payment_reference_exists(db, company_id, data.reference):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Payment reference '{data.reference}' already exists in this company.",
        )
    try:
        return create_payment(db, company_id, data)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
