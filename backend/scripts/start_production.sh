#!/usr/bin/env bash
set -euo pipefail

PORT="${PORT:-8000}"

echo "Running Alembic migrations..."
alembic upgrade head

echo "Starting Universe Studio API on port ${PORT}..."
exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT}"
