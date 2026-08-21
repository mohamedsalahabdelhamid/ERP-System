"""Tests for Phase 5: delete-permission enforcement, RBAC management, and danger zone.

Verifies:
  - DELETE endpoints now require ``<module>.delete`` (not ``<module>.manage``)
  - RBAC management API (roles CRUD, permissions, company users)
  - Danger zone: clear company data (company-scoped) and delete tenant (platform)
  - seed.py --reset requires --confirm-destroy
"""

import subprocess
import sys

import pytest
from sqlalchemy import select

from app.core.security import hash_password
from app.modules.rbac.models import Permission, Role, RolePermission, UserRole
from app.modules.rbac.seed import grant_all_to_role, sync_permissions
from app.modules.companies.models import Company, Branch, CompanySettings
from app.modules.users.models import User

PREFIX = "/api/v1"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _seed_company(db_session, code, email, grant_perms, role_name="Admin"):
    company = Company(name=f"{code} Co", code=code, base_currency="EGP",
                      activity_type="trading", is_active=True)
    db_session.add(company)
    db_session.flush()
    branch = Branch(company_id=company.id, name="Main", code="MAIN", is_active=True)
    db_session.add(branch)
    db_session.add(CompanySettings(
        company_id=company.id,
        enabled_modules=["sales", "purchases", "inventory", "accounting", "hr", "projects",
                         "manufacturing", "pos", "currencies"],
        cost_method="weighted_average",
    ))
    role = Role(company_id=company.id, name=role_name)
    db_session.add(role)
    db_session.flush()
    user = User(email=email, password_hash=hash_password("secret123"),
                full_name="Test User", is_active=True)
    db_session.add(user)
    db_session.flush()
    db_session.add(UserRole(user_id=user.id, company_id=company.id,
                            branch_id=branch.id, role_id=role.id))
    if grant_perms:
        sync_permissions(db_session)
        db_session.flush()
        grant_all_to_role(db_session, role)
    db_session.commit()
    return {"company_id": company.id, "branch_id": branch.id, "user_id": user.id,
            "role_id": role.id, "email": email, "password": "secret123"}


@pytest.fixture()
def seeded(db_session):
    return _seed_company(db_session, "TEST", "admin@test.com", grant_perms=True)


@pytest.fixture()
def seeded_no_perms(db_session):
    return _seed_company(db_session, "NOPERM", "noperm@test.com", grant_perms=False)


@pytest.fixture()
def seeded_manage_only(db_session):
    """Company where the admin role has only .manage but NOT .delete."""
    data = _seed_company(db_session, "MGMT", "mgmt@test.com", grant_perms=True)
    role = db_session.get(Role, data["role_id"])
    db_session.flush()
    # Revoke all *.delete permissions
    delete_perms = db_session.scalars(
        select(Permission.id).where(Permission.code.like("%.delete"))
    ).all()
    for pid in delete_perms:
        rp = db_session.scalar(
            select(RolePermission).where(
                RolePermission.role_id == role.id,
                RolePermission.permission_id == pid,
            )
        )
        if rp:
            db_session.delete(rp)
    db_session.commit()
    return data


@pytest.fixture()
def superuser(db_session):
    user = User(email="su@test.com", password_hash=hash_password("Super@2026X"),
                full_name="Super Admin", is_active=True, is_superuser=True)
    db_session.add(user)
    db_session.commit()
    return {"email": user.email, "password": "Super@2026X", "user_id": user.id}


# ---------------------------------------------------------------------------
# 1. DELETE endpoint permission enforcement
# ---------------------------------------------------------------------------

