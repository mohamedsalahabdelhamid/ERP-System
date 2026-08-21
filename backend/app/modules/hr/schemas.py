from typing import Optional
from pydantic import BaseModel, Field


class DepartmentCreate(BaseModel):
    name: str = Field(..., min_length=1)


class DepartmentRead(DepartmentCreate):
    id: int
    is_active: bool


class EmployeeCreate(BaseModel):
    department_id: Optional[int] = None
    # Optional: auto-generated per company when omitted (EMP-###).
    employee_number: Optional[str] = None
    name: str = Field(..., min_length=1)
    position: Optional[str] = None
    hire_date: Optional[str] = None
    basic_salary: float = 0.0


class EmployeeRead(EmployeeCreate):
    id: int
    is_active: bool


class AttendanceCreate(BaseModel):
    employee_id: int
    date: str
    status: str = "present"
    note: Optional[str] = None


class AttendanceRead(AttendanceCreate):
    id: int
    company_id: int


class PayrollRunCreate(BaseModel):
    period: str = Field(..., min_length=1)


class PayrollRunRead(PayrollRunCreate):
    id: int
    status: str
    total_gross: float
    total_deductions: float
    total_net: float


class LeaveRequestCreate(BaseModel):
    employee_id: int
    leave_type: str = "annual"
    start_date: str
    end_date: str
    days: float = 1.0
    reason: Optional[str] = None


class LeaveRequestStatusUpdate(BaseModel):
    status: str = Field(..., pattern="^(pending|approved|rejected|cancelled)$")


class LeaveRequestRead(LeaveRequestCreate):
    id: int
    company_id: int
    status: str
