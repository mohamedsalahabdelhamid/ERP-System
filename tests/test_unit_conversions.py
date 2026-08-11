"""Phase 4 unit-conversion tests: CRUD, business rules, company isolation."""

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


def _make_unit(client, h, code):
    return client.post(
        f"{PREFIX}/units", headers=h, json={"name": code, "code": code}
    ).json()["id"]


def test_conversion_crud_flow(client, seeded):
    h = _login_and_select(client, seeded)
    box = _make_unit(client, h, "BOX")
    pcs = _make_unit(client, h, "PCS")

    resp = client.post(
        f"{PREFIX}/unit-conversions",
        headers=h,
        json={"from_unit_id": box, "to_unit_id": pcs, "factor": 12},
    )
    assert resp.status_code == 201
    conv = resp.json()
    cid = conv["id"]
    assert conv["company_id"] == seeded["company_id"]
    assert float(conv["factor"]) == 12.0

    lst = client.get(f"{PREFIX}/unit-conversions", headers=h)
    assert [c["id"] for c in lst.json()] == [cid]

    upd = client.patch(
        f"{PREFIX}/unit-conversions/{cid}", headers=h, json={"factor": 24}
    )
    assert upd.status_code == 200
    assert float(upd.json()["factor"]) == 24.0

    assert (
        client.delete(f"{PREFIX}/unit-conversions/{cid}", headers=h).status_code
        == 204
    )
    assert (
        client.get(f"{PREFIX}/unit-conversions/{cid}", headers=h).status_code == 404
    )


def test_conversion_duplicate_pair_rejected(client, seeded):
    h = _login_and_select(client, seeded)
    box = _make_unit(client, h, "BOX")
    pcs = _make_unit(client, h, "PCS")
    body = {"from_unit_id": box, "to_unit_id": pcs, "factor": 12}
    assert client.post(f"{PREFIX}/unit-conversions", headers=h, json=body).status_code == 201
    assert client.post(f"{PREFIX}/unit-conversions", headers=h, json=body).status_code == 409


def test_conversion_same_unit_rejected(client, seeded):
    h = _login_and_select(client, seeded)
    pcs = _make_unit(client, h, "PCS")
    resp = client.post(
        f"{PREFIX}/unit-conversions",
        headers=h,
        json={"from_unit_id": pcs, "to_unit_id": pcs, "factor": 1},
    )
    assert resp.status_code == 400


def test_conversion_non_positive_factor_rejected(client, seeded):
    h = _login_and_select(client, seeded)
    box = _make_unit(client, h, "BOX")
    pcs = _make_unit(client, h, "PCS")
    resp = client.post(
        f"{PREFIX}/unit-conversions",
        headers=h,
        json={"from_unit_id": box, "to_unit_id": pcs, "factor": 0},
    )
    assert resp.status_code == 400


def test_conversion_rejects_foreign_company_unit(client, seeded, seeded_other):
    # Company A owns both units.
    ha = _login_and_select(client, seeded)
    box = _make_unit(client, ha, "BOX")
    pcs = _make_unit(client, ha, "PCS")

    # Company B has its own unit but tries to reference A's units -> 400.
    hb = _login_and_select(client, seeded_other)
    own = _make_unit(client, hb, "KG")
    assert client.post(
        f"{PREFIX}/unit-conversions",
        headers=hb,
        json={"from_unit_id": box, "to_unit_id": own, "factor": 5},
    ).status_code == 400
    assert client.post(
        f"{PREFIX}/unit-conversions",
        headers=hb,
        json={"from_unit_id": own, "to_unit_id": pcs, "factor": 5},
    ).status_code == 400


def test_conversion_requires_permission(client, seeded_no_perms):
    h = _login_and_select(client, seeded_no_perms)
    assert client.get(f"{PREFIX}/unit-conversions", headers=h).status_code == 403
    assert client.post(
        f"{PREFIX}/unit-conversions",
        headers=h,
        json={"from_unit_id": 1, "to_unit_id": 2, "factor": 2},
    ).status_code == 403


def test_conversion_company_isolation(client, seeded, seeded_other):
    ha = _login_and_select(client, seeded)
    box = _make_unit(client, ha, "BOX")
    pcs = _make_unit(client, ha, "PCS")
    cid = client.post(
        f"{PREFIX}/unit-conversions",
        headers=ha,
        json={"from_unit_id": box, "to_unit_id": pcs, "factor": 12},
    ).json()["id"]

    hb = _login_and_select(client, seeded_other)
    assert client.get(f"{PREFIX}/unit-conversions", headers=hb).json() == []
    assert (
        client.get(f"{PREFIX}/unit-conversions/{cid}", headers=hb).status_code == 404
    )
    assert client.patch(
        f"{PREFIX}/unit-conversions/{cid}", headers=hb, json={"factor": 99}
    ).status_code == 404
