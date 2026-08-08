"""Inventory service: company-scoped warehouse CRUD + read-only stock/movements.

Warehouses have full CRUD in Phase 3. ``warehouse_stock`` and
``inventory_movements`` are only read here; writes to them come from later phases
(sales/purchase confirm, stock taking).
"""

from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.inventory.models import (
    InventoryMovement,
    Warehouse,
    WarehouseStock,
)
from app.modules.inventory.schemas import WarehouseCreate, WarehouseUpdate


# -------------------------------------------------------------- warehouses
def list_warehouses(db: Session, company_id: int) -> list[Warehouse]:
    stmt = (
        select(Warehouse)
        .where(Warehouse.company_id == company_id)
        .order_by(Warehouse.name)
    )
    return list(db.scalars(stmt).all())


def get_warehouse(
    db: Session, company_id: int, warehouse_id: int
) -> Optional[Warehouse]:
    stmt = select(Warehouse).where(
        Warehouse.id == warehouse_id, Warehouse.company_id == company_id
    )
    return db.scalar(stmt)


def warehouse_code_exists(
    db: Session, company_id: int, code: str, exclude_id: Optional[int] = None
) -> bool:
    stmt = select(Warehouse.id).where(
        Warehouse.company_id == company_id, Warehouse.code == code
    )
    if exclude_id is not None:
        stmt = stmt.where(Warehouse.id != exclude_id)
    return db.scalar(stmt.limit(1)) is not None


def create_warehouse(
    db: Session, company_id: int, data: WarehouseCreate
) -> Warehouse:
    warehouse = Warehouse(company_id=company_id, **data.model_dump())
    db.add(warehouse)
    db.commit()
    db.refresh(warehouse)
    return warehouse


def update_warehouse(
    db: Session, warehouse: Warehouse, data: WarehouseUpdate
) -> Warehouse:
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(warehouse, field, value)
    db.commit()
    db.refresh(warehouse)
    return warehouse


def delete_warehouse(db: Session, warehouse: Warehouse) -> None:
    db.delete(warehouse)
    db.commit()


# ------------------------------------------------ stock / movements (read-only)
def list_stock(
    db: Session, company_id: int, warehouse_id: Optional[int] = None
) -> list[WarehouseStock]:
    stmt = select(WarehouseStock).where(WarehouseStock.company_id == company_id)
    if warehouse_id is not None:
        stmt = stmt.where(WarehouseStock.warehouse_id == warehouse_id)
    return list(db.scalars(stmt).all())


def list_movements(
    db: Session, company_id: int, item_id: Optional[int] = None
) -> list[InventoryMovement]:
    stmt = (
        select(InventoryMovement)
        .where(InventoryMovement.company_id == company_id)
        .order_by(InventoryMovement.id.desc())
    )
    if item_id is not None:
        stmt = stmt.where(InventoryMovement.item_id == item_id)
    return list(db.scalars(stmt).all())
