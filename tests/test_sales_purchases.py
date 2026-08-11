from datetime import datetime, timezone

PREFIX = "/api/v1"


def _login(client, email, password):
    return client.post(
        f"{PREFIX}/auth/login", json={"email": email, "password": password}
    )


def _auth_header(token):
    return {"Authorization": f"Bearer {token}"}


def _select_company(client, token, company_id, branch_id):
    resp = client.post(
        f"{PREFIX}/auth/select-company",
        headers=_auth_header(token),
        json={"company_id": company_id, "branch_id": branch_id},
    )
    assert resp.status_code == 200
    return resp.json()


def _create_partner(client, token):
    resp = client.post(
        f"{PREFIX}/partners",
        headers=_auth_header(token),
        json={
            "type": "customer",
            "name": "ACME Corp",
            "code": "ACME",
            "phone": "0123456789",
            "email": "acme@example.com",
            "address": "1 Test St",
            "tax_number": "TAX123",
            "opening_balance": 0,
            "credit_limit": 10000,
            "is_active": True,
        },
    )
    assert resp.status_code == 201
    return resp.json()


def _create_item(client, token):
    resp = client.post(
        f"{PREFIX}/items",
        headers=_auth_header(token),
        json={
            "name": "Widget",
            "code": "WIDG",
            "barcode": "000111222",
            "item_category_id": None,
            "base_unit_id": None,
            "sale_unit_id": None,
            "purchase_unit_id": None,
            "type": "stock",
            "default_sale_price": 50,
            "default_purchase_price": 30,
            "min_stock_level": 0,
            "expiry_control": False,
            "attributes": None,
            "is_active": True,
        },
    )
    assert resp.status_code == 201
    return resp.json()


def _create_sales_invoice(client, token, partner_id, item_id):
    resp = client.post(
        f"{PREFIX}/sales-invoices",
        headers=_auth_header(token),
        json={
            "partner_id": partner_id,
            "number": "SINV-001",
            "date": datetime.now(timezone.utc).isoformat(),
            "currency_code": "EGP",
            "fx_rate": 1,
            "lines": [
                {
                    "item_id": item_id,
                    "description": "Test sale",
                    "quantity": 2,
                    "unit_price": 50,
                }
            ],
        },
    )
    assert resp.status_code == 201
    return resp.json()


def _create_purchase_invoice(client, token, partner_id, item_id):
    resp = client.post(
        f"{PREFIX}/purchase-invoices",
        headers=_auth_header(token),
        json={
            "partner_id": partner_id,
            "number": "PINV-001",
            "date": datetime.now(timezone.utc).isoformat(),
            "currency_code": "EGP",
            "fx_rate": 1,
            "lines": [
                {
                    "item_id": item_id,
                    "description": "Test purchase",
                    "quantity": 3,
                    "unit_price": 30,
                }
            ],
        },
    )
    assert resp.status_code == 201
    return resp.json()


