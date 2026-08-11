"""Phase 6.3 + POS + reports + FX tests."""

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


def _create_warehouse_item(client, h, code):
    wh = client.post(
        f"{PREFIX}/warehouses", headers=h, json={"name": f"{code} WH", "code": code}
    ).json()
    item = client.post(
        f"{PREFIX}/items",
        headers=h,
        json={
            "name": f"Item {code}",
            "code": code,
            "type": "stock",
            "default_sale_price": 10,
            "default_purchase_price": 6,
        },
    ).json()
    return wh, item


def _stock_up(client, h, wh, item, qty=100, unit_cost=6):
    partner = client.post(
        f"{PREFIX}/partners",
        headers=h,
        json={"type": "supplier", "name": f"Sup {item['code']}", "code": f"S-{item['code']}"},
    ).json()
    inv = client.post(
        f"{PREFIX}/purchase-invoices",
        headers=h,
        json={
            "partner_id": partner["id"],
            "number": f"PO-{item['code']}",
            "date": "2026-01-01T00:00:00Z",
            "currency_code": "EGP",
            "fx_rate": 1,
            "warehouse_id": wh["id"],
            "lines": [
                {
                    "item_id": item["id"],
                    "quantity": qty,
                    "unit_price": unit_cost,
                    "cost_price": unit_cost,
                }
            ],
        },
    ).json()
    assert client.post(
        f"{PREFIX}/purchase-invoices/{inv['id']}/confirm", headers=h
    ).status_code == 200


def test_stock_take_full_flow(client, seeded):
    h = _login_and_select(client, seeded)
    wh, item = _create_warehouse_item(client, h, "ST")
    _stock_up(client, h, wh, item, qty=100, unit_cost=6)

    st = client.post(
        f"{PREFIX}/stock-takes",
        headers=h,
        json={
            "warehouse_id": wh["id"],
            "reference": "ST-2026-001",
            "lines": [{"item_id": item["id"], "counted_qty": 90}],
        },
    )
    assert st.status_code == 201
    st_id = st.json()["id"]
    assert st.json()["status"] == "draft"

    posted = client.post(f"{PREFIX}/stock-takes/{st_id}/post", headers=h)
    assert posted.status_code == 200
    assert posted.json()["status"] == "posted"
    assert posted.json()["posted_at"] is not None

    stock = client.get(f"{PREFIX}/warehouse-stock", headers=h).json()
    assert stock[0]["quantity"] == 90

    # Re-posting is rejected.
    assert client.post(f"{PREFIX}/stock-takes/{st_id}/post", headers=h).status_code == 400


def test_stock_take_requires_permission(client, seeded_no_perms):
    h = _login_and_select(client, seeded_no_perms)
    assert client.get(f"{PREFIX}/stock-takes", headers=h).status_code == 403


def test_pos_order_creates_confirmed_sale(client, seeded):
    h = _login_and_select(client, seeded)
    wh, item = _create_warehouse_item(client, h, "POS")
    _stock_up(client, h, wh, item, qty=100, unit_cost=6)

    partner = client.post(
        f"{PREFIX}/partners",
        headers=h,
        json={"type": "customer", "name": "Walk-in", "code": "C-WALK"},
    ).json()

    sess = client.post(
        f"{PREFIX}/pos/sessions",
        headers=h,
        json={"branch_id": seeded["branch_id"], "opening_cash": 500},
    )
    assert sess.status_code == 201
    sid = sess.json()["id"]
    assert sess.json()["status"] == "open"

    order = client.post(
        f"{PREFIX}/pos/orders",
        headers=h,
        json={
            "session_id": sid,
            "partner_id": partner["id"],
            "lines": [{"item_id": item["id"], "quantity": 2, "unit_price": 10}],
        },
    )
    assert order.status_code == 201
    body = order.json()
    assert body["total"] == 20
    assert body["status"] == "completed"
    assert body["invoice_id"] is not None

    # The POS order created + confirmed a sales invoice.
    invoices = client.get(f"{PREFIX}/sales-invoices", headers=h).json()
    assert any(i["id"] == body["invoice_id"] for i in invoices)

    # A payment was recorded.
    payments = client.get(f"{PREFIX}/payments", headers=h).json()
    assert any(p["amount"] == 20 for p in payments)

    # Closing a session computes expected cash from orders.
    closed = client.post(
        f"{PREFIX}/pos/sessions/{sid}/close",
        headers=h,
        json={"closing_cash": 520},
    )
    assert closed.status_code == 200
    assert closed.json()["status"] == "closed"
    assert closed.json()["expected_cash"] == 520
    assert closed.json()["variance"] == 0


def test_pos_requires_permission(client, seeded_no_perms):
    h = _login_and_select(client, seeded_no_perms)
    assert client.get(f"{PREFIX}/pos/sessions", headers=h).status_code == 403
    assert client.get(f"{PREFIX}/pos/orders", headers=h).status_code == 403


