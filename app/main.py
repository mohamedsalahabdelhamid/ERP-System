"""FastAPI application entrypoint.

Phase 0 wires up:
  - configuration (from environment / .env)
  - the versioned API router (currently only /health)
  - a root endpoint and a top-level /health alias for load balancers

Business modules are added from Phase 1 onward via ``app.api.router``.
"""

from fastapi import FastAPI

from app.api.router import api_router
from app.api.health import health as health_endpoint
from app.core.config import settings


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.APP_NAME,
        version="0.1.0",
        debug=settings.DEBUG,
        docs_url="/docs",
        openapi_url="/openapi.json",
    )

    # Versioned API (e.g. /api/v1/health)
    app.include_router(api_router, prefix=settings.API_V1_PREFIX)

    # Convenience top-level /health for Docker/Nginx/uptime checks.
    app.add_api_route("/health", health_endpoint, tags=["health"])

    @app.get("/", tags=["root"], summary="API root")
    def root() -> dict:
        return {
            "app": settings.APP_NAME,
            "version": "0.1.0",
            "docs": "/docs",
            "health": "/health",
        }

    return app


app = create_app()
