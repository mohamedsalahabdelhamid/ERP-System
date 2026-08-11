"""Seed a demo company with full bootstrap data.

Idempotent: running it again will not create duplicates. Intended for local
development / first-run bootstrap AND for a fresh production server (run once
after ``alembic upgrade head``).

Creates:
  - Demo company + main branch + company settings (all modules enabled).
  - Admin role (all permissions) + admin user.
  - Chart of accounts (asset/liability/equity/income/expense + FX accounts).
  - Units, item categories, items (with barcodes and stock levels).
  - Warehouse + initial stock.
  - Partners (customers / suppliers).
  - Departments + employees.

Usage (inside the web container):
    python -m scripts.seed
    python -m scripts.seed --reset   # drop existing demo company, reseed fresh
"""

import argparse
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy import select

from app.core.security import hash_password
from app.db.session import SessionLocal
from app.modules.accounting.models import Account
from app.modules.companies.models import Branch, Company, CompanySettings
from app.modules.hr.models import Department, Employee
from app.modules.inventory.models import Warehouse, WarehouseStock
from app.modules.items.models import Item, ItemCategory, Unit
from app.modules.partners.models import Partner
from app.modules.rbac.models import Role, UserRole
from app.modules.rbac.seed import grant_all_to_role, sync_permissions
from app.modules.users.models import User

DEMO_COMPANY_CODE = "DEMO"
ADMIN_EMAIL = "admin@example.com"
ADMIN_PASSWORD = "admin123"  # noqa: S105 - demo bootstrap credential only

# (code, name, account_type) - a minimal, sound chart of accounts.
DEFAULT_ACCOUNTS = [
    ("1000", "Cash on Hand", "asset"),
    ("1100", "Accounts Receivable", "asset"),
    ("1200", "Inventory", "asset"),
    ("1300", "Fixed Assets", "asset"),
    ("2100", "Accounts Payable", "liability"),
    ("2200", "Sales Tax Payable", "liability"),
    ("2300", "Salaries Payable", "liability"),
    ("3000", "Owner's Equity", "equity"),
    ("4000", "Sales Revenue", "income"),
    ("5000", "Cost of Goods Sold", "expense"),
    ("6000", "Operating Expenses", "expense"),
    ("6100", "FX Gain", "income"),
    ("6200", "FX Loss", "expense"),
]

DEFAULT_UNITS = [
    ("Pieces", "PCS", "pcs", "count"),
    ("Kilograms", "KG", "kg", "weight"),
    ("Liters", "LTR", "L", "volume"),
]

DEFAULT_CATEGORIES = [
    ("Pharmacy", "PHARM"),
    ("Clothing", "CLOTH"),
    ("Hardware", "HARD"),
]

# (name, code, category_code, unit_code, barcode, sale, purchase, min_stock)
DEFAULT_ITEMS = [
    ("Paracetamol 500mg", "ITM-001", "PHARM", "PCS", "6221001861125", 5.50, 2.00, 20),
    ("Amoxicillin 250mg", "ITM-002", "PHARM", "PCS", "6221001861132", 12.00, 5.00, 15),
    ("T-Shirt (White, L)", "ITM-003", "CLOTH", "PCS", "6256660510012", 15.00, 7.50, 10),
    ("Jeans (Blue, 32)", "ITM-004", "CLOTH", "PCS", "6256660510029", 40.00, 22.00, 8),
    ("Hammer 500g", "ITM-005", "HARD", "PCS", "6221047311507", 18.50, 9.00, 5),
    ("Water Pump 1HP", "ITM-006", "HARD", "PCS", "6221047311514", 850.00, 620.00, 2),
]

# (name, code, type, tax_number, opening_balance)
DEFAULT_PARTNERS = [
    ("Walk-in Customer", "CUS-001", "customer", None, 0.0),
    ("Al-Nour Pharmacy", "CUS-002", "customer", "612-345-678", 0.0),
    ("General Supplier", "SUP-001", "supplier", None, 0.0),
    ("Nile Trading Co", "SUP-002", "supplier", "612-999-888", 0.0),
]

DEFAULT_DEPARTMENTS = ["Administration", "Sales", "Warehouse", "IT"]

# (employee_number, name, position, department, basic_salary)
DEFAULT_EMPLOYEES = [
    ("EMP-001", "Ahmed Hassan", "Store Manager", "Administration", 12000.0),
    ("EMP-002", "Sara Mohamed", "Sales Representative", "Sales", 8000.0),
    ("EMP-003", "Omar Khaled", "Warehouse Keeper", "Warehouse", 6000.0),
]


def _get_or_create(db, model, filters: dict, **defaults):
    obj = db.scalar(select(model).where(*[getattr(model, k) == v for k, v in filters.items()]))
    if obj is None:
        obj = model(**filters, **defaults)
        db.add(obj)
        db.flush()
    return obj


