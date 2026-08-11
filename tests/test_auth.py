"""Phase 1 auth & company-scoping flow tests."""

PREFIX = "/api/v1"


def _login(client, email, password):
    return client.post(
        f"{PREFIX}/auth/login", json={"email": email, "password": password}
    )


def _auth_header(token):
    return {"Authorization": f"Bearer {token}"}


def test_login_success_and_wrong_password(client, seeded):
    resp = _login(client, seeded["email"], seeded["password"])
    assert resp.status_code == 200
    body = resp.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"]

    bad = _login(client, seeded["email"], "wrong")
    assert bad.status_code == 401


def test_me_requires_auth(client, seeded):
    assert client.get(f"{PREFIX}/auth/me").status_code == 401


def test_me_lists_accessible_companies(client, seeded):
    token = _login(client, seeded["email"], seeded["password"]).json()["access_token"]
    resp = client.get(f"{PREFIX}/auth/me", headers=_auth_header(token))
    assert resp.status_code == 200
    body = resp.json()
    assert body["user"]["email"] == seeded["email"]
    assert body["scope"]["current_company_id"] is None
    codes = [c["code"] for c in body["companies"]]
    assert "TEST" in codes


def test_company_scope_enforced_before_selection(client, seeded):
    token = _login(client, seeded["email"], seeded["password"]).json()["access_token"]
    # No company selected yet -> business scope dependency returns 409.
    resp = client.get(f"{PREFIX}/companies/current", headers=_auth_header(token))
    assert resp.status_code == 409


def test_select_company_then_scope_available(client, seeded):
    token = _login(client, seeded["email"], seeded["password"]).json()["access_token"]

    sel = client.post(
        f"{PREFIX}/auth/select-company",
        headers=_auth_header(token),
        json={"company_id": seeded["company_id"], "branch_id": seeded["branch_id"]},
    )
    assert sel.status_code == 200
    assert sel.json()["current_company_id"] == seeded["company_id"]

    cur = client.get(f"{PREFIX}/companies/current", headers=_auth_header(token))
    assert cur.status_code == 200
    assert cur.json()["id"] == seeded["company_id"]

    me = client.get(f"{PREFIX}/auth/me", headers=_auth_header(token)).json()
    assert me["scope"]["current_company_id"] == seeded["company_id"]
    assert me["scope"]["current_branch_id"] == seeded["branch_id"]


def test_select_company_without_access_forbidden(client, seeded):
    token = _login(client, seeded["email"], seeded["password"]).json()["access_token"]
    resp = client.post(
        f"{PREFIX}/auth/select-company",
        headers=_auth_header(token),
        json={"company_id": 9999},  # a company the user has no role in
    )
    assert resp.status_code == 403


def test_select_branch_from_other_company_forbidden(client, seeded):
    token = _login(client, seeded["email"], seeded["password"]).json()["access_token"]
    resp = client.post(
        f"{PREFIX}/auth/select-company",
        headers=_auth_header(token),
        json={"company_id": seeded["company_id"], "branch_id": 9999},
    )
    assert resp.status_code == 403


def test_logout_revokes_token(client, seeded):
    token = _login(client, seeded["email"], seeded["password"]).json()["access_token"]
    assert client.post(
        f"{PREFIX}/auth/logout", headers=_auth_header(token)
    ).status_code == 204

    # Token is now revoked.
    assert client.get(
        f"{PREFIX}/auth/me", headers=_auth_header(token)
    ).status_code == 401


def test_platform_creates_company_and_owner_creates_branch(client, seeded, superuser):
    # Company creation is exclusive to the platform owner (superuser).
    token = _login(client, superuser["email"], superuser["password"]).json()["access_token"]
    headers = _auth_header(token)

    created = client.post(
        f"{PREFIX}/platform/companies",
        headers=headers,
        json={
            "name": "New Company",
            "code": "NEWC",
            "subdomain": "newco",
            "base_currency": "EGP",
            "modules": ["sales", "purchases", "inventory"],
            "max_users": 5,
            "owner_email": "owner@newco.com",
            "owner_name": "New Owner",
            "owner_password": "Owner@2026X",
        },
    )
    assert created.status_code == 201, created.text
    company_id = created.json()["id"]
    assert created.json()["subdomain"] == "newco"
    assert created.json()["status"] == "active"

    # A regular (non-superuser) user cannot create companies.
    tenant_token = _login(client, seeded["email"], seeded["password"]).json()["access_token"]
    forbidden = client.post(
        f"{PREFIX}/companies", headers=_auth_header(tenant_token), json={"name": "X"}
    )
    assert forbidden.status_code == 405  # endpoint no longer exists for tenants

    # The new owner logs in, selects the company and creates a branch.
    owner_login = _login(client, "owner@newco.com", "Owner@2026X")
    assert owner_login.status_code == 200
    owner_headers = _auth_header(owner_login.json()["access_token"])
    sel = client.post(
        f"{PREFIX}/auth/select-company",
        headers=owner_headers,
        json={"company_id": company_id, "branch_id": None},
    )
    assert sel.status_code == 200

    branch = client.post(
        f"{PREFIX}/companies/{company_id}/branches",
        headers=owner_headers,
        json={"name": "Cairo Branch", "code": "CAI"},
    )
    assert branch.status_code == 201
    assert branch.json()["company_id"] == company_id
