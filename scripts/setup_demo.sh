#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

if ! command -v docker >/dev/null 2>&1; then
  echo "Docker is required for one-click demo setup. Install Docker or run backend/scripts/seed_demo.py against an existing database."
  exit 1
fi

echo "Starting demo infrastructure..."
docker compose up -d postgres neo4j

echo "Running migrations..."
cd "$ROOT_DIR/backend"
PYTHON_BIN="${PYTHON_BIN:-./.venv/bin/python}"
if [ ! -x "$PYTHON_BIN" ]; then
  PYTHON_BIN="python3"
fi

"$PYTHON_BIN" -m alembic upgrade head

echo "Seeding Memory Market 2094..."
"$PYTHON_BIN" scripts/seed_demo.py

echo "Validating demo..."
"$PYTHON_BIN" scripts/validate_demo.py

echo "Demo setup complete."