def seed(reset: bool = False) -> None:
    db = SessionLocal()
    try:
        # --- (Optional) wipe the demo company for a clean reseed ---
        existing = db.scalar(select(Company).where(Company.code == DEMO_COMPANY_CODE))
        if reset and existing is not None:
            db.delete(existing)
            db.commit()
            existing = None
            print("Reset: previous demo company removed.")

        # --- Company ---
        company = existing
        if company is None:
            company = Company(
                name="Demo Company",
                code=DEMO_COMPANY_CODE,
                base_currency="EGP",
                activity_type="trading",
                is_active=True,
            )
            db.add(company)
            db.flush()

        # --- Branch ---
        branch = _get_or_create(
            db, Branch, {"company_id": company.id, "code": "MAIN"},
            name="Main Branch", is_active=True,
        )

        # --- Company settings (1:1, all modules on) ---
        settings = db.get(CompanySettings, company.id)
        if settings is None:
            settings = CompanySettings(
                company_id=company.id,
                enabled_modules=[
                    "accounting", "sales", "purchases", "inventory",
                    "hr", "manufacturing", "projects", "pos",
                ],
                cost_method="weighted_average",
                has_manufacturing=True,
                has_projects=True,
                has_pos=True,
                pos_style="retail",
            )
            db.add(settings)

        # --- Admin role + user + grant ---
        role = _get_or_create(db, Role, {"company_id": company.id, "name": "Admin"})
        user = _get_or_create(
            db, User, {"email": ADMIN_EMAIL},
            password_hash=hash_password(ADMIN_PASSWORD),
            full_name="System Administrator",
            is_active=True,
        )
        link = db.scalar(
            select(UserRole).where(
                UserRole.user_id == user.id,
                UserRole.company_id == company.id,
                UserRole.role_id == role.id,
            )
        )
        if link is None:
            db.add(
                UserRole(
                    user_id=user.id,
                    company_id=company.id,
                    branch_id=branch.id,
                    role_id=role.id,
                )
            )

        sync_permissions(db)
        db.flush()
        grant_all_to_role(db, role)

        # --- Chart of accounts ---
        for code, name, atype in DEFAULT_ACCOUNTS:
            _get_or_create(
                db, Account, {"company_id": company.id, "code": code},
                name=name, account_type=atype, is_active=True,
            )

        # --- Units ---
        units = {}
        for name, code, symbol, utype in DEFAULT_UNITS:
            units[code] = _get_or_create(
                db, Unit, {"company_id": company.id, "code": code},
                name=name, symbol=symbol, unit_type=utype, is_active=True,
            )

        # --- Categories ---
        categories = {}
        for name, code in DEFAULT_CATEGORIES:
            categories[code] = _get_or_create(
                db, ItemCategory, {"company_id": company.id, "code": code},
                name=name, is_active=True,
            )

        # --- Warehouse + stock ---
        wh = _get_or_create(
            db, Warehouse, {"company_id": company.id, "code": "MAIN"},
            branch_id=branch.id, name="Main Warehouse", is_active=True,
        )

        # --- Items + opening stock ---
        for name, code, cat_code, unit_code, barcode, sale, purchase, min_stock in DEFAULT_ITEMS:
            item = _get_or_create(
                db, Item, {"company_id": company.id, "code": code},
                name=name,
                barcode=barcode,
                item_category_id=categories[cat_code].id,
                base_unit_id=units[unit_code].id,
                sale_unit_id=units[unit_code].id,
                purchase_unit_id=units[unit_code].id,
                type="stock",
                default_sale_price=sale,
                default_purchase_price=purchase,
                min_stock_level=min_stock,
                is_active=True,
            )
            stock = db.scalar(
                select(WarehouseStock).where(
                    WarehouseStock.warehouse_id == wh.id,
                    WarehouseStock.item_id == item.id,
                )
            )
            if stock is None:
                db.add(
                    WarehouseStock(
                        company_id=company.id,
                        warehouse_id=wh.id,
                        item_id=item.id,
                        quantity=100.0,
                        average_cost=purchase,
                    )
                )

        # --- Partners ---
        for name, code, ptype, tax, balance in DEFAULT_PARTNERS:
            _get_or_create(
                db, Partner, {"company_id": company.id, "code": code},
                type=ptype, name=name, tax_number=tax,
                opening_balance=balance, is_active=True,
            )

        # --- HR departments + employees ---
        depts = {}
        for dname in DEFAULT_DEPARTMENTS:
            depts[dname] = _get_or_create(
                db, Department, {"company_id": company.id, "name": dname},
                is_active=True,
            )
        for emp_no, ename, position, dept, salary in DEFAULT_EMPLOYEES:
            _get_or_create(
                db, Employee,
                {"company_id": company.id, "employee_number": emp_no},
                name=ename,
                position=position,
                department_id=depts[dept].id,
                hire_date="2024-01-01",
                basic_salary=salary,
                is_active=True,
            )

        db.commit()
        print(f"Seed complete. Login with {ADMIN_EMAIL} / {ADMIN_PASSWORD} "
              f"(company code: {DEMO_COMPANY_CODE}).")
        print("Modules enabled: accounting, sales, purchases, inventory, "
              "hr, manufacturing, projects, pos.")
    finally:
        db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed the ERP demo data.")
    parser.add_argument("--reset", action="store_true",
                        help="Remove the existing demo company before seeding.")
    args = parser.parse_args()
    seed(reset=args.reset)
