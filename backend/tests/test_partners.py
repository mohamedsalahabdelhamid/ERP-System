"""Phase 3 partner CRUD + company-isolation tests."""

PREFIX = "/api/v1"


def _login_and_select(client, data):
    token = client.post(
        f"{PREFIX}/auth/login",
        json={"email": data["email"], "password": data["password"]},
    ).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    sel = client.post(
        f"{PREFIX}/auth/select-company",
        headers=headers,
        json={"company_id": data["company_id"], "branch_id": data["branch_id"]},
    )
    assert sel.status_code == 200
    return headers


def _new_partner(**over):
    body = {"type": "customer", "name": "Acme", "code": "P001"}
    body.update(over)
    return body


def test_partner_crud_flow(client, seeded):
    h = _login_and_select(client, seeded)

    # create
    resp = client.post(f"{PREFIX}/partners", headers=h, json=_new_partner())
    assert resp.status_code == 201
    created = resp.json()
    pid = created["id"]
    assert created["company_id"] == seeded["company_id"]
    assert created["code"] == "P001"

    # list
    lst = client.get(f"{PREFIX}/partners", headers=h)
    assert lst.status_code == 200
    assert [p["id"] for p in lst.json()] == [pid]

    # read
    one = client.get(f"{PREFIX}/partners/{pid}", headers=h)
    assert one.status_code == 200
    assert one.json()["name"] == "Acme"

    # update (partial)
    upd = client.patch(
        f"{PREFIX}/partners/{pid}", headers=h, json={"name": "Acme Corp"}
    )
    assert upd.status_code == 200
    assert upd.json()["name"] == "Acme Corp"
    assert upd.json()["code"] == "P001"  # untouched

    # delete
    assert client.delete(f"{PREFIX}/partners/{pid}", headers=h).status_code == 204
    assert client.get(f"{PREFIX}/partners/{pid}", headers=h).status_code == 404


def test_partner_duplicate_code_rejected(client, seeded):
    h = _login_and_select(client, seeded)
    assert client.post(
        f"{PREFIX}/partners", headers=h, json=_new_partner(code="DUP")
    ).status_code == 201
    dup = client.post(
        f"{PREFIX}/partners", headers=h, json=_new_partner(name="Other", code="DUP")
    )
    assert dup.status_code == 409


def test_partner_requires_permission(client, seeded_no_perms):
    h = _login_and_select(client, seeded_no_perms)
    assert client.get(f"{PREFIX}/partners", headers=h).status_code == 403
    assert client.post(
        f"{PREFIX}/partners", headers=h, json=_new_partner()
    ).status_code == 403


def test_partner_requires_company_selection(client, seeded):
    # Logged in but no company selected -> 409 before permission check.
    token = client.post(
        f"{PREFIX}/auth/login",
        json={"email": seeded["email"], "password": seeded["password"]},
    ).json()["access_token"]
    h = {"Authorization": f"Bearer {token}"}
    assert client.get(f"{PREFIX}/partners", headers=h).status_code == 409


def test_partner_company_isolation(client, seeded, seeded_other):
    # Company A creates a partner.
    ha = _login_and_select(client, seeded)
    pid = client.post(
        f"{PREFIX}/partners", headers=ha, json=_new_partner(code="A1")
    ).json()["id"]

    # Company B must not see it in the list...
    hb = _login_and_select(client, seeded_other)
    assert client.get(f"{PREFIX}/partners", headers=hb).json() == []

    # ...nor read, update, or delete it (all 404 across the company boundary).
    assert client.get(f"{PREFIX}/partners/{pid}", headers=hb).status_code == 404
    assert client.patch(
        f"{PREFIX}/partners/{pid}", headers=hb, json={"name": "hack"}
    ).status_code == 404
    assert client.delete(f"{PREFIX}/partners/{pid}", headers=hb).status_code == 404

    # And company B may reuse the same code (codes are unique per company only).
    assert client.post(
        f"{PREFIX}/partners", headers=hb, json=_new_partner(code="A1")
    ).status_code == 201
