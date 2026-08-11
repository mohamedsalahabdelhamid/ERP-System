from typing import Optional

from pydantic import BaseModel, Field


class BOMLineCreate(BaseModel):
    item_id: int
    quantity: float


class BOMCreate(BaseModel):
    name: str = Field(..., min_length=1)
    item_id: int
    quantity: float = 1.0
    lines: list[BOMLineCreate]


class WorkOrderCreate(BaseModel):
    number: str = Field(..., min_length=1)
    bom_id: Optional[int] = None
    item_id: int
    warehouse_id: int
    planned_quantity: float


class WorkOrderConsumptionCreate(BaseModel):
    item_id: int
    quantity: float


class WorkOrderLaborCreate(BaseModel):
    description: Optional[str] = None
    hours: float
    hourly_rate: float


class WorkOrderOverheadCreate(BaseModel):
    description: Optional[str] = None
    total_cost: float
