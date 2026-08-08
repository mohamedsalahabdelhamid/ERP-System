"""Root API router.

Aggregates all route modules under the versioned prefix.
"""

from fastapi import APIRouter

from app.api import health
from app.modules.auth.router import router as auth_router
from app.modules.companies.router import router as companies_router

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(auth_router)
api_router.include_router(companies_router)

# Later phases register more module routers here (partners, items, sales, ...).
