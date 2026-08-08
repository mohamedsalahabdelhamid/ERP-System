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
- Next: **Phase 1 – Multi-Company Core & Auth**.

## Run locally (Docker)

```bash
cp .env.example .env      # then edit secrets
docker compose up --build
```

Then check:

- API root:  http://localhost/            (via nginx)
- Health:    http://localhost/health
- Docs:      http://localhost/docs
- Direct:    http://localhost:8000/health  (bypassing nginx, if exposed)

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
