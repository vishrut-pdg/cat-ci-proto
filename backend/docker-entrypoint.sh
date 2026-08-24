#!/bin/sh
set -eu

if [ "${RESET_DEMO_DATA_ON_START:-false}" = "true" ]; then
  uv run python -m app.db.demo_seed
fi

# Always apply idempotent upgrades. PostgreSQL's /docker-entrypoint-initdb.d
# scripts do not rerun for persistent production volumes.
uv run python -m app.db.runtime_migrations

exec "$@"
