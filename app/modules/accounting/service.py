from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.accounting.models import Account, JournalEntry, JournalLine
from app.modules.accounting.schemas import AccountCreate, JournalEntryCreate, JournalEntryRead

# Amounts are money (Numeric(18,4)); allow tiny float rounding when balancing.
_BALANCE_TOLERANCE = 0.01


def list_accounts(db: Session, company_id: int) -> list[Account]:
    return list(db.scalars(select(Account).where(Account.company_id == company_id)).all())


def create_account(db: Session, company_id: int, data: AccountCreate) -> Account:
    account = Account(company_id=company_id, code=data.code, name=data.name, account_type=data.account_type)
    db.add(account)
    db.commit()
    db.refresh(account)
    return account


def get_or_create_default_account(db: Session, company_id: int, account_type: str, code: str, name: str) -> Account:
    """Find a default account by (company, code), creating it if missing.

    Uses ``flush`` instead of ``commit`` so it never commits the surrounding
    transaction prematurely: composite operations (invoice confirmation,
    payroll, work-order completion) must persist atomically.
    """
    account = db.scalar(select(Account).where(Account.company_id == company_id, Account.code == code))
    if account is None:
        account = Account(company_id=company_id, code=code, name=name, account_type=account_type)
        db.add(account)
        db.flush()
        db.refresh(account)
    return account


def list_journal_entries(db: Session, company_id: int) -> list[JournalEntry]:
    return list(db.scalars(select(JournalEntry).where(JournalEntry.company_id == company_id)).all())


def _validate_journal_lines(db: Session, company_id: int, lines) -> None:
    """A journal entry must be non-empty, non-negative, balanced, and scoped."""
    if not lines:
        raise ValueError("Journal entry must have at least one line.")
    total_debit = 0.0
    total_credit = 0.0
    for line_data in lines:
        debit = float(line_data.debit or 0)
        credit = float(line_data.credit or 0)
        if debit < 0 or credit < 0:
            raise ValueError("Journal line amounts cannot be negative.")
        account = db.get(Account, line_data.account_id)
        if account is None or account.company_id != company_id:
            raise ValueError(
                f"account_id {line_data.account_id} not found in this company."
            )
        total_debit += debit
        total_credit += credit
    if abs(total_debit - total_credit) > _BALANCE_TOLERANCE:
        raise ValueError(
            f"Journal entry is unbalanced: debits {total_debit:.2f} != "
            f"credits {total_credit:.2f}."
        )


def create_journal_entry(
    db: Session, company_id: int, data: JournalEntryCreate, commit: bool = True
) -> JournalEntryRead:
    """Create a journal entry.

    ``commit=True`` (default) persists immediately for standalone calls.
    Composite operations (invoice confirmation, payroll, work-order completion,
    payment posting) pass ``commit=False`` and commit once at the end so all
    writes (stock, movements, accounting, flags) are atomic.
    """
    _validate_journal_lines(db, company_id, data.lines)
    entry = JournalEntry(company_id=company_id, reference=data.reference, entry_date=data.entry_date, notes=data.notes)
    db.add(entry)
    db.flush()

    lines = []
    for line_data in data.lines:
        line = JournalLine(
            journal_entry_id=entry.id,
            account_id=line_data.account_id,
            description=line_data.description,
            debit=line_data.debit,
            credit=line_data.credit
        )
        db.add(line)
        lines.append(line_data)

    db.flush()
    if commit:
        db.commit()
    db.refresh(entry)
    return JournalEntryRead(id=entry.id, reference=entry.reference, entry_date=entry.entry_date, notes=entry.notes, lines=lines)
