from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import (
    get_current_company_id,
    get_db,
    require_module,
    require_permission,
)
from app.modules.projects.schemas import ProjectCreate, ProjectRead, ProjectCostLineCreate, ProjectCostLineRead
from app.modules.projects.service import list_projects, create_project, add_cost_line, complete_project, project_code_exists

router = APIRouter(
    prefix="/projects",
    tags=["projects"],
    dependencies=[Depends(require_module("projects"))],
)


@router.get("/", response_model=list[ProjectRead], dependencies=[Depends(require_permission("projects.view"))])
def list_projects_ep(company_id: int = Depends(get_current_company_id), db: Session = Depends(get_db)):
    return list_projects(db, company_id)


@router.post("/", response_model=ProjectRead, status_code=201, dependencies=[Depends(require_permission("projects.manage"))])
def create_project_ep(data: ProjectCreate, company_id: int = Depends(get_current_company_id), db: Session = Depends(get_db)):
    if data.code and project_code_exists(db, company_id, data.code):
        raise HTTPException(
            status_code=409,
            detail=f"Project code '{data.code}' already exists in this company.",
        )
    return create_project(db, company_id, data)


@router.post("/{project_id}/costs", response_model=ProjectCostLineRead, status_code=201, dependencies=[Depends(require_permission("projects.manage"))])
def add_cost_ep(project_id: int, data: ProjectCostLineCreate, company_id: int = Depends(get_current_company_id), db: Session = Depends(get_db)):
    try:
        return add_cost_line(db, company_id, project_id, data)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/{project_id}/complete", response_model=ProjectRead, dependencies=[Depends(require_permission("projects.manage"))])
def complete_project_ep(project_id: int, company_id: int = Depends(get_current_company_id), db: Session = Depends(get_db)):
    try:
        return complete_project(db, company_id, project_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
