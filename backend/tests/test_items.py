"""Phase 3 item master-data tests: categories, units, items + isolation."""

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


# ------------------------------------------------------------------- categories
def test_category_crud_and_parent_validation(client, seeded, seeded_other):
    h = _login_and_select(client, seeded)

    root = client.post(
        f"{PREFIX}/item-categories", headers=h, json={"name": "Root", "code": "C1"}
    )
    assert root.status_code == 201
    root_id = root.json()["id"]

    child = client.post(
        f"{PREFIX}/item-categories",
        headers=h,
        json={"name": "Child", "code": "C2", "parent_id": root_id},
    )
    assert child.status_code == 201
    assert child.json()["parent_id"] == root_id

    # parent from another company is rejected (400).
    hb = _login_and_select(client, seeded_other)
    bad = client.post(
        f"{PREFIX}/item-categories",
        headers=hb,
        json={"name": "X", "code": "CX", "parent_id": root_id},
    )
    assert bad.status_code == 400


# ------------------------------------------------------------------------ units
def test_unit_crud(client, seeded):
    h = _login_and_select(client, seeded)
    resp = client.post(
        f"{PREFIX}/units",
        headers=h,
        json={"name": "Piece", "code": "PCS", "symbol": "pc", "unit_type": "count"},
    )
    assert resp.status_code == 201
    uid = resp.json()["id"]

    upd = client.patch(f"{PREFIX}/units/{uid}", headers=h, json={"symbol": "pcs"})
    assert upd.status_code == 200
    assert upd.json()["symbol"] == "pcs"

    assert client.delete(f"{PREFIX}/units/{uid}", headers=h).status_code == 204


# ------------------------------------------------------------------------ items
def _make_category_and_unit(client, h):
    cat_id = client.post(
        f"{PREFIX}/item-categories", headers=h, json={"name": "Cat", "code": "CAT"}
    ).json()["id"]
    unit_id = client.post(
        f"{PREFIX}/units", headers=h, json={"name": "Piece", "code": "PCS"}
    ).json()["id"]
    return cat_id, unit_id


def test_item_crud_flow(client, seeded):
    h = _login_and_select(client, seeded)
    cat_id, unit_id = _make_category_and_unit(client, h)

    resp = client.post(
        f"{PREFIX}/items",
        headers=h,
        json={
            "name": "Widget",
            "code": "IT1",
            "item_category_id": cat_id,
            "base_unit_id": unit_id,
            "type": "stock",
            "default_sale_price": 10.5,
        },
    )
    assert resp.status_code == 201
    item = resp.json()
    iid = item["id"]
    assert item["company_id"] == seeded["company_id"]
    assert item["item_category_id"] == cat_id
    assert item["base_unit_id"] == unit_id

    lst = client.get(f"{PREFIX}/items", headers=h)
    assert [i["id"] for i in lst.json()] == [iid]

    upd = client.patch(
        f"{PREFIX}/items/{iid}", headers=h, json={"default_sale_price": 12}
    )
    assert upd.status_code == 200
    assert float(upd.json()["default_sale_price"]) == 12.0

    assert client.delete(f"{PREFIX}/items/{iid}", headers=h).status_code == 204


def test_item_duplicate_code_rejected(client, seeded):
    h = _login_and_select(client, seeded)
    assert client.post(
        f"{PREFIX}/items", headers=h, json={"name": "A", "code": "DUP"}
    ).status_code == 201
    assert client.post(
        f"{PREFIX}/items", headers=h, json={"name": "B", "code": "DUP"}
    ).status_code == 409


def test_item_rejects_foreign_company_references(client, seeded, seeded_other):
    # Company A owns a category + unit.
    ha = _login_and_select(client, seeded)
    cat_id, unit_id = _make_category_and_unit(client, ha)

    # Company B cannot reference A's category or unit when creating an item.
    hb = _login_and_select(client, seeded_other)
    by_cat = client.post(
        f"{PREFIX}/items",
        headers=hb,
        json={"name": "X", "code": "BX", "item_category_id": cat_id},
    )
    assert by_cat.status_code == 400

    by_unit = client.post(
        f"{PREFIX}/items",
        headers=hb,
        json={"name": "Y", "code": "BY", "base_unit_id": unit_id},
    )
    assert by_unit.status_code == 400


def test_item_company_isolation(client, seeded, seeded_other):
    ha = _login_and_select(client, seeded)
    iid = client.post(
        f"{PREFIX}/items", headers=ha, json={"name": "Secret", "code": "S1"}
    ).json()["id"]

    hb = _login_and_select(client, seeded_other)
    assert client.get(f"{PREFIX}/items", headers=hb).json() == []
    assert client.get(f"{PREFIX}/items/{iid}", headers=hb).status_code == 404
