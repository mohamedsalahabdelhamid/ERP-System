# ERP System

A multi-company, multi-branch ERP backend built with FastAPI, PostgreSQL, Alembic, Redis, and Docker.

## What is included
- Authentication and company selection
- Multi-company and multi-branch structure
- RBAC permissions foundation
- Partners, items, units, warehouses, stock, movements
- Currencies and exchange rates
- Sales and purchase invoices with confirmation logic
- Inventory impact and weighted-average stock cost
- Docker-based local deployment

## Quick start
```bash
copy .env.example .env
bash start.sh
```

## Demo login
- Email: admin@example.com
- Password: admin123

## API docs
- http://localhost/docs
- http://localhost/health
