"""Phase 3 inventory tests: warehouse CRUD + read-only stock/movements + isolation."""

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


def test_warehouse_crud_flow(client, seeded):
    h = _login_and_select(client, seeded)

    resp = client.post(
        f"{PREFIX}/warehouses",
        headers=h,
        json={"name": "Main WH", "code": "WH1", "branch_id": seeded["branch_id"]},
    )
    assert resp.status_code == 201
    wid = resp.json()["id"]
    assert resp.json()["company_id"] == seeded["company_id"]

    lst = client.get(f"{PREFIX}/warehouses", headers=h)
    assert [w["id"] for w in lst.json()] == [wid]

    upd = client.patch(
        f"{PREFIX}/warehouses/{wid}", headers=h, json={"name": "Central WH"}
    )
    assert upd.status_code == 200
    assert upd.json()["name"] == "Central WH"

    assert client.delete(f"{PREFIX}/warehouses/{wid}", headers=h).status_code == 204
    assert client.get(f"{PREFIX}/warehouses/{wid}", headers=h).status_code == 404


def test_warehouse_duplicate_code_rejected(client, seeded):
    h = _login_and_select(client, seeded)
    assert client.post(
        f"{PREFIX}/warehouses", headers=h, json={"name": "A", "code": "DUP"}
    ).status_code == 201
    assert client.post(
        f"{PREFIX}/warehouses", headers=h, json={"name": "B", "code": "DUP"}
    ).status_code == 409


def test_stock_and_movements_read_only_empty(client, seeded):
    h = _login_and_select(client, seeded)
    # No stock or movements exist yet (populated by later phases) -> empty lists.
    assert client.get(f"{PREFIX}/warehouse-stock", headers=h).status_code == 200
    assert client.get(f"{PREFIX}/warehouse-stock", headers=h).json() == []
    assert client.get(f"{PREFIX}/inventory-movements", headers=h).status_code == 200
    assert client.get(f"{PREFIX}/inventory-movements", headers=h).json() == []


def test_stock_requires_permission(client, seeded_no_perms):
    h = _login_and_select(client, seeded_no_perms)
    assert client.get(f"{PREFIX}/warehouse-stock", headers=h).status_code == 403
    assert client.get(f"{PREFIX}/inventory-movements", headers=h).status_code == 403


def test_warehouse_company_isolation(client, seeded, seeded_other):
    ha = _login_and_select(client, seeded)
    wid = client.post(
        f"{PREFIX}/warehouses", headers=ha, json={"name": "A WH", "code": "W1"}
    ).json()["id"]

    hb = _login_and_select(client, seeded_other)
    assert client.get(f"{PREFIX}/warehouses", headers=hb).json() == []
    assert client.get(f"{PREFIX}/warehouses/{wid}", headers=hb).status_code == 404
    assert client.patch(
        f"{PREFIX}/warehouses/{wid}", headers=hb, json={"name": "hack"}
    ).status_code == 404
