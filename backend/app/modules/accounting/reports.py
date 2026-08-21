from sqlalchemy import select, func
from sqlalchemy.orm import Session
from app.modules.accounting.models import Account, JournalLine, JournalEntry

def get_trial_balance(db: Session, company_id: int):
    stmt = (
        select(
            Account.id,
            Account.code,
            Account.name,
            Account.account_type,
            func.sum(JournalLine.debit).label("total_debit"),
            func.sum(JournalLine.credit).label("total_credit")
        )
        .select_from(Account)
        .outerjoin(JournalLine, Account.id == JournalLine.account_id)
        .outerjoin(JournalEntry, JournalLine.journal_entry_id == JournalEntry.id)
        .where(Account.company_id == company_id, JournalEntry.company_id == company_id)
        .group_by(Account.id)
    )
    results = db.execute(stmt).all()
    
    lines = []
    total_debit = 0.0
    total_credit = 0.0
    
    for row in results:
        debit = float(row.total_debit or 0)
        credit = float(row.total_credit or 0)
        
        balance = debit - credit
        
        if balance > 0:
            final_debit = balance
            final_credit = 0.0
        else:
            final_debit = 0.0
            final_credit = -balance
            
        total_debit += final_debit
        total_credit += final_credit
        
        lines.append({
            "account_id": row.id,
            "account_code": row.code,
            "account_name": row.name,
            "account_type": row.account_type,
            "debit": final_debit,
            "credit": final_credit,
        })
        
    return {
        "lines": lines,
        "total_debit": total_debit,
        "total_credit": total_credit
    }

def get_income_statement(db: Session, company_id: int):
    tb = get_trial_balance(db, company_id)
    
    revenue = 0.0
    cogs = 0.0
    expenses = 0.0
    
    lines = []
    
    for line in tb["lines"]:
        if line["account_type"] == "revenue":
            val = line["credit"] - line["debit"]
            revenue += val
            lines.append(line)
        elif line["account_type"] == "cogs":
            val = line["debit"] - line["credit"]
            cogs += val
            lines.append(line)
        elif line["account_type"] == "expense":
            val = line["debit"] - line["credit"]
            expenses += val
            lines.append(line)
            
    gross_profit = revenue - cogs
    net_income = gross_profit - expenses
    
    return {
        "revenue": revenue,
        "cogs": cogs,
        "gross_profit": gross_profit,
        "expenses": expenses,
        "net_income": net_income,
        "details": lines
    }

def get_balance_sheet(db: Session, company_id: int):
    tb = get_trial_balance(db, company_id)
    
    assets = 0.0
    liabilities = 0.0
    equity = 0.0
    
    assets_lines = []
    liabilities_lines = []
    equity_lines = []
    
    for line in tb["lines"]:
        if line["account_type"] in ["asset", "receivable", "inventory", "bank", "cash"]:
            val = line["debit"] - line["credit"]
            assets += val
            assets_lines.append(line)
        elif line["account_type"] in ["liability", "payable"]:
            val = line["credit"] - line["debit"]
            liabilities += val
            liabilities_lines.append(line)
        elif line["account_type"] == "equity":
            val = line["credit"] - line["debit"]
            equity += val
            equity_lines.append(line)
            
    # Add net income to equity
    is_report = get_income_statement(db, company_id)
    net_income = is_report["net_income"]
    equity += net_income
    
    return {
        "assets": assets,
        "liabilities": liabilities,
        "equity": equity,
        "net_income": net_income,
        "assets_details": assets_lines,
        "liabilities_details": liabilities_lines,
        "equity_details": equity_lines
    }
