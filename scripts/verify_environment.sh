#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

check_command() {
  local name="$1"
  local command="$2"

  if command -v "$command" >/dev/null 2>&1; then
    echo "[ok] $name: $(command -v "$command")"
  else
    echo "[missing] $name"
  fi
}

echo "Universe Studio environment check"
check_command "Node.js" "node"
check_command "pnpm" "pnpm"
check_command "Python 3" "python3"
check_command "Docker" "docker"

if [ -f ".env" ]; then
  echo "[ok] root .env exists"
else
  echo "[missing] root .env"
fi

if [ -f "frontend/.env.local" ]; then
  echo "[ok] frontend/.env.local exists"
else
  echo "[missing] frontend/.env.local"
fi

if [ -f "backend/.env" ]; then
  echo "[ok] backend/.env exists"
else
  echo "[missing] backend/.env"
fi

check_openai_key() {
  local file="$1"

  if [ ! -f "$file" ]; then
    echo "[missing] OPENAI_API_KEY file: $file"
    return
  fi

  if grep -Eq '^OPENAI_API_KEY=.+$' "$file"; then
    echo "[ok] OPENAI_API_KEY configured in $file"
  else
    echo "[missing] OPENAI_API_KEY is empty in $file"
  fi
}

check_openai_key ".env"
check_openai_key "backend/.env"

if command -v docker >/dev/null 2>&1; then
  docker compose config >/dev/null
  echo "[ok] docker compose config"
else
  echo "[skipped] docker compose config because Docker is missing"
fi
