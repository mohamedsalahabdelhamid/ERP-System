#!/usr/bin/env bash
# =====================================================================
# ERP restore script — restore a PostgreSQL dump into the `db` container.
#
# DANGER: this DROPS all data in the target database first.
#
# Usage:
#   ./scripts/restore_db.sh backups/erp_erp_20260810_000000.sql.gz
# =====================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_DIR"

# shellcheck disable=SC1091
[ -f .env ] && set -a && . ./.env && set +a

DUMP_FILE="${1:-}"
if [ -z "$DUMP_FILE" ] || [ ! -f "$DUMP_FILE" ]; then
  echo "Usage: $0 <dump-file.sql.gz>" >&2
  echo "Available backups:" >&2
  ls -1 backups/erp_*.sql.gz 2>/dev/null || true
  exit 1
fi

read -r -p "This will DROP all data in '${POSTGRES_DB}'. Continue? [y/N] " confirm
if [ "$confirm" != "y" ] && [ "$confirm" != "Y" ]; then
  echo "Aborted."
  exit 1
fi

echo "[restore] Dropping and recreating ${POSTGRES_DB} ..."
docker compose exec -T db \
  dropdb --if-exists -U "$POSTGRES_USER" "$POSTGRES_DB"
docker compose exec -T db \
  createdb -U "$POSTGRES_USER" "$POSTGRES_DB"

echo "[restore] Loading $DUMP_FILE ..."
gunzip -c "$DUMP_FILE" | docker compose exec -T db \
  psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -v ON_ERROR_STOP=1

echo "[restore] Done."
