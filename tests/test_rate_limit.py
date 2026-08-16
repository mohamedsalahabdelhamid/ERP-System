"""Rate limiting for /auth/login (unit + endpoint-level tests)."""

import time

import pytest
from fastapi.testclient import TestClient

import app.core.rate_limit as rate_limit
from app.core.config import settings
from app.core.rate_limit import get_client_ip, login_allowed, record_login_failure
from app.main import app

PREFIX = "/api/v1"


class FakeRedis:
    """Minimal in-memory Redis stub (incr/expire/ttl/set/delete)."""

    def __init__(self):
        self._values = {}

    def incr(self, key):
        value, exp = self._values.get(key, (0, None))
        self._values[key] = (value + 1, exp)
        return value + 1

    def expire(self, key, seconds):
        if key not in self._values:
            return False
        value, _ = self._values[key]
        self._values[key] = (value, time.time() + seconds)
        return True

    def ttl(self, key):
        if key not in self._values:
            return -2
        _, exp = self._values[key]
        if exp is None:
            return -1
        return max(int(exp - time.time()), 0)

    def set(self, key, value, ex=None):
        exp = time.time() + ex if ex else None
        self._values[key] = (value, exp)
        return True

    def delete(self, *keys):
        removed = 0
        for key in keys:
            if key in self._values:
                del self._values[key]
                removed += 1
        return removed


@pytest.fixture(autouse=True)
def _fake_redis(monkeypatch):
    fake = FakeRedis()
    monkeypatch.setattr(rate_limit, "get_redis", lambda: fake)
    return fake


def _login(client, email, password):
    return client.post(
        f"{PREFIX}/auth/login", json={"email": email, "password": password}
    )


def test_get_client_ip_prefers_forwarded_header():
    class _Req:
        headers = {"x-forwarded-for": "203.0.113.9, 10.0.0.1"}
        client = None

    assert get_client_ip(_Req()) == "203.0.113.9"


def test_get_client_ip_falls_back_to_x_real_ip():
    class _Req:
        headers = {"x-real-ip": "198.51.100.7"}
        client = None

    assert get_client_ip(_Req()) == "198.51.100.7"


def test_lockout_after_max_failed_attempts(client, seeded, _fake_redis):
    for _ in range(settings.LOGIN_MAX_ATTEMPTS):
        assert _login(client, seeded["email"], "wrong").status_code == 401

    # Correct password now also rejected while locked out.
    locked = _login(client, seeded["email"], seeded["password"])
    assert locked.status_code == 429
    assert int(locked.headers["Retry-After"]) > 0


def test_successful_login_resets_failure_counters(client, seeded, _fake_redis):
    for _ in range(settings.LOGIN_MAX_ATTEMPTS - 1):
        assert _login(client, seeded["email"], "wrong").status_code == 401

    # Below the threshold, the correct password still works and resets counters.
    assert _login(client, seeded["email"], seeded["password"]).status_code == 200

    for _ in range(settings.LOGIN_MAX_ATTEMPTS):
        assert _login(client, seeded["email"], "wrong").status_code == 401

    assert _login(client, seeded["email"], seeded["password"]).status_code == 429


def test_ip_lockout_across_many_accounts(client, seeded, _fake_redis, monkeypatch):
    monkeypatch.setattr(settings, "LOGIN_MAX_IP_ATTEMPTS", 3)

    for i in range(3):
        assert _login(client, f"spray{i}@test.com", "wrong").status_code == 401

    # Any account from the same IP is now blocked.
    assert _login(client, seeded["email"], seeded["password"]).status_code == 429


def test_login_allowed_unit(_fake_redis):
    class _Req:
        headers = {}
        client = type("C", (), {"host": "192.0.2.1"})()

    assert login_allowed(_Req(), "a@b.com") == (True, 0)
    for _ in range(settings.LOGIN_MAX_ATTEMPTS):
        record_login_failure(_Req(), "a@b.com")
    allowed, retry_after = login_allowed(_Req(), "a@b.com")
    assert allowed is False
    assert retry_after > 0
