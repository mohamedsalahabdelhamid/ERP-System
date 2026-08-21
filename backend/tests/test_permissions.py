"""Phase 2 permission-enforcement tests.

Verifies ``require_permission`` on the /companies routes:
  - a user whose Admin role has no permissions gets 403 after selecting a
    company (``seeded_no_perms``),
  - the fully-permissioned admin (``seeded``, mirrors ``scripts/seed.py``) gets
    200 on the same routes.

Also covers the seeding helpers' idempotency.
"""

from sqlalchemy import select

from app.modules.rbac.models import Permission, Role, RolePermission
from app.modules.rbac.seed import grant_all_to_role, sync_permissions

PREFIX = "/api/v1"


def _login(client, email, password):
    return client.post(
        f"{PREFIX}/auth/login", json={"email": email, "password": password}
    )


def _auth_header(token):
    return {"Authorization": f"Bearer {token}"}


def _login_and_select(client, data):
    token = _login(client, data["email"], data["password"]).json()["access_token"]
    sel = client.post(
        f"{PREFIX}/auth/select-company",
        headers=_auth_header(token),
        json={"company_id": data["company_id"], "branch_id": data["branch_id"]},
    )
    assert sel.status_code == 200
    return token


def test_companies_view_forbidden_without_permission(client, seeded_no_perms):
    token = _login_and_select(client, seeded_no_perms)
    resp = client.get(f"{PREFIX}/companies", headers=_auth_header(token))
    assert resp.status_code == 403
    assert "companies.view" in resp.json()["detail"]

    cur = client.get(f"{PREFIX}/companies/current", headers=_auth_header(token))
    assert cur.status_code == 403


def test_companies_view_allowed_with_permission(client, seeded):
    token = _login_and_select(client, seeded)

    resp = client.get(f"{PREFIX}/companies", headers=_auth_header(token))
    assert resp.status_code == 200
    codes = [c["code"] for c in resp.json()]
    assert "TEST" in codes

    cur = client.get(f"{PREFIX}/companies/current", headers=_auth_header(token))
    assert cur.status_code == 200


def test_sync_permissions_is_idempotent(db_session):
    first = sync_permissions(db_session)
    db_session.flush()
    second = sync_permissions(db_session)
    db_session.flush()
    assert first.keys() == second.keys()
    assert db_session.scalar(
        select(Permission).where(Permission.code == "users.view")
    ) is not None


def test_grant_all_to_role_is_idempotent(db_session, seeded_no_perms):
    sync_permissions(db_session)
    db_session.flush()
    role = db_session.get(Role, seeded_no_perms["role_id"])
    grant_all_to_role(db_session, role)
    grant_all_to_role(db_session, role)
    db_session.flush()
    links = db_session.scalars(
        select(RolePermission).where(RolePermission.role_id == role.id)
    ).all()
    perms = db_session.scalars(select(Permission)).all()
    assert len(links) == len(perms)
