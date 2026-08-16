"""Phase A: double-entry integrity and document-lifecycle atomicity."""

from sqlalchemy import select

from app.modules.accounting.models import JournalEntry, JournalLine

PREFIX = "/api/v1"


def _login_and_select(client, data):
    token = client.post(
        f"{PREFIX}/auth/login", json={"email": data["email"], "password": data["password"]}
    ).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    resp = client.post(
        f"{PREFIX}/auth/select-company",
        headers=headers,
        json={"company_id": data["company_id"], "branch_id": data["branch_id"]},
    )
    assert resp.status_code == 200, resp.text
    return headers


def _create_account(client, headers, code="1001", name="Cash"):
    resp = client.post(
        f"{PREFIX}/accounting/accounts",
        headers=headers,
        json={"code": code, "name": name, "account_type": "asset"},
    )
    assert resp.status_code == 201, resp.text
    return resp.json()["id"]


def test_unbalanced_journal_entry_rejected(client, seeded):
    headers = _login_and_select(client, seeded)
    acc = _create_account(client, headers)
    resp = client.post(
        f"{PREFIX}/accounting/journal-entries",
        headers=headers,
        json={
            "reference": "UNB-1",
            "lines": [{"account_id": acc, "debit": 100.0, "credit": 0.0}],
        },
    )
    assert resp.status_code == 400, resp.text
    assert "unbalanced" in resp.json()["detail"].lower()


def test_empty_journal_entry_rejected(client, seeded):
    headers = _login_and_select(client, seeded)
    resp = client.post(
        f"{PREFIX}/accounting/journal-entries",
        headers=headers,
        json={"reference": "EMPTY", "lines": []},
    )
    assert resp.status_code == 400, resp.text


def test_balanced_journal_entry_accepted(client, seeded):
    headers = _login_and_select(client, seeded)
    acc = _create_account(client, headers)
    resp = client.post(
        f"{PREFIX}/accounting/journal-entries",
        headers=headers,
        json={
            "reference": "BAL-1",
            "lines": [
                {"account_id": acc, "debit": 50.0, "credit": 0.0},
                {"account_id": acc, "debit": 0.0, "credit": 50.0},
            ],
        },
    )
    assert resp.status_code == 201, resp.text


def test_journal_rejects_account_from_other_company(client, seeded, seeded_other):
    other_headers = _login_and_select(client, seeded_other)
    other_acc = _create_account(client, other_headers)
    headers = _login_and_select(client, seeded)
    resp = client.post(
        f"{PREFIX}/accounting/journal-entries",
        headers=headers,
        json={
            "reference": "CROSS-1",
            "lines": [
                {"account_id": other_acc, "debit": 1.0, "credit": 0.0},
                {"account_id": other_acc, "debit": 0.0, "credit": 1.0},
            ],
        },
    )
    assert resp.status_code == 400, resp.text


def test_payroll_journal_entry_is_balanced(client, seeded, db_session):
    headers = _login_and_select(client, seeded)
    dept = client.post(f"{PREFIX}/hr/departments", headers=headers, json={"name": "Ops"}).json()
    emp = client.post(
        f"{PREFIX}/hr/employees",
        headers=headers,
        json={
            "department_id": dept["id"],
            "employee_number": "E-1",
            "name": "Sam",
            "basic_salary": 3000.0,
        },
    ).json()
    absent = client.post(
        f"{PREFIX}/hr/attendance",
        headers=headers,
        json={"employee_id": emp["id"], "date": "2026-01-02", "status": "absent"},
    )
    assert absent.status_code == 201, absent.text

    resp = client.post(
        f"{PREFIX}/hr/payroll/run", headers=headers, json={"period": "2026-01"}
    )
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["status"] == "confirmed"
    assert body["total_deductions"] > 0

    entry = db_session.scalar(
        select(JournalEntry).where(JournalEntry.company_id == seeded["company_id"])
    )
    assert entry is not None, "payroll did not post a journal entry"
    lines = list(
        db_session.scalars(
            select(JournalLine).where(JournalLine.journal_entry_id == entry.id)
        ).all()
    )
    assert len(lines) >= 3
    total_debit = sum(float(line.debit or 0.0) for line in lines)
    total_credit = sum(float(line.credit or 0.0) for line in lines)
    assert abs(total_debit - total_credit) < 0.01
    assert abs(total_debit - body["total_gross"]) < 0.01


def test_delete_confirmed_sales_invoice_blocked(client, seeded):
    headers = _login_and_select(client, seeded)
    resp = client.patch(f"{PREFIX}/companies/settings", headers=headers, json={"block_negative_stock": False})
    assert resp.status_code == 200, resp.text

    partner = client.post(
        f"{PREFIX}/partners", headers=headers, json={"type": "customer", "name": "C", "code": "C1"}
    ).json()
    item = client.post(
        f"{PREFIX}/items", headers=headers, json={"name": "Item", "code": "I1", "type": "stock"}
    ).json()
    wh = client.post(
        f"{PREFIX}/warehouses", headers=headers, json={"name": "WH", "code": "WH1"}
    ).json()
    inv = client.post(
        f"{PREFIX}/sales-invoices",
        headers=headers,
        json={
            "partner_id": partner["id"],
            "number": "S-1",
            "date": "2026-01-01T00:00:00Z",
            "currency_code": "EGP",
            "fx_rate": 1,
            "lines": [{"item_id": item["id"], "quantity": 1, "unit_price": 10.0}],
        },
    )
    assert inv.status_code == 201, inv.text
    confirm = client.post(f"{PREFIX}/sales-invoices/{inv.json()['id']}/confirm", headers=headers)
    assert confirm.status_code == 200, confirm.text

    delete = client.delete(f"{PREFIX}/sales-invoices/{inv.json()['id']}", headers=headers)
    assert delete.status_code == 400, delete.text


def test_delete_confirmed_purchase_invoice_blocked(client, seeded):
    headers = _login_and_select(client, seeded)
    partner = client.post(
        f"{PREFIX}/partners", headers=headers, json={"type": "supplier", "name": "S", "code": "S1"}
    ).json()
    item = client.post(
        f"{PREFIX}/items", headers=headers, json={"name": "Item", "code": "I2", "type": "stock"}
    ).json()
    wh = client.post(
        f"{PREFIX}/warehouses", headers=headers, json={"name": "WH", "code": "WH2"}
    ).json()
    inv = client.post(
        f"{PREFIX}/purchase-invoices",
        headers=headers,
        json={
            "partner_id": partner["id"],
            "number": "P-1",
            "date": "2026-01-01T00:00:00Z",
            "currency_code": "EGP",
            "fx_rate": 1,
            "warehouse_id": wh["id"],
            "lines": [{"item_id": item["id"], "quantity": 1, "unit_price": 5.0}],
        },
    )
    assert inv.status_code == 201, inv.text
    confirm = client.post(f"{PREFIX}/purchase-invoices/{inv.json()['id']}/confirm", headers=headers)
    assert confirm.status_code == 200, confirm.text

    delete = client.delete(f"{PREFIX}/purchase-invoices/{inv.json()['id']}", headers=headers)
    assert delete.status_code == 400, delete.text
