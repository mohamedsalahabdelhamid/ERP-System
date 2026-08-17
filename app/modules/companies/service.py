"""Company access helpers.

Resolves which companies/branches a user may access, based on ``user_roles``.
Used during login and company selection to enforce that a user can only pick a
company they have been granted a role in.
"""

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.db.numbering import generate_code
from app.modules.companies.models import Branch, Company
from app.modules.rbac.models import UserRole


def get_user_companies(db: Session, user_id: int) -> list[Company]:
    """Return the active companies the user has any role in."""
    stmt = (
        select(Company)
        .join(UserRole, UserRole.company_id == Company.id)
        .where(UserRole.user_id == user_id, Company.is_active.is_(True))
        .distinct()
        .order_by(Company.name)
    )
    return list(db.scalars(stmt).all())


def user_can_access_company(db: Session, user_id: int, company_id: int) -> bool:
    """True if the user has at least one role in the given company."""
    stmt = select(UserRole.id).where(
        UserRole.user_id == user_id, UserRole.company_id == company_id
    ).limit(1)
    return db.scalar(stmt) is not None


def branch_belongs_to_company(db: Session, branch_id: int, company_id: int) -> bool:
    """True if the branch exists and belongs to the given company."""
    stmt = select(Branch.id).where(
        Branch.id == branch_id, Branch.company_id == company_id
    ).limit(1)
    return db.scalar(stmt) is not None


def branch_code_exists(db: Session, company_id: int, code: str) -> bool:
    stmt = select(Branch.id).where(
        Branch.company_id == company_id, Branch.code == code
    ).limit(1)
    return db.scalar(stmt) is not None


def create_branch(db: Session, company_id: int, data) -> Branch:
    values = data.model_dump()
    if not values.get("code"):
        values["code"] = generate_code(
            db, company_id, "branch", "BR", Branch, "code"
        )
    branch = Branch(company_id=company_id, **values)
    db.add(branch)
    db.commit()
    db.refresh(branch)
    return branch


# ---------------------------------------------------------------------------
# Danger Zone: clear all operational data for a company
# ---------------------------------------------------------------------------

# Tables that have a company_id column — deleted directly by company_id.
_COMPANY_SCOPED_TABLES = [
    # POS (must come before sales_invoices due to SET NULL FK from pos_orders)
    "pos_sessions",
    # Sales & purchases
    "sales_invoices",
    "purchase_invoices",
    # Payments
    "payments",
    # Manufacturing
    "work_orders",
    "boms",
    # HR
    "payroll_runs",
    "leave_requests",
    "attendance_records",
    # Projects
    "projects",
    # Accounting
    "journal_entries",
    # Inventory
    "stock_takes",
    "inventory_movements",
]

# Child tables that do NOT have company_id — cleaned via parent subqueries.
# (table, parent_table, parent_fk_col) — parent must have company_id.
_CHILD_TABLES = [
    ("pos_order_lines", "pos_orders", "order_id"),
    ("pos_orders", "pos_sessions", "session_id"),
    ("sales_invoice_lines", "sales_invoices", "invoice_id"),
    ("purchase_invoice_lines", "purchase_invoices", "invoice_id"),
    ("work_order_output", "work_orders", "work_order_id"),
    ("work_order_overheads", "work_orders", "work_order_id"),
    ("work_order_labor", "work_orders", "work_order_id"),
    ("work_order_consumption", "work_orders", "work_order_id"),
    ("bom_lines", "boms", "bom_id"),
    ("payroll_lines", "payroll_runs", "payroll_run_id"),
    ("journal_lines", "journal_entries", "journal_entry_id"),
    ("stock_take_lines", "stock_takes", "stock_take_id"),
    ("project_cost_lines", "projects", "project_id"),
]


def _enable_sqlite_fk(db: Session) -> None:
    if db.bind.dialect.name == "sqlite":
        db.execute(text("PRAGMA foreign_keys=ON"))


def clear_company_data(db: Session, company_id: int) -> None:
    """Delete all operational data for a company.

    Keeps: company, branches, settings, users, roles, chart of accounts,
    master data (items, partners, employees, departments, warehouses,
    currencies, conversions, warehouse_stock reset to zero).
    """
    _enable_sqlite_fk(db)

    # 1. Delete child tables (no company_id column) via parent subqueries.
    for child_table, parent_table, fk_col in _CHILD_TABLES:
        parent_has_cid = parent_table in _COMPANY_SCOPED_TABLES
        if parent_has_cid:
            db.execute(text(
                f"DELETE FROM {child_table} WHERE {fk_col} IN "
                f"(SELECT id FROM {parent_table} WHERE company_id = :cid)"
            ), {"cid": company_id})
        else:
            # parent itself is a child table — recurse via nested SELECT.
            for grandparent, gp_fk in _GRANDPARENT.get(parent_table, []):
                db.execute(text(
                    f"DELETE FROM {child_table} WHERE {fk_col} IN "
                    f"(SELECT id FROM {parent_table} WHERE {gp_fk} IN "
                    f"(SELECT id FROM {grandparent} WHERE company_id = :cid))"
                ), {"cid": company_id})

    # 2. Delete company-scoped tables.
    for table in _COMPANY_SCOPED_TABLES:
        db.execute(text(f"DELETE FROM {table} WHERE company_id = :cid"), {"cid": company_id})

    # 3. Reset warehouse_stock (keep structure, zero out quantities/costs).
    db.execute(text(
        "UPDATE warehouse_stock SET quantity = 0, average_cost = 0 "
        "WHERE company_id = :cid"
    ), {"cid": company_id})

    db.flush()


# Grandparent map for tables whose parent is also a child table (no company_id).
_GRANDPARENT: dict[str, list[tuple[str, str]]] = {
    "pos_order_lines": [("pos_sessions", "session_id")],
}
