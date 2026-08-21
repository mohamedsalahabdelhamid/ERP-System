"""Phase 4 currency tests: currencies + currency_rates (CRUD, rules, isolation)."""

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


# --------------------------------------------------------------- currencies
def test_currency_crud_flow(client, seeded):
    h = _login_and_select(client, seeded)

    resp = client.post(
        f"{PREFIX}/currencies", headers=h, json={"code": "USD", "name": "US Dollar"}
    )
    assert resp.status_code == 201
    cid = resp.json()["id"]
    assert resp.json()["company_id"] == seeded["company_id"]

    lst = client.get(f"{PREFIX}/currencies", headers=h)
    assert [c["id"] for c in lst.json()] == [cid]

    upd = client.patch(
        f"{PREFIX}/currencies/{cid}", headers=h, json={"name": "Dollar"}
    )
    assert upd.status_code == 200
    assert upd.json()["name"] == "Dollar"
    assert upd.json()["code"] == "USD"

    assert client.delete(f"{PREFIX}/currencies/{cid}", headers=h).status_code == 204
    assert client.get(f"{PREFIX}/currencies/{cid}", headers=h).status_code == 404


def test_currency_duplicate_code_rejected(client, seeded):
    h = _login_and_select(client, seeded)
    assert client.post(
        f"{PREFIX}/currencies", headers=h, json={"code": "EUR", "name": "Euro"}
    ).status_code == 201
    assert client.post(
        f"{PREFIX}/currencies", headers=h, json={"code": "EUR", "name": "Euro 2"}
    ).status_code == 409


def test_currency_requires_permission(client, seeded_no_perms):
    h = _login_and_select(client, seeded_no_perms)
    assert client.get(f"{PREFIX}/currencies", headers=h).status_code == 403
    assert client.post(
        f"{PREFIX}/currencies", headers=h, json={"code": "X", "name": "Y"}
    ).status_code == 403


def test_currency_requires_company_selection(client, seeded):
    token = client.post(
        f"{PREFIX}/auth/login",
        json={"email": seeded["email"], "password": seeded["password"]},
    ).json()["access_token"]
    h = {"Authorization": f"Bearer {token}"}
    assert client.get(f"{PREFIX}/currencies", headers=h).status_code == 409


def test_currency_company_isolation(client, seeded, seeded_other):
    ha = _login_and_select(client, seeded)
    cid = client.post(
        f"{PREFIX}/currencies", headers=ha, json={"code": "GBP", "name": "Pound"}
    ).json()["id"]

    hb = _login_and_select(client, seeded_other)
    assert client.get(f"{PREFIX}/currencies", headers=hb).json() == []
    assert client.get(f"{PREFIX}/currencies/{cid}", headers=hb).status_code == 404
    assert client.patch(
        f"{PREFIX}/currencies/{cid}", headers=hb, json={"name": "hack"}
    ).status_code == 404
    # Company B may reuse the same code.
    assert client.post(
        f"{PREFIX}/currencies", headers=hb, json={"code": "GBP", "name": "Pound"}
    ).status_code == 201


# ------------------------------------------------------------ currency rates
def _make_currency(client, h, code="USD"):
    return client.post(
        f"{PREFIX}/currencies", headers=h, json={"code": code, "name": code}
    ).json()


def test_rate_crud_flow(client, seeded):
    h = _login_and_select(client, seeded)
    _make_currency(client, h, "USD")

    resp = client.post(
        f"{PREFIX}/currency-rates",
        headers=h,
        json={
            "currency_code": "USD",
            "rate_to_base": 48.5,
            "valid_from": "2026-01-01T00:00:00Z",
        },
    )
    assert resp.status_code == 201
    rid = resp.json()["id"]
    assert float(resp.json()["rate_to_base"]) == 48.5

    lst = client.get(f"{PREFIX}/currency-rates", headers=h)
    assert [r["id"] for r in lst.json()] == [rid]

    # filter by currency_code
    filtered = client.get(
        f"{PREFIX}/currency-rates?currency_code=USD", headers=h
    )
    assert [r["id"] for r in filtered.json()] == [rid]

    upd = client.patch(
        f"{PREFIX}/currency-rates/{rid}", headers=h, json={"rate_to_base": 49}
    )
    assert upd.status_code == 200
    assert float(upd.json()["rate_to_base"]) == 49.0

    assert (
        client.delete(f"{PREFIX}/currency-rates/{rid}", headers=h).status_code == 204
    )


def test_rate_rejects_unknown_currency(client, seeded):
    h = _login_and_select(client, seeded)
    # No currency "JPY" created in this company -> 400.
    resp = client.post(
        f"{PREFIX}/currency-rates",
        headers=h,
        json={
            "currency_code": "JPY",
            "rate_to_base": 1.0,
            "valid_from": "2026-01-01T00:00:00Z",
        },
    )
    assert resp.status_code == 400


def test_rate_cannot_reference_other_company_currency(client, seeded, seeded_other):
    # Company A owns currency "USD".
    ha = _login_and_select(client, seeded)
    _make_currency(client, ha, "USD")

    # Company B has no "USD" -> creating a rate for it is rejected (400).
    hb = _login_and_select(client, seeded_other)
    resp = client.post(
        f"{PREFIX}/currency-rates",
        headers=hb,
        json={
            "currency_code": "USD",
            "rate_to_base": 48.5,
            "valid_from": "2026-01-01T00:00:00Z",
        },
    )
    assert resp.status_code == 400


def test_rate_company_isolation(client, seeded, seeded_other):
    ha = _login_and_select(client, seeded)
    _make_currency(client, ha, "USD")
    rid = client.post(
        f"{PREFIX}/currency-rates",
        headers=ha,
        json={
            "currency_code": "USD",
            "rate_to_base": 48.5,
            "valid_from": "2026-01-01T00:00:00Z",
        },
    ).json()["id"]

    hb = _login_and_select(client, seeded_other)
    assert client.get(f"{PREFIX}/currency-rates", headers=hb).json() == []
    assert (
        client.get(f"{PREFIX}/currency-rates/{rid}", headers=hb).status_code == 404
    )
