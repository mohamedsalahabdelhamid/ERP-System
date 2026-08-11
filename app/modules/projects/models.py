from typing import Optional
from sqlalchemy import Boolean, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base_class import Base
from app.db.mixins import TimestampMixin


class Project(TimestampMixin, Base):
    __tablename__ = "projects"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    code: Mapped[str] = mapped_column(String(50), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    partner_id: Mapped[Optional[int]] = mapped_column(ForeignKey("partners.id", ondelete="SET NULL"), nullable=True)
    start_date: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    end_date: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    contract_value: Mapped[float] = mapped_column(Numeric(18, 4), nullable=False, default=0)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="active")  # active, completed, cancelled
    total_material_cost: Mapped[float] = mapped_column(Numeric(18, 4), nullable=False, default=0)
    total_labor_cost: Mapped[float] = mapped_column(Numeric(18, 4), nullable=False, default=0)
    total_overhead_cost: Mapped[float] = mapped_column(Numeric(18, 4), nullable=False, default=0)
    total_cost: Mapped[float] = mapped_column(Numeric(18, 4), nullable=False, default=0)


class ProjectCostLine(TimestampMixin, Base):
    __tablename__ = "project_cost_lines"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    cost_type: Mapped[str] = mapped_column(String(50), nullable=False)  # material, labor, overhead
    description: Mapped[str] = mapped_column(String(255), nullable=False)
    quantity: Mapped[float] = mapped_column(Numeric(18, 4), nullable=False, default=1)
    unit_cost: Mapped[float] = mapped_column(Numeric(18, 4), nullable=False, default=0)
    total_cost: Mapped[float] = mapped_column(Numeric(18, 4), nullable=False, default=0)
