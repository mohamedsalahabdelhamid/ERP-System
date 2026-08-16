"""Inventory service: company-scoped warehouse CRUD + read-only stock/movements.

Warehouses have full CRUD in Phase 3. ``warehouse_stock`` and
``inventory_movements`` are only read here; writes to them come from later phases
(sales/purchase confirm, stock taking).
"""

from typing import Optional

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.inventory.models import (
    InventoryMovement,
    StockTake,
    StockTakeLine,
    Warehouse,
    WarehouseStock,
)
from app.modules.inventory.schemas import (
    StockTakeCreate,
    WarehouseCreate,
    WarehouseUpdate,
)
from app.modules.items.service import get_item


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


# ------------------------------------------------------------ stock takes
def list_stock_takes(db: Session, company_id: int) -> list[StockTake]:
    stmt = (
        select(StockTake)
        .where(StockTake.company_id == company_id)
        .order_by(StockTake.id.desc())
    )
    return list(db.scalars(stmt).all())


def get_stock_take(
    db: Session, company_id: int, stock_take_id: int
) -> Optional[StockTake]:
    stmt = select(StockTake).where(
        StockTake.id == stock_take_id, StockTake.company_id == company_id
    )
    return db.scalar(stmt)


def create_stock_take(
    db: Session, company_id: int, user_id: int, data: StockTakeCreate
) -> StockTake:
    warehouse = get_warehouse(db, company_id, data.warehouse_id)
    if warehouse is None:
        raise ValueError("warehouse_id not found in this company.")

    stock_take = StockTake(
        company_id=company_id,
        warehouse_id=data.warehouse_id,
        reference=data.reference,
        status="draft",
        created_by=user_id,
        note=data.note,
    )
    db.add(stock_take)
    db.flush()

    for line in data.lines:
        if get_item(db, company_id, line.item_id) is None:
            raise ValueError(f"item_id {line.item_id} not found in this company.")
        stock = db.scalar(
            select(WarehouseStock).where(
                WarehouseStock.company_id == company_id,
                WarehouseStock.warehouse_id == data.warehouse_id,
                WarehouseStock.item_id == line.item_id,
            )
        )
        book_qty = float(stock.quantity) if stock else 0.0
        unit_cost = float(stock.average_cost) if stock else 0.0
        counted = float(line.counted_qty or 0)
        diff = counted - book_qty
        db.add(
            StockTakeLine(
                stock_take_id=stock_take.id,
                item_id=line.item_id,
                book_qty=book_qty,
                counted_qty=counted,
                diff_qty=diff,
                unit_cost=unit_cost,
                adjustment_value=diff * unit_cost,
            )
        )

    db.commit()
    db.refresh(stock_take)
    return stock_take


def post_stock_take(
    db: Session, company_id: int, stock_take_id: int
) -> StockTake:
    stock_take = get_stock_take(db, company_id, stock_take_id)
    if stock_take is None:
        raise ValueError("Stock take not found in this company.")
    if stock_take.status == "posted":
        raise ValueError("Stock take is already posted.")

    lines = list(
        db.scalars(
            select(StockTakeLine).where(
                StockTakeLine.stock_take_id == stock_take.id
            )
        ).all()
    )
    for line in lines:
        if line.diff_qty == 0:
            continue
        stock = db.scalar(
            select(WarehouseStock)
            .where(
                WarehouseStock.company_id == company_id,
                WarehouseStock.warehouse_id == stock_take.warehouse_id,
                WarehouseStock.item_id == line.item_id,
            )
            .with_for_update()
        )
        if stock is None:
            stock = WarehouseStock(
                company_id=company_id,
                warehouse_id=stock_take.warehouse_id,
                item_id=line.item_id,
                quantity=0,
                average_cost=0,
            )
            db.add(stock)
        stock.quantity = float(line.counted_qty or 0)
        if float(stock.quantity) == 0:
            stock.average_cost = 0

        if float(line.diff_qty) > 0:
            db.add(
                InventoryMovement(
                    company_id=company_id,
                    item_id=line.item_id,
                    warehouse_to_id=stock_take.warehouse_id,
                    quantity=abs(float(line.diff_qty)),
                    movement_type="adjustment",
                    unit_cost=float(line.unit_cost),
                    total_cost=abs(float(line.adjustment_value)),
                    document_type="stock_take",
                    document_id=stock_take.id,
                )
            )
        else:
            db.add(
                InventoryMovement(
                    company_id=company_id,
                    item_id=line.item_id,
                    warehouse_from_id=stock_take.warehouse_id,
                    quantity=abs(float(line.diff_qty)),
                    movement_type="adjustment",
                    unit_cost=float(line.unit_cost),
                    total_cost=abs(float(line.adjustment_value)),
                    document_type="stock_take",
                    document_id=stock_take.id,
                )
            )

    stock_take.status = "posted"
    stock_take.posted_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    db.commit()
    db.refresh(stock_take)
    return stock_take
