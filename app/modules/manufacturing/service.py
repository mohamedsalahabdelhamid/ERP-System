from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.manufacturing.models import BOM, BOMLine, WorkOrder, WorkOrderConsumption, WorkOrderLabor, WorkOrderOverhead, WorkOrderOutput
from app.modules.manufacturing.schemas import BOMCreate, WorkOrderCreate, WorkOrderLaborCreate, WorkOrderOverheadCreate
from app.modules.inventory.models import InventoryMovement, WarehouseStock
from app.modules.accounting.service import get_or_create_default_account, create_journal_entry
from app.modules.accounting.schemas import JournalEntryCreate, JournalLineCreate


def create_bom(db: Session, company_id: int, data: BOMCreate) -> BOM:
    bom = BOM(
        company_id=company_id,
        name=data.name,
        item_id=data.item_id,
        quantity=data.quantity
    )
    db.add(bom)
    db.commit()
    db.refresh(bom)
    
    for line in data.lines:
        bom_line = BOMLine(
            bom_id=bom.id,
            item_id=line.item_id,
            quantity=line.quantity
        )
        db.add(bom_line)
    db.commit()
    db.refresh(bom)
    return bom

def create_work_order(db: Session, company_id: int, data: WorkOrderCreate) -> WorkOrder:
    wo = WorkOrder(
        company_id=company_id,
        number=data.number,
        bom_id=data.bom_id,
        item_id=data.item_id,
        warehouse_id=data.warehouse_id,
        planned_quantity=data.planned_quantity,
        status="draft"
    )
    db.add(wo)
    db.commit()
    db.refresh(wo)
    return wo

def finish_work_order(db: Session, wo: WorkOrder, labor: list[WorkOrderLaborCreate], overheads: list[WorkOrderOverheadCreate]) -> WorkOrder:
    if wo.status == "completed":
        return wo
        
    # Process consumption based on BOM if exists
    total_material_cost = 0.0
    
    if wo.bom_id:
        bom_lines = db.scalars(select(BOMLine).where(BOMLine.bom_id == wo.bom_id)).all()
        bom_obj = db.scalar(select(BOM).where(BOM.id == wo.bom_id))
        bom_output_qty = float(bom_obj.quantity) if bom_obj else 1.0
        multiplier = float(wo.planned_quantity) / bom_output_qty
        
        for bl in bom_lines:
            req_qty = float(bl.quantity) * multiplier
            
            # Stock lookup
            stock = db.scalar(select(WarehouseStock).where(
                WarehouseStock.company_id == wo.company_id,
                WarehouseStock.warehouse_id == wo.warehouse_id,
                WarehouseStock.item_id == bl.item_id
            ))
            
            if stock:
                unit_cost = float(stock.average_cost)
                cost = unit_cost * req_qty
                stock.quantity = float(stock.quantity) - req_qty
            else:
                unit_cost = 0.0
                cost = 0.0
                
            total_material_cost += cost
            
            woc = WorkOrderConsumption(
                work_order_id=wo.id,
                item_id=bl.item_id,
                quantity=req_qty,
                unit_cost=unit_cost,
                total_cost=cost
            )
            db.add(woc)
            
            # Stock movement out
            db.add(InventoryMovement(
                company_id=wo.company_id,
                item_id=bl.item_id,
                warehouse_from_id=wo.warehouse_id,
                quantity=req_qty,
                movement_type="manufacturing_out",
                unit_cost=unit_cost,
                total_cost=cost,
                document_type="work_order",
                document_id=wo.id
            ))
            
    total_labor_cost = sum(l.hours * l.hourly_rate for l in labor)
    for l in labor:
        db.add(WorkOrderLabor(work_order_id=wo.id, description=l.description, hours=l.hours, hourly_rate=l.hourly_rate, total_cost=l.hours*l.hourly_rate))
        
    total_overhead_cost = sum(o.total_cost for o in overheads)
    for o in overheads:
        db.add(WorkOrderOverhead(work_order_id=wo.id, description=o.description, total_cost=o.total_cost))
        
    total_cost = total_material_cost + total_labor_cost + total_overhead_cost
    unit_cost_out = total_cost / float(wo.planned_quantity)
    
    # Produce finished goods
    output = WorkOrderOutput(
        work_order_id=wo.id,
        quantity=float(wo.planned_quantity),
        unit_cost=unit_cost_out,
        total_cost=total_cost
    )
    db.add(output)
    
    # Stock movement in
    stock_in = db.scalar(select(WarehouseStock).where(
        WarehouseStock.company_id == wo.company_id,
        WarehouseStock.warehouse_id == wo.warehouse_id,
        WarehouseStock.item_id == wo.item_id
    ))
    
    if stock_in is None:
        stock_in = WarehouseStock(company_id=wo.company_id, warehouse_id=wo.warehouse_id, item_id=wo.item_id, quantity=0, average_cost=0)
        db.add(stock_in)
        
    old_qty = float(stock_in.quantity)
    old_cost = float(stock_in.average_cost)
    new_qty = old_qty + float(wo.planned_quantity)
    
    stock_in.average_cost = ((old_qty * old_cost) + total_cost) / new_qty
    stock_in.quantity = new_qty
    
    db.add(InventoryMovement(
        company_id=wo.company_id,
        item_id=wo.item_id,
        warehouse_to_id=wo.warehouse_id,
        quantity=float(wo.planned_quantity),
        movement_type="manufacturing_in",
        unit_cost=unit_cost_out,
        total_cost=total_cost,
        document_type="work_order",
        document_id=wo.id
    ))
    
    wo.total_material_cost = total_material_cost
    wo.total_labor_cost = total_labor_cost
    wo.total_overhead_cost = total_overhead_cost
    wo.total_cost = total_cost
    wo.status = "completed"
    
    # Accounting Integration
    inv_account = get_or_create_default_account(db, wo.company_id, "inventory", "1200", "Inventory")
    labor_acc = get_or_create_default_account(db, wo.company_id, "expense", "6100", "Direct Labor Applied")
    overhead_acc = get_or_create_default_account(db, wo.company_id, "expense", "6200", "Manufacturing Overhead Applied")

    je_lines = [
        JournalLineCreate(account_id=inv_account.id, debit=total_cost, credit=0.0, description="Finished Goods In"),
        JournalLineCreate(account_id=inv_account.id, debit=0.0, credit=total_material_cost, description="Raw Materials Out")
    ]
    if total_labor_cost > 0:
        je_lines.append(JournalLineCreate(account_id=labor_acc.id, debit=0.0, credit=total_labor_cost, description="Labor Applied"))
    if total_overhead_cost > 0:
        je_lines.append(JournalLineCreate(account_id=overhead_acc.id, debit=0.0, credit=total_overhead_cost, description="Overhead Applied"))
        
    create_journal_entry(db, wo.company_id, JournalEntryCreate(
        reference=f"WO-{wo.number}",
        entry_date=None,
        notes=f"Work Order {wo.number} Completion",
        lines=je_lines
    ))
    
    db.commit()
    db.refresh(wo)
    return wo
