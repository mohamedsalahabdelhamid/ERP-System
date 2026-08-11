# ERP System — Runbook

One stack, two environments. The **exact same** `docker-compose.yml`, `.env`,
migrations, seed, and backup scripts are used for a local experiment and for a
real server deployment — nothing changes between them.

## 1. Quick start (local experiment = server preview)

Requirements: Docker with the Compose plugin.

```bash
./start.sh        # creates .env (first time), builds, starts, seeds
```

Open http://localhost:9009/ — the frontend Nginx serves the SPA **and** proxies
`/api` to the backend, so the whole system is one origin, exactly like a real
deployment.

| URL | What |
|---|---|
| http://localhost:9009/ | Web UI |
| http://localhost:9009/api/v1/docs | Swagger UI |
| http://localhost:9009/health | Health check |

Login: `admin@example.com` / `admin123` (company: **DEMO**).

## 2. Manual operations

All of these run identically on a server.

```bash
# Build & start everything (Postgres, Redis, API, frontend)
docker compose up --build -d

# Watch a service
docker compose logs -f web

# Stop (keeps data)
docker compose down

# Stop AND delete all data (Postgres + Redis volumes)
docker compose down -v

# Apply migrations (done automatically at container start by docker/entrypoint.sh)
docker compose exec -T web alembic upgrade head

# Seed the demo company + admin + demo data (idempotent)
docker compose exec -T web python -m scripts.seed

# Full reseed: delete the demo company and recreate everything
docker compose exec -T web python -m scripts.seed --reset
```

## 3. Backup & restore

```bash
# Backup (writes backups/erp_<db>_<timestamp>.sql.gz, keeps newest 14)
./scripts/backup_db.sh

# Backup to a custom directory
./scripts/backup_db.sh /var/backups/erp

# Restore (WARNING: drops the target database first)
./scripts/restore_db.sh backups/erp_erp_20260810_120000.sql.gz
```

Schedule backups with cron on the server:

```cron
0 2 * * * cd /opt/erp && ./scripts/backup_db.sh >> backups/backup.log 2>&1
```

## 4. Configuration

Configuration lives in `.env` (git-ignored). Reference: `.env.example`.

- `APP_ENV=production` — the system **always** runs on PostgreSQL; there is no
  SQLite fallback in the application code. Tests use their own in-memory engine.
- `SECRET_KEY` — generate with `openssl rand -hex 32`. Changing it invalidates
  existing access tokens.
- `POSTGRES_PASSWORD` — set once **before** first `up`; the `db` volume stores it.
- `CORS_ORIGINS` — comma-separated list; leave empty for same-origin (recommended).

## 5. Deploying on a real server

1. Install Docker, copy the project, set `.env`, then `docker compose up --build -d`.
2. **TLS**: the stack listens on port 80. Terminate HTTPS in front of it (Caddy,
   Traefik, or a cloud load balancer) and forward to the host's port 80/9009.
   Uncomment the HTTP→HTTPS redirect block in `frontend/nginx.conf` if needed.
3. **Security headers** (CSP, nosniff, X-Frame-Options, …) are already served by
   Nginx and were verified against a running stack.
4. Open only ports 80 (and 22 for SSH) on the firewall. **Do not** publish the
   Postgres port (`5432`) or the backend port (`8000`) to the public internet.
5. Point `CORS_ORIGINS` at your real domain if the frontend is served from a
   different origin than the API.
6. Set up the cron backup above and **test a restore** before going live.

## 6. Testing

```bash
# Requires a Python 3.12 venv with requirements.txt installed.
python -m pytest -q        # 61 tests, uses in-memory SQLite only
```

## 7. Troubleshooting

- **`The repository ... is no longer signed` during build** — the base image
  layer is already fixed; the image installs no system packages and never runs
  apt. Rebuild with `docker compose build --no-cache web` if a stale layer is cached.
- **Login fails / "No company selected"** — call `selectCompany` after login;
  the UI does this automatically. If the demo company is missing, run the seed.
- **Port 9009 or 5432 already in use** — edit the ports in `docker-compose.yml`.
- **Wrong Postgres password after `.env` change** — the `db` volume was
  initialized with the old password: `docker compose down -v && docker compose up -d`
  (this deletes all data).
