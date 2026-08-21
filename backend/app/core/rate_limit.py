"""Login rate limiting (Redis-backed fixed-window counters).

Keys are per (client IP + email) and per (client IP), so both a single-account
brute force and a distributed password-spray across accounts from one source
are throttled. A failed login increments the counters; once the threshold is
reached a lockout key is set and all further attempts return 429 until it
expires.

Redis is optional in this codebase (compose always runs one). If Redis is
unreachable we fail OPEN and log a warning: a cache outage must never become
a total login outage for the whole tenant portal. Use a real deployment where
Redis is part of the compose stack (as in docker-compose.yml).
"""

import logging

import redis

from app.core.config import settings
from app.core.redis_client import get_redis

logger = logging.getLogger(__name__)

_LOGIN_ATTEMPTS_KEY = "erp:login:attempts:{ip}:{email}"
_LOGIN_IP_ATTEMPTS_KEY = "erp:login:attempts:ip:{ip}"
_LOGIN_LOCK_KEY = "erp:login:locked:{ip}:{email}"
_LOGIN_IP_LOCK_KEY = "erp:login:locked:ip:{ip}"


def get_client_ip(request) -> str:
    """Best-effort real client IP, honoring the nginx-set forwarding headers."""
    xff = request.headers.get("x-forwarded-for")
    if xff:
        first = xff.split(",")[0].strip()
        if first:
            return first
    x_real = request.headers.get("x-real-ip")
    if x_real:
        return x_real
    if request.client is not None:
        return request.client.host
    return "unknown"


def login_allowed(request, email: str) -> tuple[bool, int]:
    """Return (allowed, retry_after_seconds). retry_after is 0 when allowed."""
    ip = get_client_ip(request)
    lock_key = _LOGIN_LOCK_KEY.format(ip=ip, email=email.lower())
    ip_lock_key = _LOGIN_IP_LOCK_KEY.format(ip=ip)
    try:
        r = get_redis()
        for key in (lock_key, ip_lock_key):
            ttl = r.ttl(key)
            if ttl and ttl > 0:
                return False, int(ttl)
    except redis.RedisError:
        logger.warning("Redis unreachable; login rate limiting disabled", exc_info=True)
    return True, 0


def record_login_failure(request, email: str) -> None:
    """Increment the failure counters and set a lockout when thresholds are hit."""
    ip = get_client_ip(request)
    try:
        r = get_redis()
    except redis.RedisError:
        logger.warning("Redis unreachable; login failure not recorded", exc_info=True)
        return

    try:
        attempts_key = _LOGIN_ATTEMPTS_KEY.format(ip=ip, email=email.lower())
        attempts = r.incr(attempts_key)
        if attempts == 1:
            r.expire(attempts_key, settings.LOGIN_WINDOW_SECONDS)
        if attempts >= settings.LOGIN_MAX_ATTEMPTS:
            r.set(
                _LOGIN_LOCK_KEY.format(ip=ip, email=email.lower()),
                "1",
                ex=settings.LOGIN_LOCKOUT_SECONDS,
            )

        ip_attempts_key = _LOGIN_IP_ATTEMPTS_KEY.format(ip=ip)
        ip_attempts = r.incr(ip_attempts_key)
        if ip_attempts == 1:
            r.expire(ip_attempts_key, settings.LOGIN_WINDOW_SECONDS)
        if ip_attempts >= settings.LOGIN_MAX_IP_ATTEMPTS:
            r.set(
                _LOGIN_IP_LOCK_KEY.format(ip=ip),
                "1",
                ex=settings.LOGIN_LOCKOUT_SECONDS,
            )
    except redis.RedisError:
        logger.warning("Redis error while recording login failure", exc_info=True)


def record_login_success(request, email: str) -> None:
    """Clear the counters for this identity and source after a valid login."""
    ip = get_client_ip(request)
    try:
        r = get_redis()
    except redis.RedisError:
        return

    try:
        r.delete(
            _LOGIN_ATTEMPTS_KEY.format(ip=ip, email=email.lower()),
            _LOGIN_LOCK_KEY.format(ip=ip, email=email.lower()),
            _LOGIN_IP_ATTEMPTS_KEY.format(ip=ip),
            _LOGIN_IP_LOCK_KEY.format(ip=ip),
        )
    except redis.RedisError:
        logger.warning("Redis error while clearing login counters", exc_info=True)
