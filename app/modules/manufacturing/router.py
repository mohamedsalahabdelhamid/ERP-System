from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import (
    get_current_company_id,
    get_db,
    require_module,
    require_permission,
)
from app.modules.manufacturing.models import BOM, BOMLine, WorkOrder
from app.modules.manufacturing.schemas import BOMCreate, WorkOrderCreate, WorkOrderLaborCreate, WorkOrderOverheadCreate
from app.modules.manufacturing.service import create_bom, create_work_order, finish_work_order

router = APIRouter(
    prefix="/manufacturing",
    tags=["manufacturing"],
    dependencies=[Depends(require_module("manufacturing"))],
)


@router.get("/boms", dependencies=[Depends(require_permission("manufacturing.view"))])
def list_boms(company_id: int = Depends(get_current_company_id), db: Session = Depends(get_db)):
    boms = db.scalars(select(BOM).where(BOM.company_id == company_id)).all()
    result = []
    for bom in boms:
        lines = db.scalars(select(BOMLine).where(BOMLine.bom_id == bom.id)).all()
        result.append({
            "id": bom.id,
            "name": bom.name,
            "item_id": bom.item_id,
            "quantity": float(bom.quantity),
            "is_active": bom.is_active,
            "lines": [{"id": l.id, "item_id": l.item_id, "quantity": float(l.quantity)} for l in lines]
        })
    return result


@router.post("/boms", status_code=201, dependencies=[Depends(require_permission("manufacturing.manage"))])
def create_bom_ep(data: BOMCreate, company_id: int = Depends(get_current_company_id), db: Session = Depends(get_db)):
    bom = create_bom(db, company_id, data)
    return {"id": bom.id, "name": bom.name, "item_id": bom.item_id, "quantity": float(bom.quantity)}


@router.get("/work-orders", dependencies=[Depends(require_permission("manufacturing.view"))])
def list_work_orders(company_id: int = Depends(get_current_company_id), db: Session = Depends(get_db)):
    wos = db.scalars(select(WorkOrder).where(WorkOrder.company_id == company_id)).all()
    return [
        {
            "id": wo.id,
            "number": wo.number,
            "item_id": wo.item_id,
            "bom_id": wo.bom_id,
            "warehouse_id": wo.warehouse_id,
            "planned_quantity": float(wo.planned_quantity),
            "status": wo.status,
            "total_material_cost": float(wo.total_material_cost),
            "total_labor_cost": float(wo.total_labor_cost),
            "total_overhead_cost": float(wo.total_overhead_cost),
            "total_cost": float(wo.total_cost),
        }
        for wo in wos
    ]


@router.post("/work-orders", status_code=201, dependencies=[Depends(require_permission("manufacturing.manage"))])
def create_work_order_ep(data: WorkOrderCreate, company_id: int = Depends(get_current_company_id), db: Session = Depends(get_db)):
    wo = create_work_order(db, company_id, data)
    return {"id": wo.id, "number": wo.number, "status": wo.status}


class FinishWorkOrderRequest:
    def __init__(self, labor: list[WorkOrderLaborCreate] = None, overheads: list[WorkOrderOverheadCreate] = None):
        self.labor = labor or []
        self.overheads = overheads or []


from pydantic import BaseModel
from typing import Optional


class FinishRequest(BaseModel):
    labor: list[WorkOrderLaborCreate] = []
    overheads: list[WorkOrderOverheadCreate] = []


@router.post("/work-orders/{wo_id}/finish", dependencies=[Depends(require_permission("manufacturing.manage"))])
def finish_work_order_ep(wo_id: int, data: FinishRequest, company_id: int = Depends(get_current_company_id), db: Session = Depends(get_db)):
    wo = db.scalar(select(WorkOrder).where(WorkOrder.id == wo_id, WorkOrder.company_id == company_id))
    if not wo:
        raise HTTPException(status_code=404, detail="Work order not found")
    try:
        result = finish_work_order(db, wo, data.labor, data.overheads)
        return {"id": result.id, "number": result.number, "status": result.status, "total_cost": float(result.total_cost)}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