class TestDeletePermissionEnforcement:
    """Users with manage but not delete get 403 on DELETE endpoints."""

    def test_delete_partner_requires_delete_perm(self, client, seeded_manage_only):
        token = _login_and_select(client, seeded_manage_only)
        headers = _auth_header(token)
        # Create a partner first (manage allowed)
        p = client.post(f"{PREFIX}/partners", headers=headers,
                        json={"name": "Test", "type": "customer"})
        assert p.status_code == 201
        pid = p.json()["id"]
        # Delete should be 403 (no delete permission)
        resp = client.delete(f"{PREFIX}/partners/{pid}", headers=headers)
        assert resp.status_code == 403
        assert "partners.delete" in resp.json()["detail"]

    def test_delete_partner_allowed_with_delete_perm(self, client, seeded):
        token = _login_and_select(client, seeded)
        headers = _auth_header(token)
        p = client.post(f"{PREFIX}/partners", headers=headers,
                        json={"name": "DelMe", "type": "customer"})
        assert p.status_code == 201
        resp = client.delete(f"{PREFIX}/partners/{p.json()['id']}", headers=headers)
        assert resp.status_code == 204

    def test_delete_category_requires_delete_perm(self, client, seeded_manage_only):
        token = _login_and_select(client, seeded_manage_only)
        headers = _auth_header(token)
        c = client.post(f"{PREFIX}/item-categories", headers=headers,
                        json={"name": "TestCat", "code": "TC1"})
        assert c.status_code == 201
        resp = client.delete(f"{PREFIX}/item-categories/{c.json()['id']}", headers=headers)
        assert resp.status_code == 403
        assert "categories.delete" in resp.json()["detail"]

    def test_manage_only_can_still_create_and_update(self, client, seeded_manage_only):
        token = _login_and_select(client, seeded_manage_only)
        headers = _auth_header(token)
        p = client.post(f"{PREFIX}/partners", headers=headers,
                        json={"name": "KeepMe", "type": "supplier"})
        assert p.status_code == 201
        updated = client.patch(f"{PREFIX}/partners/{p.json()['id']}", headers=headers,
                               json={"name": "Updated"})
        assert updated.status_code == 200

    def test_no_perms_gets_403_on_delete(self, client, seeded_no_perms):
        token = _login_and_select(client, seeded_no_perms)
        headers = _auth_header(token)
        resp = client.delete(f"{PREFIX}/partners/1", headers=headers)
        assert resp.status_code == 403


# ---------------------------------------------------------------------------
# 2. auth/me returns permissions
# ---------------------------------------------------------------------------

class TestAuthMePermissions:
    def test_me_includes_permissions(self, client, seeded):
        token = _login_and_select(client, seeded)
        resp = client.get(f"{PREFIX}/auth/me", headers=_auth_header(token))
        assert resp.status_code == 200
        data = resp.json()
        assert "permissions" in data
        assert isinstance(data["permissions"], list)
        assert "partners.view" in data["permissions"]
        assert "partners.delete" in data["permissions"]

    def test_me_permissions_empty_for_no_perms(self, client, seeded_no_perms):
        token = _login_and_select(client, seeded_no_perms)
        resp = client.get(f"{PREFIX}/auth/me", headers=_auth_header(token))
        assert resp.status_code == 200
        assert resp.json()["permissions"] == []


# ---------------------------------------------------------------------------
# 3. RBAC management API
# ---------------------------------------------------------------------------

