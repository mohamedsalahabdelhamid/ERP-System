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
    PermissionDef("users.view", "View users"),
    PermissionDef("users.manage", "Create/update users"),
    PermissionDef("roles.view", "View roles"),
    PermissionDef("roles.manage", "Create/update roles and their permissions"),
    PermissionDef("permissions.view", "View the permission catalog"),
    # ---- Phase 3 master data ----
    PermissionDef("partners.view", "View partners (customers/suppliers)"),
    PermissionDef("partners.manage", "Create/update/delete partners"),
    PermissionDef("categories.view", "View item categories"),
    PermissionDef("categories.manage", "Create/update/delete item categories"),
    PermissionDef("units.view", "View units of measure"),
    PermissionDef("units.manage", "Create/update/delete units of measure"),
    PermissionDef("items.view", "View items"),
    PermissionDef("items.manage", "Create/update/delete items"),
    PermissionDef("sales.view", "View sales invoices"),
    PermissionDef("sales.manage", "Create/update/delete sales invoices"),
    PermissionDef("purchases.view", "View purchase invoices"),
    PermissionDef("purchases.manage", "Create/update/delete purchase invoices"),
    PermissionDef("warehouses.view", "View warehouses"),
    PermissionDef("warehouses.manage", "Create/update/delete warehouses"),
    PermissionDef("stock.view", "View warehouse stock levels"),
    PermissionDef("movements.view", "View inventory movements"),
    PermissionDef("payments.view", "View payments"),
    PermissionDef("payments.manage", "Create/update/delete payments"),
    PermissionDef("accounts.view", "View accounting accounts"),
    PermissionDef("accounts.manage", "Create/update/delete accounting accounts"),
    PermissionDef("journal_entries.view", "View journal entries"),
    PermissionDef("journal_entries.manage", "Create/update/delete journal entries"),
    # ---- Phase 4 currencies & units ----
    PermissionDef("currencies.view", "View currencies"),
    PermissionDef("currencies.manage", "Create/update/delete currencies"),
    PermissionDef("currency_rates.view", "View currency exchange rates"),
    PermissionDef("currency_rates.manage", "Create/update/delete currency rates"),
    PermissionDef("unit_conversions.view", "View unit conversions"),
    PermissionDef(
        "unit_conversions.manage", "Create/update/delete unit conversions"
    ),
    # ---- Accounting (used by app/modules/accounting/router.py) ----
    PermissionDef("accounting.view", "View accounts and journal entries"),
    PermissionDef("accounting.manage", "Create/update accounts and journal entries"),
    PermissionDef("accounting.reports", "View financial reports"),
    # ---- HR (used by app/modules/hr/router.py) ----
    PermissionDef("hr.view", "View HR data"),
    PermissionDef("hr.manage", "Manage departments, employees, attendance, leave"),
    PermissionDef("hr.payroll", "Run payroll"),
    # ---- Projects (used by app/modules/projects/router.py) ----
    PermissionDef("projects.view", "View projects and their costs"),
    PermissionDef("projects.manage", "Create/update projects and cost lines"),
    # ---- Manufacturing (used by app/modules/manufacturing/router.py) ----
    PermissionDef("manufacturing.view", "View BOMs and work orders"),
    PermissionDef("manufacturing.manage", "Create BOMs and work orders, finish work orders"),
    # ---- POS (Phase 6.3) ----
    PermissionDef("pos.view", "View POS sessions and orders"),
    PermissionDef("pos.manage", "Open/close sessions and create POS orders"),
    # ---- Stock taking & adjustments (Phase 6.3) ----
    PermissionDef("stock_takes.view", "View stock takes and adjustments"),
    PermissionDef("stock_takes.manage", "Create stock takes and post adjustments"),
]

# All known permission codes (used to grant the Admin role everything).
ALL_PERMISSION_CODES: list[str] = [p.code for p in DEFAULT_PERMISSIONS]
