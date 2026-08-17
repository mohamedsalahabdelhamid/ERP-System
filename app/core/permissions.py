"""Default permission catalog (Phase 2).

A single source of truth for the permission codes the system knows about. These
codes are synced into the ``permissions`` table by ``app.modules.rbac.seed`` and
referenced by ``require_permission(...)`` on endpoints.

Convention: ``<module>.<action>`` (e.g. "companies.view", "users.manage").
Later phases (sales, inventory, ...) will extend this list with their own codes.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class PermissionDef:
    code: str
    description: str


# ---- Phase 1/2 core permissions ----
DEFAULT_PERMISSIONS: list[PermissionDef] = [
    PermissionDef("companies.view", "View companies and branches"),
    PermissionDef("companies.manage", "Create/update companies and branches"),
    PermissionDef("companies.delete_data", "Delete all of a company's operational data (danger zone)"),
    PermissionDef("users.view", "View users"),
    PermissionDef("users.manage", "Create/update users"),
    PermissionDef("roles.view", "View roles"),
    PermissionDef("roles.manage", "Create/update roles and their permissions"),
    PermissionDef("permissions.view", "View the permission catalog"),
    # ---- Phase 3 master data ----
    PermissionDef("partners.view", "View partners (customers/suppliers)"),
    PermissionDef("partners.manage", "Create/update partners"),
    PermissionDef("partners.delete", "Delete partners"),
    PermissionDef("categories.view", "View item categories"),
    PermissionDef("categories.manage", "Create/update item categories"),
    PermissionDef("categories.delete", "Delete item categories"),
    PermissionDef("units.view", "View units of measure"),
    PermissionDef("units.manage", "Create/update units of measure"),
    PermissionDef("units.delete", "Delete units of measure"),
    PermissionDef("items.view", "View items"),
    PermissionDef("items.manage", "Create/update items"),
    PermissionDef("items.delete", "Delete items"),
    PermissionDef("sales.view", "View sales invoices"),
    PermissionDef("sales.manage", "Create/update sales invoices"),
    PermissionDef("sales.delete", "Delete sales invoices"),
    PermissionDef("purchases.view", "View purchase invoices"),
    PermissionDef("purchases.manage", "Create/update purchase invoices"),
    PermissionDef("purchases.delete", "Delete purchase invoices"),
    PermissionDef("warehouses.view", "View warehouses"),
    PermissionDef("warehouses.manage", "Create/update warehouses"),
    PermissionDef("warehouses.delete", "Delete warehouses"),
    PermissionDef("stock.view", "View warehouse stock levels"),
    PermissionDef("movements.view", "View inventory movements"),
    PermissionDef("payments.view", "View payments"),
    PermissionDef("payments.manage", "Create/update payments"),
    PermissionDef("payments.delete", "Delete payments"),
    PermissionDef("accounts.view", "View accounting accounts"),
    PermissionDef("accounts.manage", "Create/update accounting accounts"),
    PermissionDef("accounts.delete", "Delete accounting accounts"),
    PermissionDef("journal_entries.view", "View journal entries"),
    PermissionDef("journal_entries.manage", "Create/update journal entries"),
    PermissionDef("journal_entries.delete", "Delete journal entries"),
    # ---- Phase 4 currencies & units ----
    PermissionDef("currencies.view", "View currencies"),
    PermissionDef("currencies.manage", "Create/update currencies"),
    PermissionDef("currencies.delete", "Delete currencies"),
    PermissionDef("currency_rates.view", "View currency exchange rates"),
    PermissionDef("currency_rates.manage", "Create/update currency rates"),
    PermissionDef("currency_rates.delete", "Delete currency rates"),
    PermissionDef("unit_conversions.view", "View unit conversions"),
    PermissionDef(
        "unit_conversions.manage", "Create/update unit conversions"
    ),
    PermissionDef("unit_conversions.delete", "Delete unit conversions"),
    # ---- Accounting (used by app/modules/accounting/router.py) ----
    PermissionDef("accounting.view", "View accounts and journal entries"),
    PermissionDef("accounting.manage", "Create/update accounts and journal entries"),
    PermissionDef("accounting.reports", "View financial reports"),
    # ---- HR (used by app/modules/hr/router.py) ----
    PermissionDef("hr.view", "View HR data"),
    PermissionDef("hr.manage", "Manage departments, employees, attendance, leave"),
    PermissionDef("hr.delete", "Delete HR records"),
    PermissionDef("hr.payroll", "Run payroll"),
    # ---- Projects (used by app/modules/projects/router.py) ----
    PermissionDef("projects.view", "View projects and their costs"),
    PermissionDef("projects.manage", "Create/update projects and cost lines"),
    PermissionDef("projects.delete", "Delete projects and cost lines"),
    # ---- Manufacturing (used by app/modules/manufacturing/router.py) ----
    PermissionDef("manufacturing.view", "View BOMs and work orders"),
    PermissionDef("manufacturing.manage", "Create BOMs and work orders, finish work orders"),
    PermissionDef("manufacturing.delete", "Delete BOMs and work orders"),
    # ---- POS (Phase 6.3) ----
    PermissionDef("pos.view", "View POS sessions and orders"),
    PermissionDef("pos.manage", "Open/close sessions and create POS orders"),
    PermissionDef("pos.delete", "Delete POS sessions and orders"),
    # ---- Stock taking & adjustments (Phase 6.3) ----
    PermissionDef("stock_takes.view", "View stock takes and adjustments"),
    PermissionDef("stock_takes.manage", "Create stock takes and post adjustments"),
    PermissionDef("stock_takes.delete", "Delete stock takes and adjustments"),
]

# All known permission codes (used to grant the Admin role everything).
ALL_PERMISSION_CODES: list[str] = [p.code for p in DEFAULT_PERMISSIONS]