def test_sales_and_purchase_invoices_round_trip(client, seeded):
    token = _login(client, seeded["email"], seeded["password"]).json()["access_token"]
    _select_company(client, token, seeded["company_id"], seeded["branch_id"])

    partner = _create_partner(client, token)
    item = _create_item(client, token)

    sales_invoice = _create_sales_invoice(client, token, partner["id"], item["id"])
    assert sales_invoice["number"] == "SINV-001"
    assert sales_invoice["total_amount"] == 100
    assert sales_invoice["total_amount_base"] == 100

    purchase_invoice = _create_purchase_invoice(client, token, partner["id"], item["id"])
    assert purchase_invoice["number"] == "PINV-001"
    assert purchase_invoice["total_amount"] == 90
    assert purchase_invoice["total_amount_base"] == 90

    list_sales = client.get(
        f"{PREFIX}/sales-invoices", headers=_auth_header(token)
    )
    assert list_sales.status_code == 200
    assert any(inv["id"] == sales_invoice["id"] for inv in list_sales.json())

    list_purchases = client.get(
        f"{PREFIX}/purchase-invoices", headers=_auth_header(token)
    )
    assert list_purchases.status_code == 200
    assert any(inv["id"] == purchase_invoice["id"] for inv in list_purchases.json())

    sales_get = client.get(
        f"{PREFIX}/sales-invoices/{sales_invoice['id']}",
        headers=_auth_header(token),
    )
    assert sales_get.status_code == 200
    assert sales_get.json()["number"] == "SINV-001"

    purchase_get = client.get(
        f"{PREFIX}/purchase-invoices/{purchase_invoice['id']}",
        headers=_auth_header(token),
    )
    assert purchase_get.status_code == 200
    assert purchase_get.json()["number"] == "PINV-001"

    sales_delete = client.delete(
        f"{PREFIX}/sales-invoices/{sales_invoice['id']}",
        headers=_auth_header(token),
    )
    assert sales_delete.status_code == 204

    purchase_delete = client.delete(
        f"{PREFIX}/purchase-invoices/{purchase_invoice['id']}",
        headers=_auth_header(token),
    )
    assert purchase_delete.status_code == 204

    assert client.get(
        f"{PREFIX}/sales-invoices/{sales_invoice['id']}",
        headers=_auth_header(token),
    ).status_code == 404
    assert client.get(
        f"{PREFIX}/purchase-invoices/{purchase_invoice['id']}",
        headers=_auth_header(token),
    ).status_code == 404


def test_invoice_confirmation_updates_inventory(client, seeded):
    token = _login(client, seeded["email"], seeded["password"]).json()["access_token"]
    _select_company(client, token, seeded["company_id"], seeded["branch_id"])

    partner = _create_partner(client, token)
    item = _create_item(client, token)

    warehouse = client.post(
        f"{PREFIX}/warehouses",
        headers=_auth_header(token),
        json={"name": "Main Warehouse", "code": "WH1"},
    )
    assert warehouse.status_code == 201

    purchase = client.post(
        f"{PREFIX}/purchase-invoices",
        headers=_auth_header(token),
        json={
            "partner_id": partner["id"],
            "number": "PINV-002",
            "date": datetime.now(timezone.utc).isoformat(),
            "currency_code": "EGP",
            "fx_rate": 1,
            "lines": [
                {
                    "item_id": item["id"],
                    "description": "Stock receipt",
                    "quantity": 3,
                    "unit_price": 30,
                }
            ],
        },
    )
    assert purchase.status_code == 201

    sales = client.post(
        f"{PREFIX}/sales-invoices",
        headers=_auth_header(token),
        json={
            "partner_id": partner["id"],
            "number": "SINV-002",
            "date": datetime.now(timezone.utc).isoformat(),
            "currency_code": "EGP",
            "fx_rate": 1,
            "lines": [
                {
                    "item_id": item["id"],
                    "description": "Stock issue",
                    "quantity": 2,
                    "unit_price": 50,
                }
            ],
        },
    )
    assert sales.status_code == 201

    purchase_confirm = client.post(
        f"{PREFIX}/purchase-invoices/{purchase.json()['id']}/confirm",
        headers=_auth_header(token),
    )
    assert purchase_confirm.status_code == 200
    assert purchase_confirm.json()["is_confirmed"] is True

    sales_confirm = client.post(
        f"{PREFIX}/sales-invoices/{sales.json()['id']}/confirm",
        headers=_auth_header(token),
    )
    assert sales_confirm.status_code == 200
    assert sales_confirm.json()["is_confirmed"] is True

    stock = client.get(
        f"{PREFIX}/warehouse-stock",
        headers=_auth_header(token),
    )
    assert stock.status_code == 200
    rows = stock.json()
    assert len(rows) == 1
    assert rows[0]["item_id"] == item["id"]
    assert rows[0]["warehouse_id"] == warehouse.json()["id"]
    assert rows[0]["quantity"] == 1
    assert rows[0]["average_cost"] == 30.0

    movements = client.get(
        f"{PREFIX}/inventory-movements",
        headers=_auth_header(token),
    )
    assert movements.status_code == 200
    assert len(movements.json()) >= 2
