"""Licensed module registry.

Modules are the sellable features of the platform. Each tenant (company) has an
``enabled_modules`` list in ``company_settings``. The platform owner toggles
these per company (the "subscription"). ``require_module(...)`` enforces at the
API level: if a module is not licensed, its endpoints return 403.

Values here are the single source of truth for what can be sold/toggled.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class ModuleDef:
    key: str
    label: str
    description: str


AVAILABLE_MODULES: list[ModuleDef] = [
    ModuleDef("sales", "Sales", "Sales invoices and confirmations"),
    ModuleDef("purchases", "Purchases", "Purchase invoices and confirmations"),
    ModuleDef("inventory", "Inventory", "Warehouses, stock, movements and stock takes"),
    ModuleDef("pos", "Point of Sale", "POS sessions, orders and cash handling"),
    ModuleDef("manufacturing", "Manufacturing", "BOMs and work orders"),
    ModuleDef("projects", "Projects", "Projects and cost tracking"),
    ModuleDef("hr", "Human Resources", "Employees, attendance, leave and payroll"),
    ModuleDef("accounting", "Accounting", "Chart of accounts, journal entries and reports"),
]

MODULE_KEYS: list[str] = [m.key for m in AVAILABLE_MODULES]
MODULE_LABELS: dict[str, str] = {m.key: m.label for m in AVAILABLE_MODULES}


def is_valid_module(key: str) -> bool:
    return key in MODULE_KEYS