def test_reports(client, seeded):
    h = _login_and_select(client, seeded)
    wh, item = _create_warehouse_item(client, h, "REP")
    _stock_up(client, h, wh, item, qty=50, unit_cost=6)

    partner = client.post(
        f"{PREFIX}/partners",
        headers=h,
        json={"type": "customer", "name": "Rep Cust", "code": "C-REP"},
    ).json()
    inv = client.post(
        f"{PREFIX}/sales-invoices",
        headers=h,
        json={
            "partner_id": partner["id"],
            "number": "INV-REP-1",
            "date": "2026-02-01T00:00:00Z",
            "currency_code": "EGP",
            "fx_rate": 1,
            "lines": [{"item_id": item["id"], "quantity": 5, "unit_price": 10}],
        },
    ).json()
    client.post(f"{PREFIX}/sales-invoices/{inv['id']}/confirm", headers=h)

    summary = client.get(f"{PREFIX}/reports/sales-summary", headers=h).json()
    assert summary["total_invoices"] == 1
    assert summary["by_status"]["confirmed"]["total"] == 50

    value = client.get(f"{PREFIX}/reports/stock-value", headers=h).json()
    assert value["total_value"] == 45 * 6  # 50 bought, 5 sold

    low = client.get(f"{PREFIX}/reports/low-stock", headers=h, params={"threshold": 100}).json()
    assert any(r["item_id"] == item["id"] for r in low)

    project = client.post(
        f"{PREFIX}/projects",
        headers=h,
        json={"code": "P1", "name": "Project One", "contract_value": 10000},
    ).json()
    assert client.post(
        f"{PREFIX}/projects/{project['id']}/costs",
        headers=h,
        json={"cost_type": "material", "description": "steel", "quantity": 2, "unit_cost": 50},
    ).status_code == 201

    costs = client.get(f"{PREFIX}/reports/project-costs", headers=h).json()
    assert costs["total_cost"] == 100


def test_payments_fx_gain_loss(client, seeded):
    h = _login_and_select(client, seeded)
    wh, item = _create_warehouse_item(client, h, "FX")
    _stock_up(client, h, wh, item, qty=100, unit_cost=6)

    partner = client.post(
        f"{PREFIX}/partners",
        headers=h,
        json={"type": "customer", "name": "Fx Cust", "code": "C-FX"},
    ).json()
    inv = client.post(
        f"{PREFIX}/sales-invoices",
        headers=h,
        json={
            "partner_id": partner["id"],
            "number": "INV-FX-1",
            "date": "2026-03-01T00:00:00Z",
            "currency_code": "USD",
            "fx_rate": 50,
            "lines": [{"item_id": item["id"], "quantity": 1, "unit_price": 100}],
        },
    ).json()
    client.post(f"{PREFIX}/sales-invoices/{inv['id']}/confirm", headers=h)

    # Settle at a higher rate -> realized FX gain.
    pay = client.post(
        f"{PREFIX}/payments",
        headers=h,
        json={
            "partner_id": partner["id"],
            "reference": "PAY-FX-1",
            "document_type": "invoice",
            "document_id": inv["id"],
            "amount": 100,
            "currency_code": "USD",
            "fx_rate_used": 52,
        },
    )
    assert pay.status_code == 201
    body = pay.json()
    assert body["base_amount"] == 5200
    assert body["fx_gain_loss"] == 200

    # The gain is booked to an FX Gain journal account.
    entries = client.get(f"{PREFIX}/accounting/journal-entries", headers=h).json()
    assert len(entries) >= 1


def test_leave_requests_flow(client, seeded):
    h = _login_and_select(client, seeded)
    dept = client.post(f"{PREFIX}/hr/departments", headers=h, json={"name": "Ops"}).json()
    emp = client.post(
        f"{PREFIX}/hr/employees",
        headers=h,
        json={"department_id": dept["id"], "employee_number": "E1", "name": "Sam", "basic_salary": 5000},
    ).json()

    leave = client.post(
        f"{PREFIX}/hr/leave-requests",
        headers=h,
        json={
            "employee_id": emp["id"],
            "leave_type": "annual",
            "start_date": "2026-04-01",
            "end_date": "2026-04-05",
            "days": 5,
        },
    )
    assert leave.status_code == 201
    lid = leave.json()["id"]
    assert leave.json()["status"] == "pending"

    approved = client.post(
        f"{PREFIX}/hr/leave-requests/{lid}/status",
        headers=h,
        json={"status": "approved"},
    )
    assert approved.status_code == 200
    assert approved.json()["status"] == "approved"

    lst = client.get(f"{PREFIX}/hr/leave-requests", headers=h).json()
    assert len(lst) == 1
