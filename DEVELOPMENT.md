# ERP System — Developer Guide

Backend: **FastAPI + PostgreSQL** (per the project specification).
Full product spec & roadmap: see root `README.md` and the specification PDF.

## Project layout

```
app/
  main.py            # FastAPI app factory & entrypoint
  core/
    config.py        # settings (env-driven)
    redis_client.py  # optional Redis helper
  db/
    base_class.py    # SQLAlchemy DeclarativeBase
    base.py          # metadata registry for Alembic
    session.py       # engine, SessionLocal, get_db, ping_db
  api/
    router.py        # aggregate API router (versioned)
    health.py        # /health endpoint
alembic/             # migrations (env + versions)
docker/
  entrypoint.sh      # wait-for-db + migrate + serve
  nginx/nginx.conf   # reverse proxy
Dockerfile
docker-compose.yml   # web, db, nginx, redis
```

## Phase status

- **Phase 0 – Infrastructure: DONE** — repo, Python env, Dockerfile,
  docker-compose (web/db/nginx/redis), Alembic scaffold, `/health`.
- **Phase 1 – Multi-Company Core & Auth: DONE** — companies/branches/settings,
  users, roles/permissions tables, token-based auth (login/logout),
  current-company selection per session, and company-scope enforcement.
- **Phase 2 – Roles & Permissions (basic enforcement): DONE** — default
  permission catalog seeded, Admin role granted all permissions, and a
  `require_permission("...")` dependency enforcing per-company permissions on
  endpoints (applied to the `/companies` routes as an example).
- Next: **Phase 3**.

## Phase 1 endpoints

All under the versioned prefix (e.g. `/api/v1`):

| Method | Path                    | Purpose                                        |
|--------|-------------------------|------------------------------------------------|
| POST   | `/auth/login`           | email + password → bearer token                |
| POST   | `/auth/logout`          | revoke current session                         |
| POST   | `/auth/select-company`  | set active company/branch for the session      |
| GET    | `/auth/me`              | current user, active scope, accessible companies |
| GET    | `/companies`            | companies the user can access                  |
| GET    | `/companies/current`    | active company (requires selection → else 409) |

Auth model: opaque bearer tokens stored as SHA-256 hashes in `auth_sessions`;
each session carries `current_company_id` / `current_branch_id`. Business
endpoints depend on `app.api.deps.get_current_company_id` to enforce scoping.

## Seed demo data

```bash
docker compose exec web python -m scripts.seed
# Login: admin@example.com / admin123  (company code: DEMO)
```


## Run locally (Docker)

```bash
cp .env.example .env      # then edit secrets
./start.sh
```

Then check:

- API root:  http://localhost:9000/
- Health:    http://localhost:9000/health
- Docs:      http://localhost:9000/docs
- Nginx:     http://localhost:9009/

`/health` returns the status of the app plus its `database` and `redis`
dependencies.

## Migrations (Alembic)

Once models exist (Phase 1+):

```bash
docker compose exec web alembic revision --autogenerate -m "message"
docker compose exec web alembic upgrade head
```

The `web` entrypoint applies `alembic upgrade head` automatically on startup
once migration files exist.

## Tests

```bash
docker compose exec web pytest
```
