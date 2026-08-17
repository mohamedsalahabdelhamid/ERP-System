"""Auto-generated per-company codes/numbers for new modules.

Each entity that carries a user-visible code (branch, work order, payment,
journal entry) now auto-generates a unique value when the caller omits it,
and still rejects explicit duplicates with 409.
"""

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


def _make_item_and_warehouse(client, h):
    item_id = client.post(
        f"{PREFIX}/items", headers=h, json={"name": "Widget", "code": "IT-AUTO1"}
    ).json()["id"]
    wh_id = client.post(
        f"{PREFIX}/warehouses", headers=h, json={"name": "WH", "code": "WH-AUTO1"}
    ).json()["id"]
    return item_id, wh_id


def _make_partner(client, h):
    return client.post(
        f"{PREFIX}/partners",
        headers=h,
        json={"type": "customer", "name": "Auto Partner", "code": "AUTO-1000"},
    ).json()["id"]


def _make_account(client, h, code="5001"):
    return client.post(
        f"{PREFIX}/accounting/accounts",
        headers=h,
        json={"code": code, "name": "Test Account", "account_type": "asset"},
    ).json()["id"]


# ------------------------------------------------------------------- branches
def test_branch_auto_code_when_omitted(client, seeded):
    h = _login_and_select(client, seeded)
    resp = client.post(
        f"{PREFIX}/companies/{seeded['company_id']}/branches",
        headers=h,
        json={"name": "Auto Branch"},
    )
    assert resp.status_code == 201
    assert resp.json()["code"].startswith("BR-")


def test_branch_explicit_code_respected_and_duplicate_rejected(client, seeded):
    h = _login_and_select(client, seeded)
    first = client.post(
        f"{PREFIX}/companies/{seeded['company_id']}/branches",
        headers=h,
        json={"name": "B1", "code": "BR-MANUAL"},
    )
    assert first.status_code == 201
    assert first.json()["code"] == "BR-MANUAL"

    dup = client.post(
        f"{PREFIX}/companies/{seeded['company_id']}/branches",
        headers=h,
        json={"name": "B2", "code": "BR-MANUAL"},
    )
    assert dup.status_code == 409


# ------------------------------------------------------------------ work orders
def test_work_order_auto_number_when_omitted(client, seeded):
    h = _login_and_select(client, seeded)
    item_id, wh_id = _make_item_and_warehouse(client, h)
    resp = client.post(
        f"{PREFIX}/manufacturing/work-orders",
        headers=h,
        json={"item_id": item_id, "warehouse_id": wh_id, "planned_quantity": 5},
    )
    assert resp.status_code == 201
    assert resp.json()["number"].startswith("WO-")


def test_work_order_explicit_number_and_duplicate_rejected(client, seeded):
    h = _login_and_select(client, seeded)
    item_id, wh_id = _make_item_and_warehouse(client, h)
    first = client.post(
        f"{PREFIX}/manufacturing/work-orders",
        headers=h,
        json={
            "item_id": item_id,
            "warehouse_id": wh_id,
            "planned_quantity": 1,
            "number": "WO-MANUAL",
        },
    )
    assert first.status_code == 201
    assert first.json()["number"] == "WO-MANUAL"

    dup = client.post(
        f"{PREFIX}/manufacturing/work-orders",
        headers=h,
        json={
            "item_id": item_id,
            "warehouse_id": wh_id,
            "planned_quantity": 1,
            "number": "WO-MANUAL",
        },
    )
    assert dup.status_code == 409


# -------------------------------------------------------------------- payments
def test_payment_auto_reference_when_omitted(client, seeded):
    h = _login_and_select(client, seeded)
    partner_id = _make_partner(client, h)
    resp = client.post(
        f"{PREFIX}/payments",
        headers=h,
        json={"partner_id": partner_id, "amount": 100, "payment_date": "2026-08-16"},
    )
    assert resp.status_code == 201
    assert resp.json()["reference"].startswith("PAY-")


def test_payment_explicit_reference_and_duplicate_rejected(client, seeded):
    h = _login_and_select(client, seeded)
    partner_id = _make_partner(client, h)
    body = {"partner_id": partner_id, "amount": 100, "reference": "PAY-MANUAL"}
    first = client.post(f"{PREFIX}/payments", headers=h, json=body)
    assert first.status_code == 201
    assert first.json()["reference"] == "PAY-MANUAL"

    dup = client.post(f"{PREFIX}/payments", headers=h, json=body)
    assert dup.status_code == 409


# -------------------------------------------------------------- journal entries
def test_journal_entry_auto_reference_when_omitted(client, seeded):
    h = _login_and_select(client, seeded)
    acc = _make_account(client, h)
    resp = client.post(
        f"{PREFIX}/accounting/journal-entries",
        headers=h,
        json={
            "entry_date": "2026-08-16",
            "lines": [
                {"account_id": acc, "debit": 50},
                {"account_id": acc, "credit": 50},
            ],
        },
    )
    assert resp.status_code == 201
    assert resp.json()["reference"].startswith("JE-")


def test_journal_entry_explicit_reference_and_duplicate_rejected(client, seeded):
    h = _login_and_select(client, seeded)
    acc = _make_account(client, h)
    body = {
        "entry_date": "2026-08-16",
        "reference": "JE-MANUAL",
        "lines": [
            {"account_id": acc, "debit": 50},
            {"account_id": acc, "credit": 50},
        ],
    }
    first = client.post(f"{PREFIX}/accounting/journal-entries", headers=h, json=body)
    assert first.status_code == 201
    assert first.json()["reference"] == "JE-MANUAL"

    dup = client.post(f"{PREFIX}/accounting/journal-entries", headers=h, json=body)
    assert dup.status_code == 409