class TestRBACManagement:
    def test_list_permissions(self, client, seeded):
        token = _login_and_select(client, seeded)
        resp = client.get(f"{PREFIX}/permissions", headers=_auth_header(token))
        assert resp.status_code == 200
        codes = [p["code"] for p in resp.json()]
        assert "partners.view" in codes
        assert "partners.delete" in codes
        assert "companies.delete_data" in codes

    def test_create_role(self, client, seeded):
        token = _login_and_select(client, seeded)
        resp = client.post(f"{PREFIX}/roles", headers=_auth_header(token),
                           json={"name": "Cashier", "permissions": ["pos.view", "pos.manage"]})
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == "Cashier"
        assert "pos.view" in data["permissions"]
        assert "pos.manage" in data["permissions"]

    def test_cannot_create_admin_role(self, client, seeded):
        token = _login_and_select(client, seeded)
        resp = client.post(f"{PREFIX}/roles", headers=_auth_header(token),
                           json={"name": "Admin", "permissions": []})
        assert resp.status_code == 400

    def test_list_roles(self, client, seeded):
        token = _login_and_select(client, seeded)
        resp = client.get(f"{PREFIX}/roles", headers=_auth_header(token))
        assert resp.status_code == 200
        names = [r["name"] for r in resp.json()]
        assert "Admin" in names

    def test_update_role_permissions(self, client, seeded):
        token = _login_and_select(client, seeded)
        headers = _auth_header(token)
        r = client.post(f"{PREFIX}/roles", headers=headers,
                        json={"name": "Sales", "permissions": ["sales.view"]})
        rid = r.json()["id"]
        resp = client.patch(f"{PREFIX}/roles/{rid}/permissions", headers=headers,
                            json={"permissions": ["sales.view", "sales.manage"]})
        assert resp.status_code == 200
        assert "sales.manage" in resp.json()["permissions"]

    def test_delete_role(self, client, seeded):
        token = _login_and_select(client, seeded)
        headers = _auth_header(token)
        r = client.post(f"{PREFIX}/roles", headers=headers,
                        json={"name": "Temp", "permissions": []})
        rid = r.json()["id"]
        resp = client.delete(f"{PREFIX}/roles/{rid}", headers=headers)
        assert resp.status_code == 204

    def test_cannot_delete_admin_role(self, client, seeded):
        token = _login_and_select(client, seeded)
        # Find Admin role id
        roles = client.get(f"{PREFIX}/roles", headers=_auth_header(token)).json()
        admin_role = next(r for r in roles if r["name"] == "Admin")
        resp = client.delete(f"{PREFIX}/roles/{admin_role['id']}", headers=_auth_header(token))
        assert resp.status_code == 400
        assert "Admin" in resp.json()["detail"]

    def test_cannot_delete_role_with_users(self, client, seeded):
        token = _login_and_select(client, seeded)
        headers = _auth_header(token)
        r = client.post(f"{PREFIX}/roles", headers=headers,
                        json={"name": "Occupied", "permissions": []})
        rid = r.json()["id"]
        # Assign the seeded user to this role so it has users
        resp = client.patch(f"{PREFIX}/company-users/{seeded['user_id']}/roles", headers=headers,
                            json={"role_names": ["Admin", "Occupied"]})
        assert resp.status_code == 200
        resp = client.delete(f"{PREFIX}/roles/{rid}", headers=headers)
        assert resp.status_code == 400
        assert "users" in resp.json()["detail"]

    def test_company_users_crud(self, client, seeded):
        token = _login_and_select(client, seeded)
        headers = _auth_header(token)
        # Create a role to assign
        client.post(f"{PREFIX}/roles", headers=headers,
                    json={"name": "Employee", "permissions": ["partners.view"]})
        # Create user
        resp = client.post(f"{PREFIX}/company-users", headers=headers,
                           json={"email": "new@test.com", "full_name": "New User",
                                 "password": "strong123!", "role_names": ["Employee"]})
        assert resp.status_code == 201, resp.json()
        uid = resp.json()["id"]
        # List
        users = client.get(f"{PREFIX}/company-users", headers=headers).json()
        assert any(u["id"] == uid for u in users)
        # Update roles
        resp = client.patch(f"{PREFIX}/company-users/{uid}/roles", headers=headers,
                            json={"role_names": ["Admin"]})
        assert resp.status_code == 200
        assert "Admin" in resp.json()["roles"]
        # Toggle active
        resp = client.patch(f"{PREFIX}/company-users/{uid}/status", headers=headers,
                            json={"is_active": False})
        assert resp.status_code == 200
        assert resp.json()["is_active"] is False

    def test_no_perms_cannot_manage_roles(self, client, seeded_no_perms):
        token = _login_and_select(client, seeded_no_perms)
        resp = client.get(f"{PREFIX}/roles", headers=_auth_header(token))
        assert resp.status_code == 403


