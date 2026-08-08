"""Root API router.

Aggregates all route modules. As phases add modules (companies, auth, ...),
their routers are included here under the versioned prefix.
"""

from fastapi import APIRouter

from app.api import health

api_router = APIRouter()
api_router.include_router(health.router)

# Phase 1+ will register module routers here, e.g.:
#   from app.modules.companies.router import router as companies_router
#   api_router.include_router(companies_router, prefix="/companies")
