from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import (
    get_current_company_id,
    get_db,
    require_module,
    require_permission,
)
from app.modules.sales import service
from app.modules.sales.models import SalesInvoice
from app.modules.sales.schemas import (
    SalesInvoiceCreate,
    SalesInvoiceRead,
    SalesInvoiceUpdate,
)

router = APIRouter(
    prefix="/sales-invoices",
    tags=["sales-invoices"],
    dependencies=[Depends(require_module("sales"))],
)


def _get_invoice_or_404(db: Session, company_id: int, invoice_id: int) -> SalesInvoice:
    invoice = service.get_invoice(db, company_id, invoice_id)
    if invoice is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Sales invoice not found."
        )
    return invoice


@router.get(
    "",
    response_model=list[SalesInvoiceRead],
    dependencies=[Depends(require_permission("sales.view"))],
)
def list_invoices(
    company_id: int = Depends(get_current_company_id),
    db: Session = Depends(get_db),
) -> list[SalesInvoice]:
    return service.list_invoices(db, company_id)


@router.post(
    "",
    response_model=SalesInvoiceRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission("sales.manage"))],
)
def create_invoice(
    data: SalesInvoiceCreate,
    company_id: int = Depends(get_current_company_id),
    db: Session = Depends(get_db),
) -> SalesInvoice:
    if service.invoice_number_exists(db, company_id, data.number):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Sales invoice number '{data.number}' already exists in this company.",
        )
    try:
        return service.create_invoice(db, company_id, data)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.get(
    "/{invoice_id}",
    response_model=SalesInvoiceRead,
    dependencies=[Depends(require_permission("sales.view"))],
)
def get_invoice(
    invoice_id: int,
    company_id: int = Depends(get_current_company_id),
    db: Session = Depends(get_db),
) -> SalesInvoice:
    return _get_invoice_or_404(db, company_id, invoice_id)


@router.patch(
    "/{invoice_id}",
    response_model=SalesInvoiceRead,
    dependencies=[Depends(require_permission("sales.manage"))],
)
def update_invoice(
    invoice_id: int,
    data: SalesInvoiceUpdate,
    company_id: int = Depends(get_current_company_id),
    db: Session = Depends(get_db),
) -> SalesInvoice:
    invoice = _get_invoice_or_404(db, company_id, invoice_id)
    if data.number is not None and service.invoice_number_exists(
        db, company_id, data.number, exclude_id=invoice.id
    ):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Sales invoice number '{data.number}' already exists in this company.",
        )
    try:
        return service.update_invoice(db, invoice, data)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.post(
    "/{invoice_id}/confirm",
    response_model=SalesInvoiceRead,
    dependencies=[Depends(require_permission("sales.manage"))],
)
def confirm_invoice(
    invoice_id: int,
    company_id: int = Depends(get_current_company_id),
    db: Session = Depends(get_db),
) -> SalesInvoice:
    invoice = _get_invoice_or_404(db, company_id, invoice_id)
    try:
        return service.confirm_invoice(db, invoice)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.delete(
    "/{invoice_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_permission("sales.manage"))],
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
