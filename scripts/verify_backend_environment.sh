#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND_DIR="$ROOT_DIR/backend"
PYTHON_BIN="$BACKEND_DIR/.venv/bin/python"
ALEMBIC_BIN="$BACKEND_DIR/.venv/bin/alembic"

echo "Universe Studio backend environment check"

if [ -x "$PYTHON_BIN" ]; then
  echo "[ok] virtual environment detected: backend/.venv"
else
  echo "[missing] virtual environment: backend/.venv"
  echo "Run: cd backend && python3.12 -m venv .venv && .venv/bin/python -m pip install -e \".[dev]\""
  exit 1
fi

if [ -x "$ALEMBIC_BIN" ]; then
  echo "[ok] Alembic executable: backend/.venv/bin/alembic"
else
  echo "[missing] Alembic executable: backend/.venv/bin/alembic"
  exit 1
fi

cd "$BACKEND_DIR"

"$PYTHON_BIN" -m pip check

"$PYTHON_BIN" - <<'PY'
from __future__ import annotations

from importlib.metadata import PackageNotFoundError, version

required_packages = [
    "alembic",
    "sqlalchemy",
    "psycopg",
    "psycopg-binary",
    "neo4j",
    "openai",
    "openai-agents",
    "fastapi",
    "pydantic",
    "pydantic-settings",
    "pgvector",
]

for package in required_packages:
    try:
        print(f"[ok] {package}=={version(package)}")
    except PackageNotFoundError:
        print(f"[missing] {package}")
        raise SystemExit(1)
PY

"$PYTHON_BIN" - <<'PY'
from __future__ import annotations

from sqlalchemy import create_engine, text

from app.core.config import get_settings
from app.integrations.neo4j.connection import Neo4jConnectionManager
from app.integrations.openai.status import get_openai_auth_status

settings = get_settings()
failed = False

try:
    engine = create_engine(settings.database_url, pool_pre_ping=True)
    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))
    print("[ok] PostgreSQL connection working")
except Exception as error:
    print(f"[fail] PostgreSQL connection failed: {error}")
    failed = True

try:
    manager = Neo4jConnectionManager(
        uri=settings.neo4j_uri,
        user=settings.neo4j_user,
        password=settings.neo4j_password,
    )
    try:
        manager.verify_connectivity()
        print("[ok] Neo4j connection working")
    finally:
        manager.close()
except Exception as error:
    print(f"[fail] Neo4j connection failed: {error}")
    failed = True

openai_status = get_openai_auth_status()
if openai_status.api_key_found:
    print(f"[ok] OpenAI configuration detected: {openai_status.message}")
else:
    print(f"[missing] OpenAI configuration: {openai_status.message}")
    failed = True

if failed:
    raise SystemExit(1)
PY

"$ALEMBIC_BIN" current
echo "[ok] Alembic current command completed"
