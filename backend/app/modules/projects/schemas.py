from typing import Optional
from pydantic import BaseModel, Field


class ProjectCreate(BaseModel):
    # Optional: auto-generated per company when omitted (PRJ-###).
    code: Optional[str] = None
    name: str = Field(..., min_length=1)
    partner_id: Optional[int] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    contract_value: float = 0.0


class ProjectRead(ProjectCreate):
    id: int
    status: str
    total_cost: float
    total_material_cost: float
    total_labor_cost: float
    total_overhead_cost: float


class ProjectCostLineCreate(BaseModel):
    cost_type: str
    description: str
    quantity: float = 1.0
    unit_cost: float = 0.0


class ProjectCostLineRead(ProjectCostLineCreate):
    id: int
    total_cost: float
