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
    """Return a cached Redis client instance.

    Short socket timeouts keep the fail-open path fast: if Redis is down, a
    command returns an error within 2s instead of blocking on the OS default
    (which can be 20s+ on some systems).
    """
    return redis.Redis.from_url(
        settings.REDIS_URL,
        decode_responses=True,
        socket_connect_timeout=2,
        socket_timeout=2,
    )


def ping_redis() -> bool:
    """Return True if Redis responds to PING."""
    return bool(get_redis().ping())
