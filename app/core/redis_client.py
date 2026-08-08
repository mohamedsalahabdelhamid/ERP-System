"""Redis client helper.

Redis is optional per the spec (cache / background jobs). We expose a lazily
created client plus a ``ping_redis`` helper used by /health. The rest of the app
does not depend on Redis being available.
"""

from functools import lru_cache

import redis

from app.core.config import settings


@lru_cache
def get_redis() -> "redis.Redis":
    """Return a cached Redis client instance."""
    return redis.Redis.from_url(settings.REDIS_URL, decode_responses=True)


def ping_redis() -> bool:
    """Return True if Redis responds to PING."""
    return bool(get_redis().ping())
