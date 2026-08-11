#!/usr/bin/env bash
set -euo pipefail

if ! command -v docker >/dev/null 2>&1; then
  echo 'Docker is required to run this stack.' >&2
  exit 1
fi

# Create `.env` only if it does not exist yet. NEVER overwrite an existing one:
# it holds the DB password and SECRET_KEY that the `db` volume was initialized with.
if [ ! -f .env ]; then
  echo "[start] Creating .env from .env.example (edit it if needed)."
  cp .env.example .env
fi

docker compose up --build -d

echo "[start] Waiting for services to become healthy ..."
docker compose up -d --wait --timeout 180

# Idempotent: seeds the demo company + admin + demo data if missing.
docker compose exec -T web python -m scripts.seed || true

printf '\nERP is running.\n'
printf 'Web UI (single entry point): http://localhost:9009/\n'
printf 'API docs:                    http://localhost:9009/docs (via backend port 8000)\n'
printf 'Health:                      http://localhost:9009/health\n'
printf 'Seed login:                  admin@example.com / admin123\n'
printf 'Backup:                      ./scripts/backup_db.sh\n'
