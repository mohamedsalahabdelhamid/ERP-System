"""Item master-data models (spec section 4.2).

Tables:
  - item_categories : per-company category tree (self-referential parent_id).
  - units           : per-company units of measure (Piece, Box, Kg, ...).
                      Unit *conversions* are added in Phase 4.
  - items           : products & services, linked to a category and units.

All tables are scoped to a company.
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
from sqlalchemy.types import JSON

from app.db.base_class import Base
from app.db.mixins import TimestampMixin


class ItemCategory(TimestampMixin, Base):
    __tablename__ = "item_categories"
    __table_args__ = (
        UniqueConstraint(
            "company_id", "code", name="uq_item_categories_company_code"
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    company_id: Mapped[int] = mapped_column(
        ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    code: Mapped[str] = mapped_column(String(50), nullable=False)
    # Self-referential tree; SET NULL keeps children when a parent is removed.
    parent_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("item_categories.id", ondelete="SET NULL"), nullable=True
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)


class Unit(TimestampMixin, Base):
    __tablename__ = "units"
    __table_args__ = (
        UniqueConstraint("company_id", "code", name="uq_units_company_code"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    company_id: Mapped[int] = mapped_column(
        ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    code: Mapped[str] = mapped_column(String(50), nullable=False)
    symbol: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    # unit_type: weight / length / count / volume
    unit_type: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)


class Item(TimestampMixin, Base):
    __tablename__ = "items"
    __table_args__ = (
        UniqueConstraint("company_id", "code", name="uq_items_company_code"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    company_id: Mapped[int] = mapped_column(
        ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    code: Mapped[str] = mapped_column(String(50), nullable=False)
    barcode: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    item_category_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("item_categories.id", ondelete="SET NULL"), nullable=True
    )
    base_unit_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("units.id", ondelete="SET NULL"), nullable=True
    )
    sale_unit_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("units.id", ondelete="SET NULL"), nullable=True
    )
    purchase_unit_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("units.id", ondelete="SET NULL"), nullable=True
    )
    # type: stock / service / manufactured
    type: Mapped[str] = mapped_column(String(20), nullable=False, default="stock")
    default_sale_price: Mapped[float] = mapped_column(
        Numeric(18, 4), nullable=False, default=0
    )
    default_purchase_price: Mapped[float] = mapped_column(
        Numeric(18, 4), nullable=False, default=0
    )
    min_stock_level: Mapped[float] = mapped_column(
        Numeric(18, 4), nullable=False, default=0
    )
    # expiry_control matters for pharmacies (spec 4.2).
    expiry_control: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )
    # attributes: free-form JSON (e.g. size/color for clothing).
    attributes: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
