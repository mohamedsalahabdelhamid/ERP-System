from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import (
    get_current_company_id,
    get_db,
    require_module,
    require_permission,
)
from app.modules.reports import service

router = APIRouter(prefix="/reports", tags=["reports"])


@router.get(
    "/sales-summary",
    dependencies=[
        Depends(require_module("sales")),
        Depends(require_permission("accounting.reports")),
    ],
)
def sales_summary(
    start_date: Optional[str] = Query(default=None),
    end_date: Optional[str] = Query(default=None),
    company_id: int = Depends(get_current_company_id),
    db: Session = Depends(get_db),
) -> dict:
    return service.sales_summary(db, company_id, start_date, end_date)


@router.get(
    "/stock-value",
    dependencies=[
        Depends(require_module("inventory")),
        Depends(require_permission("stock_takes.view")),
    ],
)
def stock_value(
    company_id: int = Depends(get_current_company_id),
    db: Session = Depends(get_db),
) -> dict:
    return service.stock_value(db, company_id)


@router.get(
    "/low-stock",
    dependencies=[
        Depends(require_module("inventory")),
        Depends(require_permission("stock_takes.view")),
    ],
)
def low_stock(
    threshold: float = Query(default=10.0),
    company_id: int = Depends(get_current_company_id),
    db: Session = Depends(get_db),
) -> list[dict]:
    return service.low_stock(db, company_id, threshold)


@router.get(
    "/project-costs",
    dependencies=[
        Depends(require_module("projects")),
        Depends(require_permission("projects.view")),
    ],
)
def project_costs(
    company_id: int = Depends(get_current_company_id),
    db: Session = Depends(get_db),
) -> dict:
    return service.project_costs(db, company_id)
