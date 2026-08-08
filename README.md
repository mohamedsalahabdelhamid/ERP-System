# ERP System – Flexible Multi‑Activity, Multi‑Company

This project is a **flexible ERP product** that runs multiple companies and business activities on a single codebase and server.

It is designed to be:
- **Multi‑Company**: many companies on one instance.
- **Multi‑Activity**: factories, trading, retail, pharmacies, restaurants, contracting, real estate, cars, academies…
- **Configurable per Client**: each company enables its own modules, costing models, currencies, and units.

---
## 1. Architecture & Tech Stack

- **Backend**: Python (Django or FastAPI).
- **Database**: PostgreSQL.
- **Frontend**: Web dashboard (HTML/CSS/Bootstrap or Admin template).
- **Reverse Proxy**: Nginx.
- **Optional**: Redis (cache / background jobs).
- **Deployment**: Docker + docker‑compose (web, db, nginx, redis).

Basic docker‑compose services:
- `web`: backend API + business logic.
- `db`: PostgreSQL with volume.
- `nginx`: reverse proxy / SSL.
- `redis`: optional.

---
## 2. Core Domain Model

### Multi‑Company
- `companies`: name, code, base_currency, activity_type, is_active.
- `branches`: per‑company branches.
- `company_settings`: enabled_modules, cost_method, flags (has_manufacturing, has_projects, has_pos, pos_style).

### Users & Permissions
- `users`: auth & identity.
- `roles`, `permissions`, `user_roles`, `role_permissions`: per‑company access control.

### Master Data
- `partners`: customers / suppliers.
- `item_categories`, `items`: products & services.
- `units`, `unit_conversions`: units of measure & conversions.
- `warehouses`, `warehouse_stock`, `inventory_movements`: stock per warehouse.

### Currencies
- `currencies`, `currency_rates`.
- Each document stores: `document_currency`, `fx_rate_used`, totals in document & base currency.

---
## 3. Functional Modules (High Level)

- **Sales**: sales invoices, lines, payments.
- **Purchases**: purchase invoices, lines, payments.
- **POS**: sessions, orders, order lines.
- **Inventory**: items, stock, movements, stock taking.
- **Manufacturing**: BOMs, work orders, consumption, labor, overheads, output.
- **Projects / Jobs**: projects/jobs with materials, labor, overheads.
- **HR (optional)**: employees, departments, attendance, payroll.
- **Accounting**: chart_of_accounts, journal_entries, journal_lines.
- **Costs**: product costing + job/project costing.
- **Reports & Dashboards**: per module, filterable.

---
## 4. Costing Models

- **Product‑level costing** (trading/retail):
  - Weighted Average per (company, warehouse, item).
  - Stock‑in updates `average_cost`; stock‑out uses `average_cost` for COGS.

- **Work‑order / manufacturing costing** (factories):
  - Finished Cost = Raw Materials + Direct Labor + Overheads.

- **Job / Project costing** (contracting, real estate, cars):
  - Project Cost = Materials + Labor + Overheads.
  - Profit = Revenue − Project Cost.

---
## 5. Accounting Integration (Later Phase)

Once business flows are stable:
- Implement GL: `chart_of_accounts`, `journal_entries`, `journal_lines`.
- Post:
  - Sales invoices → AR/Cash, Sales, VAT, Inventory, COGS.
  - Purchase invoices → Inventory, Input VAT, AP.
  - Manufacturing completion → move cost from raw to finished goods.
  - FX differences → FX gain/loss accounts.

---
## 6. Implementation Roadmap (Summary)

1. **Phase 0 – Infra**: repo, Python env, Dockerfile, docker‑compose, `/health`.
2. **Phase 1 – Multi‑Company & Auth**: users, companies, branches, company scoping.
3. **Phase 2 – Roles & Permissions**: roles, permissions, user_roles.
4. **Phase 3 – Master Data**: partners, items, units, warehouses, inventory movements.
5. **Phase 4 – Currencies & Units**: currencies, rates, units & conversions.
6. **Phase 5 – Sales & Purchases**: invoices, lines, payments, confirm logic (stock + cost).
7. **Phase 6 – Inventory Reporting**: stock balance, movements, adjustments.
8. **Phase 7 – Manufacturing & Projects**: BOMs, work orders, jobs, costing reports.
9. **Phase 8 – HR (optional)**: employees, attendance, payroll.
10. **Phase 9 – Accounting Integration**: GL + financial reports.
11. **Phase 10 – Costs & Dashboards**: cost reports & KPIs.
12. **Phase 11 – Hardening & Production**: indexes, security, backup, deploy.

For the full detailed spec (tables, flows, and infographic script), see the main documentation file or system design doc.