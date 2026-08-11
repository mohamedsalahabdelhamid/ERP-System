from typing import Optional

from pydantic import BaseModel, Field


class AccountCreate(BaseModel):
    code: str = Field(..., min_length=1)
    name: str = Field(..., min_length=1)
    account_type: str = "asset"


class AccountRead(AccountCreate):
    id: int


class JournalEntryCreate(BaseModel):
    reference: str = Field(..., min_length=1)
    entry_date: Optional[str] = None
    notes: Optional[str] = None
    lines: list["JournalLineCreate"] = []


class JournalLineCreate(BaseModel):
    account_id: int
    description: Optional[str] = None
    debit: float = 0.0
    credit: float = 0.0


class JournalEntryRead(JournalEntryCreate):
    id: int
    lines: list[JournalLineCreate] = []
