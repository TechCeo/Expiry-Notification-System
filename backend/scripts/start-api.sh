#!/usr/bin/env sh
set -eu

if [ "${RUN_MIGRATIONS_ON_STARTUP:-false}" = "true" ]; then
  alembic upgrade head
fi

if [ "${SEED_DEMO_ON_STARTUP:-false}" = "true" ]; then
  python -m app.cli.seed_demo_data \
    --owner-email "${DEMO_OWNER_EMAIL:-owner@example.com}" \
    --viewer-email "${DEMO_VIEWER_EMAIL:-demo@example.com}"
fi

exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}"
