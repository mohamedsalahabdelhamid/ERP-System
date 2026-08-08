"""Multi-company core models (spec section 3.1).

Tables:
  - companies         : the tenant/company record.
  - branches          : per-company branches.
  - company_settings  : per-company configuration (1:1 with companies).
"""

from typing import Optional

from sqlalchemy import (
    Boolean,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from app.db.base_class import Base
from app.db.mixins import TimestampMixin


class Company(TimestampMixin, Base):
    __tablename__ = "companies"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    code: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    base_currency: Mapped[str] = mapped_column(String(3), nullable=False)
    # activity_type: manufacturing / trading / pharmacy / ... / mixed (spec 1.1).
    activity_type: Mapped[str] = mapped_column(String(50), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    branches: Mapped[list["Branch"]] = relationship(
        back_populates="company", cascade="all, delete-orphan"
    )
    settings: Mapped[Optional["CompanySettings"]] = relationship(
        back_populates="company",
        cascade="all, delete-orphan",
        uselist=False,
    )


class Branch(TimestampMixin, Base):
    __tablename__ = "branches"
    __table_args__ = (
        # Branch codes are unique within a company.
        UniqueConstraint("company_id", "code", name="uq_branches_company_code"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    company_id: Mapped[int] = mapped_column(
        ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    code: Mapped[str] = mapped_column(String(50), nullable=False)
    address: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    company: Mapped["Company"] = relationship(back_populates="branches")


class CompanySettings(TimestampMixin, Base):
    __tablename__ = "company_settings"

    # 1:1 with companies -> company_id is both PK and FK.
    company_id: Mapped[int] = mapped_column(
        ForeignKey("companies.id", ondelete="CASCADE"), primary_key=True
    )
    enabled_modules: Mapped[list] = mapped_column(
        JSON, nullable=False, default=list
    )
    cost_method: Mapped[str] = mapped_column(
        String(50), nullable=False, default="weighted_average"
    )
    has_manufacturing: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )
    has_projects: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    has_pos: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    # pos_style: retail / restaurant / pharmacy / ... (nullable when has_pos is False)
    pos_style: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    company: Mapped["Company"] = relationship(back_populates="settings")
