"""Shared pytest fixtures.

Tests run against an in-memory SQLite database (created from the ORM metadata),
with the app's ``get_db`` dependency overridden to use it. This lets the full
auth flow be tested without Postgres or Docker.
"""

import pytest
import redis
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.security import hash_password
from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.modules.companies.models import Branch, Company, CompanySettings
from app.modules.rbac.models import Role, UserRole
from app.modules.rbac.seed import grant_all_to_role, sync_permissions
from app.modules.users.models import User


class _OfflineRedis:
    """Stands in for the Redis client: every command fails immediately.

    The app treats Redis as optional and fails open on redis.RedisError, so a
    stub that raises instantly keeps tests fast and deterministic without a
    live Redis.
    """

    def __getattr__(self, name):
        def _raise(*args, **kwargs):
            raise redis.exceptions.ConnectionError("Redis is offline in tests")

        return _raise


@pytest.fixture(autouse=True)
def _redis_offline(monkeypatch):
    """Make every login skip real Redis (fast fail-open) in the test suite."""
    stub = lambda: _OfflineRedis()
    # rate_limit binds `get_redis` at import time, so patch both references.
    monkeypatch.setattr("app.core.redis_client.get_redis", stub)
    monkeypatch.setattr("app.core.rate_limit.get_redis", stub)


@pytest.fixture()
def db_session():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    TestingSessionLocal = sessionmaker(
        bind=engine, autoflush=False, autocommit=False, expire_on_commit=False
    )
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(engine)


@pytest.fixture()
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def _seed_company_admin(db_session, code, email, grant_perms):
    """Create a company + branch + admin user with a role. Returns key ids.

    When ``grant_perms`` is True the Admin role is granted every permission,
    mirroring ``scripts/seed.py`` (the demo admin has full access).
    """
    company = Company(
        name=f"{code} Co",
        code=code,
        base_currency="EGP",
        activity_type="trading",
        is_active=True,
    )
    db_session.add(company)
    db_session.flush()

    branch = Branch(
        company_id=company.id, name="Main", code="MAIN", is_active=True
    )
    db_session.add(branch)

    db_session.add(
        CompanySettings(
            company_id=company.id,
            enabled_modules=[
                "sales",
                "purchases",
                "inventory",
                "pos",
                "manufacturing",
                "projects",
                "hr",
                "accounting",
            ],
            cost_method="weighted_average",
        )
    )

    role = Role(company_id=company.id, name="Admin")
    db_session.add(role)
    db_session.flush()

    user = User(
        email=email,
        password_hash=hash_password("secret123"),
        full_name="Admin",
        is_active=True,
    )
    db_session.add(user)
    db_session.flush()

    db_session.add(
        UserRole(
            user_id=user.id,
            company_id=company.id,
            branch_id=branch.id,
            role_id=role.id,
        )
    )

    if grant_perms:
        sync_permissions(db_session)
        db_session.flush()
        grant_all_to_role(db_session, role)

    db_session.commit()

    return {
        "company_id": company.id,
        "branch_id": branch.id,
        "user_id": user.id,
        "role_id": role.id,
        "email": email,
        "password": "secret123",
    }


@pytest.fixture()
def seeded(db_session):
    """Company + admin user whose Admin role has all permissions."""
    return _seed_company_admin(
        db_session, code="TEST", email="admin@test.com", grant_perms=True
    )


@pytest.fixture()
def seeded_no_perms(db_session):
    """Company + admin user whose role has NO permissions (403 enforcement)."""
    return _seed_company_admin(
        db_session, code="NOPERM", email="noperm@test.com", grant_perms=False
    )


@pytest.fixture()
def seeded_other(db_session):
    """A second, independent company + fully-permissioned admin.

    Used to prove company isolation: this user must never see or touch the
    first company's data even though they hold every permission.
    """
    return _seed_company_admin(
        db_session, code="OTHER", email="admin@other.com", grant_perms=True
    )


@pytest.fixture()
def superuser(db_session):
    """A platform superuser (no company required for platform endpoints)."""
    user = User(
        email="platform@example.com",
        password_hash=hash_password("Super@2026X"),
        full_name="Platform Owner",
        is_active=True,
        is_superuser=True,
    )
    db_session.add(user)
    db_session.commit()
    return {"email": user.email, "password": "Super@2026X", "user_id": user.id}
