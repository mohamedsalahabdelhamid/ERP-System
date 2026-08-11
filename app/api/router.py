"""Root API router.

Aggregates all route modules under the versioned prefix.
"""

from fastapi import APIRouter

from app.api import health
from app.modules.auth.router import router as auth_router
from app.modules.companies.router import router as companies_router
from app.modules.currencies.router import currencies_router, rates_router
from app.modules.inventory.router import movements_router, stock_router, stock_takes_router, warehouses_router
from app.modules.items.router import categories_router, conversions_router, items_router, units_router
from app.modules.partners.router import router as partners_router
from app.modules.payments.router import router as payments_router
from app.modules.pos.router import router as pos_router
from app.modules.purchases.router import router as purchases_router
from app.modules.sales.router import router as sales_router
from app.modules.accounting.router import router as accounting_router
from app.modules.hr.router import router as hr_router
from app.modules.projects.router import router as projects_router
from app.modules.reports.router import router as reports_router
from app.modules.manufacturing.router import router as manufacturing_router
from app.modules.platform.router import router as platform_router

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(auth_router)
api_router.include_router(companies_router)
api_router.include_router(platform_router)

# ---- Phase 3: Master Data ----
api_router.include_router(partners_router)
api_router.include_router(categories_router)
api_router.include_router(units_router)
api_router.include_router(items_router)
api_router.include_router(warehouses_router)
api_router.include_router(stock_router)
api_router.include_router(movements_router)
api_router.include_router(stock_takes_router)

# ---- Phase 5: Sales & Purchases ----
api_router.include_router(sales_router)
api_router.include_router(purchases_router)
api_router.include_router(payments_router)
api_router.include_router(accounting_router)

# ---- Phase 4: Currencies & Units ----
api_router.include_router(currencies_router)
api_router.include_router(rates_router)
api_router.include_router(conversions_router)

# ---- Phase 7: Manufacturing ----
api_router.include_router(manufacturing_router)

# ---- Phase 8: HR ----
api_router.include_router(hr_router)

# ---- Projects ----
api_router.include_router(projects_router)

# ---- POS ----
api_router.include_router(pos_router)

# ---- Reports & Analytics ----
api_router.include_router(reports_router)
