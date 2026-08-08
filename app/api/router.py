"""Root API router.

Aggregates all route modules under the versioned prefix.
"""

from fastapi import APIRouter

from app.api import health
from app.modules.auth.router import router as auth_router
from app.modules.companies.router import router as companies_router
from app.modules.inventory.router import (
    movements_router,
    stock_router,
    warehouses_router,
)
from app.modules.items.router import (
    categories_router,
    items_router,
    units_router,
)
from app.modules.partners.router import router as partners_router

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(auth_router)
api_router.include_router(companies_router)

# ---- Phase 3: Master Data ----
api_router.include_router(partners_router)
api_router.include_router(categories_router)
api_router.include_router(units_router)
api_router.include_router(items_router)
api_router.include_router(warehouses_router)
api_router.include_router(stock_router)
api_router.include_router(movements_router)

# Later phases register more module routers here (sales, purchases, ...).
