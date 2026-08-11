from typing import Optional

from sqlalchemy import Boolean, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base_class import Base
from app.db.mixins import TimestampMixin


class BOM(TimestampMixin, Base):
    __tablename__ = "boms"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    company_id: Mapped[int] = mapped_column(
        ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    item_id: Mapped[int] = mapped_column(
        ForeignKey("items.id", ondelete="CASCADE"), nullable=False, index=True
    )
    quantity: Mapped[float] = mapped_column(Numeric(18, 4), nullable=False, default=1)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class BOMLine(TimestampMixin, Base):
    __tablename__ = "bom_lines"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    bom_id: Mapped[int] = mapped_column(
        ForeignKey("boms.id", ondelete="CASCADE"), nullable=False, index=True
    )
    item_id: Mapped[int] = mapped_column(
        ForeignKey("items.id", ondelete="CASCADE"), nullable=False, index=True
    )
    quantity: Mapped[float] = mapped_column(Numeric(18, 4), nullable=False, default=1)


class WorkOrder(TimestampMixin, Base):
    __tablename__ = "work_orders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    company_id: Mapped[int] = mapped_column(
        ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True
    )
    number: Mapped[str] = mapped_column(String(100), nullable=False)
    bom_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("boms.id", ondelete="SET NULL"), nullable=True
    )
    item_id: Mapped[int] = mapped_column(
        ForeignKey("items.id", ondelete="CASCADE"), nullable=False, index=True
    )
    warehouse_id: Mapped[int] = mapped_column(
        ForeignKey("warehouses.id", ondelete="CASCADE"), nullable=False, index=True
    )
    planned_quantity: Mapped[float] = mapped_column(Numeric(18, 4), nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="draft") # draft, in_progress, completed
    total_material_cost: Mapped[float] = mapped_column(Numeric(18, 4), nullable=False, default=0)
    total_labor_cost: Mapped[float] = mapped_column(Numeric(18, 4), nullable=False, default=0)
    total_overhead_cost: Mapped[float] = mapped_column(Numeric(18, 4), nullable=False, default=0)
    total_cost: Mapped[float] = mapped_column(Numeric(18, 4), nullable=False, default=0)


class WorkOrderConsumption(TimestampMixin, Base):
    __tablename__ = "work_order_consumption"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    work_order_id: Mapped[int] = mapped_column(
        ForeignKey("work_orders.id", ondelete="CASCADE"), nullable=False, index=True
    )
    item_id: Mapped[int] = mapped_column(
        ForeignKey("items.id", ondelete="CASCADE"), nullable=False, index=True
    )
    quantity: Mapped[float] = mapped_column(Numeric(18, 4), nullable=False)
    unit_cost: Mapped[float] = mapped_column(Numeric(18, 4), nullable=False, default=0)
    total_cost: Mapped[float] = mapped_column(Numeric(18, 4), nullable=False, default=0)


class WorkOrderLabor(TimestampMixin, Base):
    __tablename__ = "work_order_labor"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    work_order_id: Mapped[int] = mapped_column(
        ForeignKey("work_orders.id", ondelete="CASCADE"), nullable=False, index=True
    )
    description: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    hours: Mapped[float] = mapped_column(Numeric(18, 4), nullable=False)
    hourly_rate: Mapped[float] = mapped_column(Numeric(18, 4), nullable=False, default=0)
    total_cost: Mapped[float] = mapped_column(Numeric(18, 4), nullable=False, default=0)


class WorkOrderOverhead(TimestampMixin, Base):
    __tablename__ = "work_order_overheads"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    work_order_id: Mapped[int] = mapped_column(
        ForeignKey("work_orders.id", ondelete="CASCADE"), nullable=False, index=True
    )
    description: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    total_cost: Mapped[float] = mapped_column(Numeric(18, 4), nullable=False, default=0)


class WorkOrderOutput(TimestampMixin, Base):
    __tablename__ = "work_order_output"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    work_order_id: Mapped[int] = mapped_column(
        ForeignKey("work_orders.id", ondelete="CASCADE"), nullable=False, index=True
    )
    quantity: Mapped[float] = mapped_column(Numeric(18, 4), nullable=False)
    unit_cost: Mapped[float] = mapped_column(Numeric(18, 4), nullable=False, default=0)
    total_cost: Mapped[float] = mapped_column(Numeric(18, 4), nullable=False, default=0)
