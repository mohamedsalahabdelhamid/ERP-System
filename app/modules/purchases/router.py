from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import (
    get_current_company_id,
    get_db,
    require_module,
    require_permission,
)
from app.modules.purchases import service
from app.modules.purchases.models import PurchaseInvoice
from app.modules.purchases.schemas import (
    PurchaseInvoiceCreate,
    PurchaseInvoiceRead,
    PurchaseInvoiceUpdate,
)

router = APIRouter(
    prefix="/purchase-invoices",
    tags=["purchase-invoices"],
    dependencies=[Depends(require_module("purchases"))],
)


def _get_invoice_or_404(db: Session, company_id: int, invoice_id: int) -> PurchaseInvoice:
    invoice = service.get_invoice(db, company_id, invoice_id)
    if invoice is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Purchase invoice not found."
        )
    return invoice


@router.get(
    "",
    response_model=list[PurchaseInvoiceRead],
    dependencies=[Depends(require_permission("purchases.view"))],
)
def list_invoices(
    company_id: int = Depends(get_current_company_id),
    db: Session = Depends(get_db),
) -> list[PurchaseInvoice]:
    return service.list_invoices(db, company_id)


@router.post(
    "",
    response_model=PurchaseInvoiceRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission("purchases.manage"))],
)
def create_invoice(
    data: PurchaseInvoiceCreate,
    company_id: int = Depends(get_current_company_id),
    db: Session = Depends(get_db),
) -> PurchaseInvoice:
    if service.invoice_number_exists(db, company_id, data.number):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Purchase invoice number '{data.number}' already exists in this company.",
        )
    try:
        return service.create_invoice(db, company_id, data)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.get(
    "/{invoice_id}",
    response_model=PurchaseInvoiceRead,
    dependencies=[Depends(require_permission("purchases.view"))],
)
def get_invoice(
    invoice_id: int,
    company_id: int = Depends(get_current_company_id),
    db: Session = Depends(get_db),
) -> PurchaseInvoice:
    return _get_invoice_or_404(db, company_id, invoice_id)


@router.patch(
    "/{invoice_id}",
    response_model=PurchaseInvoiceRead,
    dependencies=[Depends(require_permission("purchases.manage"))],
)
def update_invoice(
    invoice_id: int,
    data: PurchaseInvoiceUpdate,
    company_id: int = Depends(get_current_company_id),
    db: Session = Depends(get_db),
) -> PurchaseInvoice:
    invoice = _get_invoice_or_404(db, company_id, invoice_id)
    if data.number is not None and service.invoice_number_exists(
        db, company_id, data.number, exclude_id=invoice.id
    ):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Purchase invoice number '{data.number}' already exists in this company.",
        )
    try:
        return service.update_invoice(db, invoice, data)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.post(
    "/{invoice_id}/confirm",
    response_model=PurchaseInvoiceRead,
    dependencies=[Depends(require_permission("purchases.manage"))],
)
def confirm_invoice(
    invoice_id: int,
    company_id: int = Depends(get_current_company_id),
    db: Session = Depends(get_db),
) -> PurchaseInvoice:
    invoice = _get_invoice_or_404(db, company_id, invoice_id)
    try:
        return service.confirm_invoice(db, invoice)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.delete(
    "/{invoice_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_permission("purchases.manage"))],
)
def delete_invoice(
    invoice_id: int,
    company_id: int = Depends(get_current_company_id),
    db: Session = Depends(get_db),
) -> None:
    invoice = _get_invoice_or_404(db, company_id, invoice_id)
    try:
        service.delete_invoice(db, invoice)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