# ---------------------------------------------------------------------------
# 4. Danger Zone — clear company data
# ---------------------------------------------------------------------------

class TestClearCompanyData:
    def _create_partner_and_partner_count(self, client, headers):
        p1 = client.post(f"{PREFIX}/partners", headers=headers,
                         json={"name": "P1", "type": "customer"})
        p2 = client.post(f"{PREFIX}/partners", headers=headers,
                         json={"name": "P2", "type": "supplier"})
        return p1.status_code == 201 and p2.status_code == 201

    def test_clear_data_wrong_confirm(self, client, seeded):
        token = _login_and_select(client, seeded)
        resp = client.post(f"{PREFIX}/companies/current/danger/clear-data",
                           headers=_auth_header(token),
                           json={"confirm": "WRONG"})
        assert resp.status_code == 400

    def test_clear_data_correct_confirm(self, client, seeded):
        token = _login_and_select(client, seeded)
        headers = _auth_header(token)
        # Create some data
        self._create_partner_and_partner_count(client, headers)
        # Clear with correct code
        resp = client.post(f"{PREFIX}/companies/current/danger/clear-data",
                           headers=headers, json={"confirm": "TEST"})
        assert resp.status_code == 200
        # Partners should still exist (master data)
        partners = client.get(f"{PREFIX}/partners", headers=headers)
        assert partners.status_code == 200

    def test_no_perms_cannot_clear_data(self, client, seeded_no_perms):
        token = _login_and_select(client, seeded_no_perms)
        resp = client.post(f"{PREFIX}/companies/current/danger/clear-data",
                           headers=_auth_header(token),
                           json={"confirm": "NOPERM"})
        assert resp.status_code == 403


# ---------------------------------------------------------------------------
# 5. Platform — delete tenant
# ---------------------------------------------------------------------------

class TestPlatformDeleteTenant:
    def test_delete_tenant_wrong_code(self, client, superuser, db_session):
        company = Company(name="Del Co", code="DEL", base_currency="EGP",
                          activity_type="trading", is_active=True)
        db_session.add(company)
        db_session.commit()
        token = _login(client, superuser["email"], superuser["password"]).json()["access_token"]
        resp = client.request("DELETE", f"{PREFIX}/platform/companies/{company.id}",
                              headers=_auth_header(token),
                              json={"confirm_code": "WRONG"})
        assert resp.status_code == 400

    def test_delete_tenant_correct_code(self, client, superuser, db_session):
        company = Company(name="Del Co", code="DEL", base_currency="EGP",
                          activity_type="trading", is_active=True)
        db_session.add(company)
        db_session.commit()
        cid = company.id
        token = _login(client, superuser["email"], superuser["password"]).json()["access_token"]
        resp = client.request("DELETE", f"{PREFIX}/platform/companies/{cid}",
                              headers=_auth_header(token),
                              json={"confirm_code": "DEL"})
        assert resp.status_code == 204
        assert db_session.get(Company, cid) is None

    def test_non_superuser_cannot_delete(self, client, seeded):
        token = _login_and_select(client, seeded)
        resp = client.request("DELETE", f"{PREFIX}/platform/companies/999",
                              headers=_auth_header(token),
                              json={"confirm_code": "X"})
        assert resp.status_code == 403


# ---------------------------------------------------------------------------
# 6. seed.py --reset requires --confirm-destroy
# ---------------------------------------------------------------------------

class TestSeedResetGuard:
    def test_reset_without_confirm_fails(self):
        result = subprocess.run(
            [sys.executable, "-m", "scripts.seed", "--reset"],
            capture_output=True, text=True, timeout=15,
        )
        assert result.returncode != 0
        assert "--confirm-destroy" in result.stderr or "--confirm-destroy" in result.stdout
