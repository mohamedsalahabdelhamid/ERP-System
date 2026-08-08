"""Inventory models (spec section 4.3).

Tables:
  - warehouses          : per-company stock locations (optionally per branch).
  - warehouse_stock     : quantity + average_cost per (warehouse, item).
  - inventory_movements : the stock ledger (stock-in / stock-out / transfer).

In Phase 3 warehouses get full CRUD. ``warehouse_stock`` and
``inventory_movements`` are created here and are **read-only** via the API — they
are populated later (Phase 5+) by sales/purchase confirm logic and stock taking.
"""

from typing import Optional

from sqlalchemy import (
    Boolean,
    ForeignKey,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base_class import Base
from app.db.mixins import TimestampMixin


class Warehouse(TimestampMixin, Base):
    __tablename__ = "warehouses"
    __table_args__ = (
        UniqueConstraint("company_id", "code", name="uq_warehouses_company_code"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    company_id: Mapped[int] = mapped_column(
        ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True
    )
    branch_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("branches.id", ondelete="SET NULL"), nullable=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    code: Mapped[str] = mapped_column(String(50), nullable=False)
    address: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)


class WarehouseStock(TimestampMixin, Base):
    __tablename__ = "warehouse_stock"
    __table_args__ = (
        UniqueConstraint(
            "warehouse_id", "item_id", name="uq_warehouse_stock_warehouse_item"
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    company_id: Mapped[int] = mapped_column(
        ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True
    )
    warehouse_id: Mapped[int] = mapped_column(
        ForeignKey("warehouses.id", ondelete="CASCADE"), nullable=False, index=True
    )
    item_id: Mapped[int] = mapped_column(
        ForeignKey("items.id", ondelete="CASCADE"), nullable=False, index=True
    )
    quantity: Mapped[float] = mapped_column(Numeric(18, 4), nullable=False, default=0)
    # Weighted-average cost per (company, warehouse, item) — spec section 4 costing.
    average_cost: Mapped[float] = mapped_column(
        Numeric(18, 4), nullable=False, default=0
    )


class InventoryMovement(TimestampMixin, Base):
    __tablename__ = "inventory_movements"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    company_id: Mapped[int] = mapped_column(
        ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True
    )
    item_id: Mapped[int] = mapped_column(
        ForeignKey("items.id", ondelete="CASCADE"), nullable=False, index=True
    )
    # Source / destination; a plain in/out uses one side, a transfer uses both.
    warehouse_from_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("warehouses.id", ondelete="SET NULL"), nullable=True
    )
    warehouse_to_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("warehouses.id", ondelete="SET NULL"), nullable=True
    )
    quantity: Mapped[float] = mapped_column(Numeric(18, 4), nullable=False)
    # movement_type: purchase_in / sale_out / transfer / adjustment / ...
    movement_type: Mapped[str] = mapped_column(String(30), nullable=False)
    unit_cost: Mapped[float] = mapped_column(Numeric(18, 4), nullable=False, default=0)
    total_cost: Mapped[float] = mapped_column(
        Numeric(18, 4), nullable=False, default=0
    )
    # Link back to the source document (e.g. sales_invoice / purchase_invoice).
    document_type: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    document_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
