from typing import Optional
from sqlalchemy import Boolean, Date, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base_class import Base
from app.db.mixins import TimestampMixin


class Department(TimestampMixin, Base):
    __tablename__ = "departments"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class Employee(TimestampMixin, Base):
    __tablename__ = "employees"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    department_id: Mapped[Optional[int]] = mapped_column(ForeignKey("departments.id", ondelete="SET NULL"), nullable=True)
    employee_number: Mapped[str] = mapped_column(String(50), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    position: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    hire_date: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    basic_salary: Mapped[float] = mapped_column(Numeric(18, 4), nullable=False, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class AttendanceRecord(TimestampMixin, Base):
    __tablename__ = "attendance_records"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    employee_id: Mapped[int] = mapped_column(ForeignKey("employees.id", ondelete="CASCADE"), nullable=False, index=True)
    date: Mapped[str] = mapped_column(String(20), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="present")  # present, absent, half_day, leave
    note: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)


class PayrollRun(TimestampMixin, Base):
    __tablename__ = "payroll_runs"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    period: Mapped[str] = mapped_column(String(20), nullable=False)  # e.g. 2026-08
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="draft")  # draft, confirmed
    total_gross: Mapped[float] = mapped_column(Numeric(18, 4), nullable=False, default=0)
    total_deductions: Mapped[float] = mapped_column(Numeric(18, 4), nullable=False, default=0)
    total_net: Mapped[float] = mapped_column(Numeric(18, 4), nullable=False, default=0)


class PayrollLine(TimestampMixin, Base):
    __tablename__ = "payroll_lines"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    payroll_run_id: Mapped[int] = mapped_column(ForeignKey("payroll_runs.id", ondelete="CASCADE"), nullable=False, index=True)
    employee_id: Mapped[int] = mapped_column(ForeignKey("employees.id", ondelete="CASCADE"), nullable=False, index=True)
    basic_salary: Mapped[float] = mapped_column(Numeric(18, 4), nullable=False, default=0)
    allowances: Mapped[float] = mapped_column(Numeric(18, 4), nullable=False, default=0)
    deductions: Mapped[float] = mapped_column(Numeric(18, 4), nullable=False, default=0)
    net_salary: Mapped[float] = mapped_column(Numeric(18, 4), nullable=False, default=0)
    days_worked: Mapped[int] = mapped_column(Integer, nullable=False, default=30)
    absent_days: Mapped[int] = mapped_column(Integer, nullable=False, default=0)


class LeaveRequest(TimestampMixin, Base):
    __tablename__ = "leave_requests"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    employee_id: Mapped[int] = mapped_column(ForeignKey("employees.id", ondelete="CASCADE"), nullable=False, index=True)
    leave_type: Mapped[str] = mapped_column(String(50), nullable=False)  # annual, sick, unpaid, ...
    start_date: Mapped[str] = mapped_column(String(20), nullable=False)
    end_date: Mapped[str] = mapped_column(String(20), nullable=False)
    days: Mapped[float] = mapped_column(Numeric(18, 4), nullable=False, default=1)
    reason: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")  # pending, approved, rejected
