#!/bin/sh
set -eu

if [ "${RESET_DEMO_DATA_ON_START:-false}" = "true" ]; then
  uv run python -m app.db.demo_seed
fi

exec "$@"
