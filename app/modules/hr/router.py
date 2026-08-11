from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import (
    get_current_company_id,
    get_db,
    require_module,
    require_permission,
)
from app.modules.hr.schemas import (
    AttendanceCreate,
    AttendanceRead,
    DepartmentCreate,
    DepartmentRead,
    EmployeeCreate,
    EmployeeRead,
    LeaveRequestCreate,
    LeaveRequestRead,
    LeaveRequestStatusUpdate,
    PayrollRunCreate,
    PayrollRunRead,
)
from app.modules.hr.service import (
    create_attendance,
    create_department,
    create_employee,
    create_leave_request,
    list_departments,
    list_employees,
    list_leave_requests,
    run_payroll,
    update_leave_status,
)

router = APIRouter(
    prefix="/hr",
    tags=["hr"],
    dependencies=[Depends(require_module("hr"))],
)


@router.get("/departments", response_model=list[DepartmentRead], dependencies=[Depends(require_permission("hr.view"))])
def list_departments_ep(company_id: int = Depends(get_current_company_id), db: Session = Depends(get_db)):
    return list_departments(db, company_id)


@router.post("/departments", response_model=DepartmentRead, status_code=201, dependencies=[Depends(require_permission("hr.manage"))])
def create_department_ep(data: DepartmentCreate, company_id: int = Depends(get_current_company_id), db: Session = Depends(get_db)):
    return create_department(db, company_id, data)


@router.get("/employees", response_model=list[EmployeeRead], dependencies=[Depends(require_permission("hr.view"))])
def list_employees_ep(company_id: int = Depends(get_current_company_id), db: Session = Depends(get_db)):
    return list_employees(db, company_id)


@router.post("/employees", response_model=EmployeeRead, status_code=201, dependencies=[Depends(require_permission("hr.manage"))])
def create_employee_ep(data: EmployeeCreate, company_id: int = Depends(get_current_company_id), db: Session = Depends(get_db)):
    return create_employee(db, company_id, data)


@router.post("/attendance", response_model=AttendanceRead, status_code=201, dependencies=[Depends(require_permission("hr.manage"))])
def create_attendance_ep(data: AttendanceCreate, company_id: int = Depends(get_current_company_id), db: Session = Depends(get_db)):
    try:
        return create_attendance(db, company_id, data)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/payroll/run", response_model=PayrollRunRead, status_code=201, dependencies=[Depends(require_permission("hr.payroll"))])
def run_payroll_ep(data: PayrollRunCreate, company_id: int = Depends(get_current_company_id), db: Session = Depends(get_db)):
    return run_payroll(db, company_id, data)


@router.get("/leave-requests", response_model=list[LeaveRequestRead], dependencies=[Depends(require_permission("hr.view"))])
def list_leave_requests_ep(company_id: int = Depends(get_current_company_id), db: Session = Depends(get_db)):
    return list_leave_requests(db, company_id)


@router.post("/leave-requests", response_model=LeaveRequestRead, status_code=201, dependencies=[Depends(require_permission("hr.manage"))])
def create_leave_request_ep(data: LeaveRequestCreate, company_id: int = Depends(get_current_company_id), db: Session = Depends(get_db)):
    try:
        return create_leave_request(db, company_id, data)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/leave-requests/{leave_id}/status", response_model=LeaveRequestRead, dependencies=[Depends(require_permission("hr.manage"))])
def update_leave_status_ep(leave_id: int, data: LeaveRequestStatusUpdate, company_id: int = Depends(get_current_company_id), db: Session = Depends(get_db)):
    try:
        return update_leave_status(db, company_id, leave_id, data.status)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
