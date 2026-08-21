#!/usr/bin/env bash
# =====================================================================
# ERP backup script — PostgreSQL logical dump via the `db` container.
#
# Works identically for a local `docker compose` experiment and for a
# real server: it talks to the compose service named `db`.
#
# Usage:
#   ./scripts/backup_db.sh                 # dump to ./backups/
#   ./scripts/backup_db.sh /path/to/dir    # dump to a custom directory
#
# Keeps the newest BACKUP_KEEP (default 14) files.
# =====================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# Repo root = two levels up (backend/scripts/ -> backend/ -> repo root),
# where .env, backups/ and docker-compose.yml live.
PROJECT_DIR="$(dirname "$(dirname "$SCRIPT_DIR")")"
BACKEND_DIR="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_DIR"

# shellcheck disable=SC1091
[ -f .env ] && set -a && . ./.env && set +a

BACKUP_DIR="${1:-$PROJECT_DIR/backups}"
BACKUP_KEEP="${BACKUP_KEEP:-14}"

mkdir -p "$BACKUP_DIR"

STAMP="$(date +%Y%m%d_%H%M%S)"
FILENAME="erp_${POSTGRES_DB}_${STAMP}.sql.gz"
DEST="$BACKUP_DIR/$FILENAME"

echo "[backup] Dumping ${POSTGRES_DB} ..."
docker compose exec -T db \
  pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" \
  --no-owner --no-privileges \
  | gzip > "$DEST"

SIZE="$(du -h "$DEST" | cut -f1)"
echo "[backup] Wrote $DEST ($SIZE)"

# Prune old backups, keep the newest BACKUP_KEEP.
ls -1t "$BACKUP_DIR"/erp_*.sql.gz 2>/dev/null | tail -n +$((BACKUP_KEEP + 1)) | xargs -r rm -f
echo "[backup] Keeping the newest $BACKUP_KEEP backups."
