# ERP System

A multi-company, multi-branch ERP built with **FastAPI, PostgreSQL, Alembic, Redis, React, and Docker** — one stack that runs identically on a local machine and on a real server.

## What is included
- Authentication, sessions, and company selection
- Multi-company and multi-branch structure
- RBAC permissions foundation
- Partners, items, units, warehouses, stock, movements
- Currencies and exchange rates
- Sales and purchase invoices with confirmation logic
- Accounting (double-entry journal entries, trial balance, reports)
- HR (departments, employees, attendance, payroll, leave)
- Payments, POS, projects, manufacturing (BOMs/work orders)
- Login rate limiting and Redis fail-open hardening
- Docker-based deployment (single origin: frontend Nginx proxies `/api`)

## Quick start

### Windows (recommended launchers)
1. Double-click **`setup.bat`** — one-time preparation: installs/opens Docker Desktop,
   creates `.env` with random secrets, builds the images, installs the local test
   environment and frontend dependencies, and runs the test suite.
2. Double-click **`start.bat`** — opens Docker automatically, starts all services,
   seeds demo data, and opens the app in your browser at `http://localhost:9009/`.

### Linux / server
```bash
./start.sh
```

## Demo login
- Email: `admin@example.com`
- Password: `admin123`
- Company: **DEMO**

> Override the bootstrap password for deployments via the `ADMIN_PASSWORD` environment variable.

## URLs (local)
- Web UI: `http://localhost:9009/`
- API docs (Swagger): `http://localhost:9009/api/v1/docs`
- Health check: `http://localhost:9009/health`

## Documentation
- `RUNBOOK.md` — run, backup/restore, and deploy operations
- `DEVELOPMENT.md` — developer guide (layout, tests)

## Testing
```bash
cd backend
python -m pytest -q     # unit + integration (110 tests)
python -m pytest tests/test_e2e.py -v   # E2E (requires the Docker stack running)
```

## License
Proprietary — internal use.
