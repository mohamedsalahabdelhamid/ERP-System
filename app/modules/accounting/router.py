from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import (
    get_current_company_id,
    get_db,
    require_module,
    require_permission,
)
from app.modules.accounting.schemas import AccountCreate, AccountRead, JournalEntryCreate, JournalEntryRead
from app.modules.accounting.service import (
    create_account,
    create_journal_entry,
    journal_entry_reference_exists,
    list_accounts,
    list_journal_entries,
)
from app.modules.accounting.reports import get_trial_balance, get_income_statement, get_balance_sheet

router = APIRouter(
    prefix="/accounting",
    tags=["accounting"],
    dependencies=[Depends(require_module("accounting"))],
)


@router.get("/accounts", response_model=list[AccountRead], dependencies=[Depends(require_permission("accounting.view"))])
def list_accounts_endpoint(
    company_id: int = Depends(get_current_company_id),
    db: Session = Depends(get_db),
) -> list[AccountRead]:
    return list_accounts(db, company_id)


@router.post("/accounts", response_model=AccountRead, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_permission("accounting.manage"))])
def create_account_endpoint(
    data: AccountCreate,
    company_id: int = Depends(get_current_company_id),
    db: Session = Depends(get_db),
) -> AccountRead:
    try:
        return create_account(db, company_id, data)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.get("/journal-entries", response_model=list[JournalEntryRead], dependencies=[Depends(require_permission("accounting.view"))])
def list_journal_entries_endpoint(
    company_id: int = Depends(get_current_company_id),
    db: Session = Depends(get_db),
) -> list[JournalEntryRead]:
    return list_journal_entries(db, company_id)


@router.post("/journal-entries", response_model=JournalEntryRead, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_permission("accounting.manage"))])
def create_journal_entry_endpoint(
    data: JournalEntryCreate,
    company_id: int = Depends(get_current_company_id),
    db: Session = Depends(get_db),
) -> JournalEntryRead:
    if data.reference and journal_entry_reference_exists(db, company_id, data.reference):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Journal reference '{data.reference}' already exists in this company.",
        )
    try:
        return create_journal_entry(db, company_id, data)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.get("/reports/trial-balance", dependencies=[Depends(require_permission("accounting.reports"))])
def trial_balance_endpoint(
    company_id: int = Depends(get_current_company_id),
    db: Session = Depends(get_db),
):
    return get_trial_balance(db, company_id)


@router.get("/reports/income-statement", dependencies=[Depends(require_permission("accounting.reports"))])
def income_statement_endpoint(
    company_id: int = Depends(get_current_company_id),
    db: Session = Depends(get_db),
):
    return get_income_statement(db, company_id)


@router.get("/reports/balance-sheet", dependencies=[Depends(require_permission("accounting.reports"))])
def balance_sheet_endpoint(
    company_id: int = Depends(get_current_company_id),
    db: Session = Depends(get_db),
):
    return get_balance_sheet(db, company_id)
