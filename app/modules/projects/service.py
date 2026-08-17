from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.numbering import generate_code
from app.modules.projects.models import Project, ProjectCostLine
from app.modules.projects.schemas import ProjectCreate, ProjectCostLineCreate
from app.modules.accounting.service import get_or_create_default_account, create_journal_entry
from app.modules.accounting.schemas import JournalEntryCreate, JournalLineCreate


def list_projects(db: Session, company_id: int) -> list[Project]:
    return list(db.scalars(select(Project).where(Project.company_id == company_id)).all())


def get_project(db: Session, company_id: int, project_id: int) -> Project | None:
    return db.scalar(select(Project).where(Project.id == project_id, Project.company_id == company_id))


def project_code_exists(db: Session, company_id: int, code: str) -> bool:
    stmt = select(Project.id).where(
        Project.company_id == company_id, Project.code == code
    )
    return db.scalar(stmt.limit(1)) is not None


def create_project(db: Session, company_id: int, data: ProjectCreate) -> Project:
    values = data.model_dump()
    if not values.get("code"):
        values["code"] = generate_code(db, company_id, "project", "PRJ", Project, "code")
    proj = Project(
        company_id=company_id,
        code=values["code"],
        name=values["name"],
        partner_id=values.get("partner_id"),
        start_date=values.get("start_date"),
        end_date=values.get("end_date"),
        contract_value=values.get("contract_value", 0.0),
        status="active"
    )
    db.add(proj)
    db.commit()
    db.refresh(proj)
    return proj


def add_cost_line(db: Session, company_id: int, project_id: int, data: ProjectCostLineCreate) -> ProjectCostLine:
    proj = get_project(db, company_id, project_id)
    if not proj:
        raise ValueError("Project not found")

    total_cost = data.quantity * data.unit_cost
    line = ProjectCostLine(
        project_id=project_id,
        cost_type=data.cost_type,
        description=data.description,
        quantity=data.quantity,
        unit_cost=data.unit_cost,
        total_cost=total_cost
    )
    db.add(line)

    # Update project totals
    if data.cost_type == "material":
        proj.total_material_cost = float(proj.total_material_cost or 0) + total_cost
    elif data.cost_type == "labor":
        proj.total_labor_cost = float(proj.total_labor_cost or 0) + total_cost
    else:
        proj.total_overhead_cost = float(proj.total_overhead_cost or 0) + total_cost
    proj.total_cost = float(proj.total_material_cost or 0) + float(proj.total_labor_cost or 0) + float(proj.total_overhead_cost or 0)

    # Journal entry for the cost
    wip_acc = get_or_create_default_account(db, company_id, "asset", "1500", "Work In Progress - Projects")
    cash_acc = get_or_create_default_account(db, company_id, "cash", "1010", "Cash & Bank")
    create_journal_entry(db, company_id, JournalEntryCreate(
        reference=f"PROJ-{proj.code}-COST",
        notes=f"Project cost: {data.description}",
        lines=[
            JournalLineCreate(account_id=wip_acc.id, debit=total_cost, credit=0.0, description=data.description),
            JournalLineCreate(account_id=cash_acc.id, debit=0.0, credit=total_cost, description=data.description),
        ]
    ))

    db.commit()
    db.refresh(line)
    return line


def complete_project(db: Session, company_id: int, project_id: int) -> Project:
    proj = get_project(db, company_id, project_id)
    if not proj:
        raise ValueError("Project not found")
    proj.status = "completed"
    db.commit()
    db.refresh(proj)
    return proj
