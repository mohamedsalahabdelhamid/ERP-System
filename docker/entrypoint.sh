#!/usr/bin/env bash
# Container entrypoint for the `web` service.
# Waits for PostgreSQL to accept connections, applies migrations, then starts
# the API server.
set -euo pipefail

echo "[entrypoint] Waiting for PostgreSQL at ${POSTGRES_HOST}:${POSTGRES_PORT} ..."
until python -c "
import socket, os, sys
s = socket.socket()
s.settimeout(2)
try:
    s.connect((os.environ['POSTGRES_HOST'], int(os.environ['POSTGRES_PORT'])))
except OSError:
    sys.exit(1)
" 2>/dev/null; do
  sleep 1
done
echo "[entrypoint] PostgreSQL is up."

# Apply database migrations (no-op in Phase 0 until the first revision exists).
if ls alembic/versions/*.py >/dev/null 2>&1; then
  echo "[entrypoint] Applying database migrations ..."
  alembic upgrade head
else
  echo "[entrypoint] No migrations yet - skipping alembic upgrade."
fi

echo "[entrypoint] Starting API server ..."
exec "$@"
