"""Inventory API endpoints (Phase 3).

  - /warehouses            full CRUD (warehouses.view / warehouses.manage)
  - /warehouse-stock       read-only stock levels (stock.view)
  - /inventory-movements   read-only movement ledger (movements.view)

Stock and movements are read-only in Phase 3; they are written by later phases
(sales/purchase confirm, stock taking).
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import (
    get_current_company_id,
    get_current_user,
    get_db,
    require_module,
    require_permission,
)
from app.modules.inventory import service
from app.modules.inventory.models import (
    InventoryMovement,
    StockTake,
    Warehouse,
    WarehouseStock,
)
from app.modules.inventory.schemas import (
    InventoryMovementRead,
    StockTakeCreate,
    StockTakeRead,
    WarehouseCreate,
    WarehouseRead,
    WarehouseStockRead,
    WarehouseUpdate,
)

_MODULE = Depends(require_module("inventory"))

warehouses_router = APIRouter(
    prefix="/warehouses", tags=["warehouses"], dependencies=[_MODULE]
)
stock_router = APIRouter(
    prefix="/warehouse-stock", tags=["warehouse-stock"], dependencies=[_MODULE]
)
movements_router = APIRouter(
    prefix="/inventory-movements",
    tags=["inventory-movements"],
    dependencies=[_MODULE],
)
stock_takes_router = APIRouter(
    prefix="/stock-takes", tags=["stock-takes"], dependencies=[_MODULE]
)


# ===================================================================== warehouses
def _get_warehouse_or_404(
    db: Session, company_id: int, warehouse_id: int
) -> Warehouse:
    warehouse = service.get_warehouse(db, company_id, warehouse_id)
    if warehouse is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Warehouse not found."
        )
    return warehouse


@warehouses_router.get(
    "",
    response_model=list[WarehouseRead],
    dependencies=[Depends(require_permission("warehouses.view"))],
)
def list_warehouses(
    company_id: int = Depends(get_current_company_id),
    db: Session = Depends(get_db),
) -> list[Warehouse]:
    return service.list_warehouses(db, company_id)


@warehouses_router.post(
    "",
    response_model=WarehouseRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission("warehouses.manage"))],
)
def create_warehouse(
    data: WarehouseCreate,
    company_id: int = Depends(get_current_company_id),
    db: Session = Depends(get_db),
) -> Warehouse:
    if data.code and service.warehouse_code_exists(db, company_id, data.code):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Warehouse code '{data.code}' already exists in this company.",
        )
    return service.create_warehouse(db, company_id, data)


@warehouses_router.get(
    "/{warehouse_id}",
    response_model=WarehouseRead,
    dependencies=[Depends(require_permission("warehouses.view"))],
)
def get_warehouse(
    warehouse_id: int,
    company_id: int = Depends(get_current_company_id),
    db: Session = Depends(get_db),
) -> Warehouse:
    return _get_warehouse_or_404(db, company_id, warehouse_id)


@warehouses_router.patch(
    "/{warehouse_id}",
    response_model=WarehouseRead,
    dependencies=[Depends(require_permission("warehouses.manage"))],
)
def update_warehouse(
    warehouse_id: int,
    data: WarehouseUpdate,
    company_id: int = Depends(get_current_company_id),
    db: Session = Depends(get_db),
) -> Warehouse:
    warehouse = _get_warehouse_or_404(db, company_id, warehouse_id)
    if data.code is not None and service.warehouse_code_exists(
        db, company_id, data.code, exclude_id=warehouse.id
    ):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Warehouse code '{data.code}' already exists in this company.",
        )
    return service.update_warehouse(db, warehouse, data)


@warehouses_router.delete(
    "/{warehouse_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_permission("warehouses.delete"))],
)
def delete_warehouse(
    warehouse_id: int,
    company_id: int = Depends(get_current_company_id),
    db: Session = Depends(get_db),
) -> None:
    warehouse = _get_warehouse_or_404(db, company_id, warehouse_id)
    service.delete_warehouse(db, warehouse)


# ================================================================ warehouse stock
@stock_router.get(
    "",
    response_model=list[WarehouseStockRead],
    dependencies=[Depends(require_permission("stock.view"))],
)
def list_stock(
    warehouse_id: Optional[int] = Query(default=None),
    company_id: int = Depends(get_current_company_id),
    db: Session = Depends(get_db),
) -> list[WarehouseStock]:
    return service.list_stock(db, company_id, warehouse_id)


# ============================================================ inventory movements
@movements_router.get(
    "",
    response_model=list[InventoryMovementRead],
    dependencies=[Depends(require_permission("movements.view"))],
)
def list_movements(
    item_id: Optional[int] = Query(default=None),
    company_id: int = Depends(get_current_company_id),
    db: Session = Depends(get_db),
) -> list[InventoryMovement]:
    return service.list_movements(db, company_id, item_id)


# ================================================================= stock takes
@stock_takes_router.get(
    "",
    response_model=list[StockTakeRead],
    dependencies=[Depends(require_permission("stock_takes.view"))],
)
def list_stock_takes(
    company_id: int = Depends(get_current_company_id),
    db: Session = Depends(get_db),
) -> list[StockTake]:
    return service.list_stock_takes(db, company_id)


@stock_takes_router.get(
    "/{stock_take_id}",
    response_model=StockTakeRead,
    dependencies=[Depends(require_permission("stock_takes.view"))],
)
def get_stock_take(
    stock_take_id: int,
    company_id: int = Depends(get_current_company_id),
    db: Session = Depends(get_db),
):
    st = service.get_stock_take(db, company_id, stock_take_id)
    if st is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Stock take not found")
    return st


@stock_takes_router.post(
    "",
    response_model=StockTakeRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission("stock_takes.manage"))],
)
def create_stock_take(
    data: StockTakeCreate,
    user=Depends(get_current_user),
    company_id: int = Depends(get_current_company_id),
    db: Session = Depends(get_db),
):
    if data.reference and service.stock_take_reference_exists(
        db, company_id, data.reference
    ):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Stock take reference '{data.reference}' already exists in this company.",
        )
    try:
        return service.create_stock_take(db, company_id, user.id, data)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@stock_takes_router.post(
    "/{stock_take_id}/post",
    response_model=StockTakeRead,
    dependencies=[Depends(require_permission("stock_takes.manage"))],
)
def post_stock_take(
    stock_take_id: int,
    company_id: int = Depends(get_current_company_id),
    db: Session = Depends(get_db),
):
    try:
        return service.post_stock_take(db, company_id, stock_take_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
