"""Phase 0 smoke tests.

Verifies the app boots and the health/root endpoints behave. Dependency checks
(DB, Redis) are monkeypatched so the tests run without live containers, while
still exercising the real endpoint logic.
"""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_root():
    resp = client.get("/")
    assert resp.status_code == 200
    body = resp.json()
    assert body["health"] == "/health"
    assert "version" in body


def test_health_ok(monkeypatch):
    # Force both dependency checks to succeed.
    monkeypatch.setattr("app.api.health.ping_db", lambda: True)
    monkeypatch.setattr("app.api.health.ping_redis", lambda: True)

    resp = client.get("/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert body["dependencies"]["database"]["status"] == "ok"
    assert body["dependencies"]["redis"]["status"] == "ok"


def test_health_reports_dependency_failure(monkeypatch):
    # The endpoint stays 200 (app is alive) but reports the failing dependency.
    def boom():
        raise RuntimeError("connection refused")

    monkeypatch.setattr("app.api.health.ping_db", boom)
    monkeypatch.setattr("app.api.health.ping_redis", lambda: True)

    resp = client.get("/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["dependencies"]["database"]["status"] == "error"
    assert "connection refused" in body["dependencies"]["database"]["detail"]


def test_versioned_health_alias(monkeypatch):
    monkeypatch.setattr("app.api.health.ping_db", lambda: True)
    monkeypatch.setattr("app.api.health.ping_redis", lambda: True)

    resp = client.get("/api/v1/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"
