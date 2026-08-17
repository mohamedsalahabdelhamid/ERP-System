from sqlalchemy import select, func
from sqlalchemy.orm import Session

from app.db.numbering import generate_code
from app.modules.hr.models import Department, Employee, AttendanceRecord, PayrollRun, PayrollLine, LeaveRequest
from app.modules.hr.schemas import DepartmentCreate, EmployeeCreate, AttendanceCreate, PayrollRunCreate, LeaveRequestCreate
from app.modules.accounting.service import get_or_create_default_account, create_journal_entry
from app.modules.accounting.schemas import JournalEntryCreate, JournalLineCreate


def list_departments(db: Session, company_id: int) -> list[Department]:
    return list(db.scalars(select(Department).where(Department.company_id == company_id)).all())


def create_department(db: Session, company_id: int, data: DepartmentCreate) -> Department:
    dept = Department(company_id=company_id, name=data.name)
    db.add(dept)
    db.commit()
    db.refresh(dept)
    return dept


def list_employees(db: Session, company_id: int) -> list[Employee]:
    return list(db.scalars(select(Employee).where(Employee.company_id == company_id)).all())


def employee_number_exists(
    db: Session, company_id: int, employee_number: str
) -> bool:
    stmt = select(Employee.id).where(
        Employee.company_id == company_id,
        Employee.employee_number == employee_number,
    )
    return db.scalar(stmt.limit(1)) is not None


def create_employee(db: Session, company_id: int, data: EmployeeCreate) -> Employee:
    values = data.model_dump()
    if not values.get("employee_number"):
        values["employee_number"] = generate_code(
            db, company_id, "employee", "EMP", Employee, "employee_number"
        )
    emp = Employee(
        company_id=company_id,
        department_id=values.get("department_id"),
        employee_number=values["employee_number"],
        name=values["name"],
        position=values.get("position"),
        hire_date=values.get("hire_date"),
        basic_salary=values.get("basic_salary", 0.0),
    )
    db.add(emp)
    db.commit()
    db.refresh(emp)
    return emp


def create_attendance(db: Session, company_id: int, data: AttendanceCreate) -> AttendanceRecord:
    employee = db.scalar(
        select(Employee).where(
            Employee.id == data.employee_id, Employee.company_id == company_id
        )
    )
    if employee is None:
        raise ValueError("employee_id not found in this company.")
    record = AttendanceRecord(
        company_id=company_id,
        employee_id=data.employee_id,
        date=data.date,
        status=data.status,
        note=data.note
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def list_leave_requests(db: Session, company_id: int) -> list[LeaveRequest]:
    return list(
        db.scalars(
            select(LeaveRequest).where(LeaveRequest.company_id == company_id)
        ).all()
    )


def create_leave_request(
    db: Session, company_id: int, data: LeaveRequestCreate
) -> LeaveRequest:
    employee = db.scalar(
        select(Employee).where(
            Employee.id == data.employee_id, Employee.company_id == company_id
        )
    )
    if employee is None:
        raise ValueError("employee_id not found in this company.")
    record = LeaveRequest(
        company_id=company_id,
        employee_id=data.employee_id,
        leave_type=data.leave_type,
        start_date=data.start_date,
        end_date=data.end_date,
        days=data.days,
        reason=data.reason,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def update_leave_status(
    db: Session, company_id: int, leave_id: int, status: str
) -> LeaveRequest:
    record = db.scalar(
        select(LeaveRequest).where(
            LeaveRequest.id == leave_id, LeaveRequest.company_id == company_id
        )
    )
    if record is None:
        raise ValueError("Leave request not found in this company.")
    record.status = status
    db.commit()
    db.refresh(record)
    return record


def run_payroll(db: Session, company_id: int, data: PayrollRunCreate) -> PayrollRun:
    payroll = PayrollRun(company_id=company_id, period=data.period, status="draft")
    db.add(payroll)
    db.flush()

    employees = list_employees(db, company_id)
    total_gross = 0.0
    total_net = 0.0

    for emp in employees:
        if not emp.is_active:
            continue

        # Count absences in the period
        absences = db.scalar(
            select(func.count(AttendanceRecord.id)).where(
                AttendanceRecord.employee_id == emp.id,
                AttendanceRecord.status == "absent"
            )
        ) or 0

        daily_rate = float(emp.basic_salary) / 30
        deductions = daily_rate * absences
        gross = float(emp.basic_salary)
        net = gross - deductions

        total_gross += gross
        total_net += net

        line = PayrollLine(
            payroll_run_id=payroll.id,
            employee_id=emp.id,
            basic_salary=gross,
            allowances=0,
            deductions=deductions,
            net_salary=net,
            days_worked=30 - absences,
            absent_days=absences
        )
        db.add(line)

    payroll.total_gross = total_gross
    payroll.total_deductions = total_gross - total_net
    payroll.total_net = total_net
    payroll.status = "confirmed"

    # Accounting journal entry
    salaries_acc = get_or_create_default_account(db, company_id, "expense", "6500", "Salaries Expense")
    cash_acc = get_or_create_default_account(db, company_id, "cash", "1010", "Cash & Bank")
    deductions_acc = get_or_create_default_account(db, company_id, "liability", "2300", "Statutory Deductions Payable")
    # The entry must balance: gross salary expense is offset by net cash paid
    # plus the withheld deductions (absences, statutory deductions) that are
    # now payable to the tax/social-insurance authority.
    je_lines = [
        JournalLineCreate(account_id=salaries_acc.id, debit=total_gross, credit=0.0, description=f"Payroll {data.period}"),
        JournalLineCreate(account_id=cash_acc.id, debit=0.0, credit=total_net, description=f"Net Pay {data.period}")
    ]
    if payroll.total_deductions > 0:
        je_lines.append(JournalLineCreate(
            account_id=deductions_acc.id,
            debit=0.0,
            credit=payroll.total_deductions,
            description=f"Payroll Deductions {data.period}"
        ))
    create_journal_entry(db, company_id, JournalEntryCreate(
        reference=f"PAY-{data.period}",
        notes=f"Payroll run for {data.period}",
        lines=je_lines
    ), commit=False)

    db.commit()
    db.refresh(payroll)
    return payroll
