from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.accounting.models import Account, JournalEntry, JournalLine
from app.modules.accounting.schemas import AccountCreate, JournalEntryCreate, JournalEntryRead


def list_accounts(db: Session, company_id: int) -> list[Account]:
    return list(db.scalars(select(Account).where(Account.company_id == company_id)).all())


def create_account(db: Session, company_id: int, data: AccountCreate) -> Account:
    account = Account(company_id=company_id, code=data.code, name=data.name, account_type=data.account_type)
    db.add(account)
    db.commit()
    db.refresh(account)
    return account


def get_or_create_default_account(db: Session, company_id: int, account_type: str, code: str, name: str) -> Account:
    account = db.scalar(select(Account).where(Account.company_id == company_id, Account.code == code))
    if account is None:
        account = Account(company_id=company_id, code=code, name=name, account_type=account_type)
        db.add(account)
        db.commit()
        db.refresh(account)
    return account


def list_journal_entries(db: Session, company_id: int) -> list[JournalEntry]:
    return list(db.scalars(select(JournalEntry).where(JournalEntry.company_id == company_id)).all())


def create_journal_entry(db: Session, company_id: int, data: JournalEntryCreate) -> JournalEntryRead:
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

    db.commit()
    db.refresh(entry)
    return JournalEntryRead(id=entry.id, reference=entry.reference, entry_date=entry.entry_date, notes=entry.notes, lines=lines)
