#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND_DIR="$ROOT_DIR/backend"
ALEMBIC_BIN="$BACKEND_DIR/.venv/bin/alembic"

if [ ! -x "$ALEMBIC_BIN" ]; then
  echo "[missing] Alembic executable not found at backend/.venv/bin/alembic"
  echo "Run:"
  echo "  cd backend"
  echo "  python3.12 -m venv .venv"
  echo "  .venv/bin/python -m pip install -e \".[dev]\""
  exit 127
fi

cd "$BACKEND_DIR"
exec "$ALEMBIC_BIN" "$@"
