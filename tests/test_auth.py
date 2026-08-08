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
