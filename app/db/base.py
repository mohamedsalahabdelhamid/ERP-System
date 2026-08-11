"""Metadata registry for Alembic and ``create_all``.

Every ORM model must be imported here so that ``Base.metadata`` sees it.
"""

from app.db.base_class import Base  # noqa: F401

# ---- Phase 1: Multi-Company Core & Auth ----
from app.modules.companies.models import Branch, Company, CompanySettings  # noqa: F401
from app.modules.users.models import User  # noqa: F401
from app.modules.rbac.models import Permission, Role, RolePermission, UserRole  # noqa: F401
from app.modules.auth.models import AuthSession  # noqa: F401

# ---- Accounting ----
from app.modules.accounting.models import Account, JournalEntry, JournalLine  # noqa: F401

# ---- Phase 3: Master Data ----
from app.modules.partners.models import Partner  # noqa: F401
from app.modules.items.models import Item, ItemCategory, Unit, UnitConversion  # noqa: F401
from app.modules.inventory.models import InventoryMovement, StockTake, StockTakeLine, Warehouse, WarehouseStock  # noqa: F401

# ---- Phase 4: Currencies ----
from app.modules.currencies.models import Currency, CurrencyRate  # noqa: F401

# ---- Phase 5: Sales & Purchases ----
from app.modules.sales.models import SalesInvoice, SalesInvoiceLine  # noqa: F401
from app.modules.purchases.models import PurchaseInvoice, PurchaseInvoiceLine  # noqa: F401

# ---- Phase 7: Manufacturing ----
from app.modules.manufacturing.models import BOM, BOMLine, WorkOrder, WorkOrderConsumption, WorkOrderLabor, WorkOrderOverhead, WorkOrderOutput  # noqa: F401

# ---- Phase 8: HR ----
from app.modules.hr.models import Department, Employee, AttendanceRecord, PayrollRun, PayrollLine, LeaveRequest  # noqa: F401

# ---- Projects ----
from app.modules.projects.models import Project, ProjectCostLine  # noqa: F401

# ---- POS ----
from app.modules.pos.models import PosSession, PosOrder, PosOrderLine  # noqa: F401
