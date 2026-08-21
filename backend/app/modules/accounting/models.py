from typing import Optional

from sqlalchemy import ForeignKey, Integer, Numeric, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base_class import Base
from app.db.mixins import TimestampMixin


class Account(TimestampMixin, Base):
    __tablename__ = "accounts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    company_id: Mapped[int] = mapped_column(
        ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True
    )
    code: Mapped[str] = mapped_column(String(50), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    account_type: Mapped[str] = mapped_column(String(50), nullable=False, default="asset")
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)


class JournalEntry(TimestampMixin, Base):
    __tablename__ = "journal_entries"
    __table_args__ = (
        UniqueConstraint(
            "company_id", "reference", name="uq_journal_entries_company_reference"
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    company_id: Mapped[int] = mapped_column(
        ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True
    )
    entry_date: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    reference: Mapped[str] = mapped_column(String(100), nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)


class JournalLine(TimestampMixin, Base):
    __tablename__ = "journal_lines"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    journal_entry_id: Mapped[int] = mapped_column(
        ForeignKey("journal_entries.id", ondelete="CASCADE"), nullable=False, index=True
    )
    account_id: Mapped[int] = mapped_column(
        ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False, index=True
    )
    description: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    debit: Mapped[float] = mapped_column(Numeric(18, 4), nullable=False, default=0)
    credit: Mapped[float] = mapped_column(Numeric(18, 4), nullable=False, default=0)
