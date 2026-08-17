"""Pydantic schemas for inventory: warehouses, stock, movements."""

from typing import Optional

from pydantic import BaseModel, ConfigDict


# ---- Warehouses (full CRUD) ----
class WarehouseCreate(BaseModel):
    name: str
    # Optional: auto-generated per company when omitted (WH-###).
    code: Optional[str] = None
    branch_id: Optional[int] = None
    address: Optional[str] = None
    is_active: bool = True


class WarehouseUpdate(BaseModel):
    name: Optional[str] = None
    code: Optional[str] = None
    branch_id: Optional[int] = None
    address: Optional[str] = None
    is_active: Optional[bool] = None


class WarehouseRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    company_id: int
    branch_id: Optional[int]
    name: str
    code: str
    address: Optional[str]
    is_active: bool


# ---- Warehouse stock (read-only in Phase 3) ----
class WarehouseStockRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    company_id: int
    warehouse_id: int
    item_id: int
    quantity: float
    average_cost: float


# ---- Inventory movements (read-only in Phase 3) ----
class InventoryMovementRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    company_id: int
    item_id: int
    warehouse_from_id: Optional[int]
    warehouse_to_id: Optional[int]
    quantity: float
    movement_type: str
    unit_cost: float
    total_cost: float
    document_type: Optional[str]
    document_id: Optional[int]


# ---- Stock taking & adjustments (Phase 6.3) ----
class StockTakeLineCreate(BaseModel):
    item_id: int
    counted_qty: float = 0


class StockTakeCreate(BaseModel):
    warehouse_id: int
    # Optional: auto-generated per company when omitted (ST-###).
    reference: Optional[str] = None
    note: Optional[str] = None
    lines: list[StockTakeLineCreate] = []


class StockTakeLineRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    stock_take_id: int
    item_id: int
    book_qty: float
    counted_qty: float
    diff_qty: float
    unit_cost: float
    adjustment_value: float


class StockTakeRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    company_id: int
    warehouse_id: int
    reference: str
    status: str
    created_by: int
    posted_at: Optional[str]
    note: Optional[str]
    lines: list[StockTakeLineRead] = []
