from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.inventory.models import Warehouse, WarehouseStock
from app.modules.items.models import Item
from app.modules.projects.models import Project, ProjectCostLine
from app.modules.sales.models import SalesInvoice


def sales_summary(
    db: Session,
    company_id: int,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
) -> dict:
    """Aggregate sales totals grouped by status within an optional date range."""
    stmt = select(SalesInvoice).where(SalesInvoice.company_id == company_id)
    if start_date:
        stmt = stmt.where(SalesInvoice.date >= start_date)
    if end_date:
        stmt = stmt.where(SalesInvoice.date <= end_date)
    invoices = list(db.scalars(stmt).all())

    totals = {}
    for inv in invoices:
        status = "confirmed" if inv.is_confirmed else "draft"
        totals.setdefault(status, {"count": 0, "total": 0.0})
        totals[status]["count"] += 1
        totals[status]["total"] += float(inv.total_amount or 0)

    grand = sum(t["total"] for t in totals.values())
    return {
        "total_invoices": len(invoices),
        "grand_total": round(grand, 2),
        "by_status": totals,
    }


def stock_value(db: Session, company_id: int) -> dict:
    """Stock valuation: quantity * average cost grouped by warehouse."""
    stocks = list(
        db.scalars(
            select(WarehouseStock).where(
                WarehouseStock.company_id == company_id
            )
        ).all()
    )
    warehouses = {
        w.id: w.name
        for w in db.scalars(
            select(Warehouse).where(Warehouse.company_id == company_id)
        ).all()
    }

    by_warehouse = {}
    total_value = 0.0
    for s in stocks:
        if float(s.quantity) == 0:
            continue
        value = float(s.quantity) * float(s.average_cost or 0)
        total_value += value
        wname = warehouses.get(s.warehouse_id, f"#{s.warehouse_id}")
        by_warehouse[wname] = round(by_warehouse.get(wname, 0.0) + value, 2)

    return {
        "total_value": round(total_value, 2),
        "by_warehouse": by_warehouse,
        "item_count": sum(1 for s in stocks if float(s.quantity) > 0),
    }


def low_stock(db: Session, company_id: int, threshold: float = 10.0) -> list[dict]:
    """Items whose total on-hand quantity is below the threshold."""
    items = {
        i.id: (i.name, i.code)
        for i in db.scalars(
            select(Item).where(Item.company_id == company_id)
        ).all()
    }
    stocks = list(
        db.scalars(
            select(WarehouseStock).where(
                WarehouseStock.company_id == company_id
            )
        ).all()
    )
    totals: dict[int, float] = {}
    for s in stocks:
        totals[s.item_id] = totals.get(s.item_id, 0.0) + float(s.quantity)

    rows = []
    for item_id, qty in totals.items():
        if qty < threshold:
            name, code = items.get(item_id, ("?", "?"))
            rows.append(
                {
                    "item_id": item_id,
                    "code": code,
                    "name": name,
                    "quantity": round(qty, 4),
                }
            )
    rows.sort(key=lambda r: r["quantity"])
    return rows


def project_costs(db: Session, company_id: int) -> dict:
    """Total costs per project from ProjectCostLine."""
    lines = list(
        db.scalars(
            select(ProjectCostLine)
            .join(Project, ProjectCostLine.project_id == Project.id)
            .where(Project.company_id == company_id)
        ).all()
    )
    projects = {
        p.id: (p.name, p.status)
        for p in db.scalars(
            select(Project).where(Project.company_id == company_id)
        ).all()
    }
    by_project = {}
    for line in lines:
        name, status = projects.get(line.project_id, ("?", "?"))
        by_project[line.project_id] = {
            "name": name,
            "status": status,
            "cost": round(
                by_project.get(line.project_id, {}).get("cost", 0.0)
                + float(line.total_cost or 0),
                2,
            ),
        }

    return {
        "projects": list(by_project.values()),
        "total_cost": round(
            sum(p["cost"] for p in by_project.values()), 2
        ),
    }
