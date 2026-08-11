"""FastAPI application entrypoint.

Phase 0 wires up:
  - configuration (from environment / .env)
  - the versioned API router (currently only /health)
  - a root endpoint and a top-level /health alias for load balancers

Business modules are added from Phase 1 onward via ``app.api.router``.
"""

from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

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

    # CORS: local dev defaults when APP_ENV=local, otherwise the explicit
    # CORS_ORIGINS list from the environment (comma-separated).
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Versioned API (e.g. /api/v1/health)
    app.include_router(api_router, prefix=settings.API_V1_PREFIX)

    # Convenience top-level /health for Docker/Nginx/uptime checks.
    app.add_api_route("/health", health_endpoint, tags=["health"])

    @app.get("/", tags=["root"], summary="Web UI")
    def root() -> FileResponse:
        static_file = Path(__file__).resolve().parent / "static" / "index.html"
        return FileResponse(static_file)

    @app.get("/api/metadata", tags=["root"], summary="API metadata")
    def metadata() -> dict:
        return {
            "app": settings.APP_NAME,
            "version": "0.1.0",
            "docs": "/docs",
            "health": "/health",
        }

    return app


app = create_app()
