"""Shared pytest fixtures.

Tests run against an in-memory SQLite database (created from the ORM metadata),
with the app's ``get_db`` dependency overridden to use it. This lets the full
auth flow be tested without Postgres or Docker.
"""

import pytest
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
from app.modules.users.models import User


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


@pytest.fixture()
def seeded(db_session):
    """Create a company + branch + admin user with a role. Returns key ids."""
    company = Company(
        name="Test Co",
        code="TEST",
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
            enabled_modules=["sales"],
            cost_method="weighted_average",
        )
    )

    role = Role(company_id=company.id, name="Admin")
    db_session.add(role)
    db_session.flush()

    user = User(
        email="admin@test.com",
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
    db_session.commit()

    return {
        "company_id": company.id,
        "branch_id": branch.id,
        "user_id": user.id,
        "email": "admin@test.com",
        "password": "secret123",
    }
