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
    # Unique subdomain used by the tenant portal: <subdomain>.<domain>.
    subdomain: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True, unique=True
    )
    # status: active / trial / suspended (suspended blocks all tenant access).
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="active", server_default="active"
    )
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
    # Licensed seat count: the company owner may create up to max_users users
    # (excludes the platform-created owner account when desired).
    max_users: Mapped[int] = mapped_column(
        Integer, nullable=False, default=5, server_default="5"
    )
    has_manufacturing: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )
    has_projects: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    has_pos: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    # pos_style: retail / restaurant / pharmacy / ... (nullable when has_pos is False)
    pos_style: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # ---- Stock Alert Settings ----
    # Default threshold below which stock-alert emails are triggered.
    # Individual items can override this via min_stock_level on the Item model.
    low_stock_threshold: Mapped[float] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )
    # Comma-separated list of emails to notify on low/zero stock.
    alert_emails: Mapped[Optional[str]] = mapped_column(
        String(1000), nullable=True
    )
    # Whether to block sales (invoice + POS) when stock reaches zero.
    block_negative_stock: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default="true"
    )

    company: Mapped["Company"] = relationship(back_populates="settings")
