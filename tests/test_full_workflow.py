from fastapi.testclient import TestClient

from app.main import app
from app.db.base import Base
from app.db.session import get_db
from app.modules.auth.router import router as auth_router
from app.modules.rbac.seed import sync_permissions, grant_all_to_role
from app.modules.rbac.models import Role, UserRole
from app.modules.companies.models import Branch, Company, CompanySettings
from app.modules.users.models import User
from app.core.security import hash_password
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool


def test_complete_business_flow():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)
    db = TestingSessionLocal()

    try:
        company = Company(name="Flow Co", code="FLOW", base_currency="EGP", activity_type="trading", is_active=True)
        db.add(company)
        db.flush()
        branch = Branch(company_id=company.id, name="Main", code="MAIN", is_active=True)
        db.add(branch)
        db.add(CompanySettings(company_id=company.id, enabled_modules=["sales", "purchases", "inventory", "accounting"], cost_method="weighted_average"))
        role = Role(company_id=company.id, name="Admin")
        db.add(role)
        db.flush()
        user = User(email="flow@example.com", password_hash=hash_password("secret123"), full_name="Flow Admin", is_active=True)
        db.add(user)
        db.flush()
        db.add(UserRole(user_id=user.id, company_id=company.id, branch_id=branch.id, role_id=role.id))
        sync_permissions(db)
        grant_all_to_role(db, role)
        db.commit()

        def override_get_db():
            try:
                yield db
            finally:
                pass

        app.dependency_overrides[get_db] = override_get_db
        with TestClient(app) as client:
            login = client.post('/api/v1/auth/login', json={'email': 'flow@example.com', 'password': 'secret123'})
            assert login.status_code == 200
            token = login.json()['access_token']
            headers = {'Authorization': f'Bearer {token}'}
            sel = client.post(
                '/api/v1/auth/select-company',
                headers=headers,
                json={'company_id': company.id, 'branch_id': branch.id},
            )
            assert sel.status_code == 200
            partner_resp = client.post('/api/v1/partners', json={'type':'customer','name':'Acme','code':'ACM-NEW','phone':'123'}, headers=headers)
            assert partner_resp.status_code == 201
            item_resp = client.post('/api/v1/items', json={'name':'Widget','code':'W1','type':'stock','default_sale_price':10,'default_purchase_price':8}, headers=headers)
            assert item_resp.status_code == 201
            warehouse_resp = client.post('/api/v1/warehouses', json={'name':'Main Warehouse','code':'WH1'}, headers=headers)
            assert warehouse_resp.status_code == 201
            invoice_resp = client.post('/api/v1/sales-invoices', json={'partner_id': partner_resp.json()['id'], 'number':'INV-1','date':'2026-01-01T00:00:00Z','currency_code':'EGP','fx_rate':1,'lines':[{'item_id': item_resp.json()['id'], 'description':'sale','quantity':1,'unit_price':10}]}, headers=headers)
            assert invoice_resp.status_code == 201
            purchase_resp = client.post('/api/v1/purchase-invoices', json={'partner_id': partner_resp.json()['id'], 'number':'PINV-1','date':'2026-01-01T00:00:00Z','currency_code':'EGP','fx_rate':1,'lines':[{'item_id': item_resp.json()['id'], 'description':'stock receipt','quantity':5,'unit_price':8}]}, headers=headers)
            assert purchase_resp.status_code == 201
            purchase_confirm = client.post(f"/api/v1/purchase-invoices/{purchase_resp.json()['id']}/confirm", headers=headers)
            assert purchase_confirm.status_code == 200
            confirm_resp = client.post(f"/api/v1/sales-invoices/{invoice_resp.json()['id']}/confirm", headers=headers)
            assert confirm_resp.status_code == 200
            payment_resp = client.post('/api/v1/payments', json={'partner_id': partner_resp.json()['id'], 'reference':'PAY-1','amount':10,'currency_code':'EGP'}, headers=headers)
            assert payment_resp.status_code == 201
            account_resp = client.post('/api/v1/accounting/accounts', json={'code':'1001','name':'Cash','account_type':'asset'}, headers=headers)
            assert account_resp.status_code == 201
            acc_id = account_resp.json()['id']
            journal_resp = client.post('/api/v1/accounting/journal-entries', json={'reference':'J1','entry_date':'2026-01-01','notes':'test','lines':[{'account_id':acc_id,'debit':100.0,'credit':0.0,'description':'dr'},{'account_id':acc_id,'debit':0.0,'credit':100.0,'description':'cr'}]}, headers=headers)
            assert journal_resp.status_code == 201, journal_resp.text
            assert client.get('/health').status_code == 200
            assert client.get('/').status_code == 200
    finally:
        app.dependency_overrides.clear()
        db.close()
        Base.metadata.drop_all(engine)
