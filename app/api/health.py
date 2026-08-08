"""Health check endpoint (Phase 0).

Reports overall service liveness plus the reachability of the database and
Redis. Returns HTTP 200 when the app itself is up; each dependency's status is
reported individually so a Redis outage (optional dependency) does not mark the
whole service unhealthy.
"""

from fastapi import APIRouter

from app.core.config import settings
from app.core.redis_client import ping_redis
from app.db.session import ping_db

router = APIRouter(tags=["health"])


def _check(fn) -> dict:
    """Run a dependency check, capturing success/failure without raising."""
    try:
        fn()
        return {"status": "ok"}
    except Exception as exc:  # noqa: BLE001 - report, never crash /health
        return {"status": "error", "detail": str(exc)}


@router.get("/health", summary="Service health check")
def health() -> dict:
    db = _check(ping_db)
    cache = _check(ping_redis)

    return {
        "status": "ok",
        "app": settings.APP_NAME,
        "environment": settings.APP_ENV,
        "dependencies": {
            "database": db,
            "redis": cache,
        },
    }
