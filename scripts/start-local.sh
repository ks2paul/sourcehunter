#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

cd "$ROOT_DIR"

if [ ! -d backend/.venv ]; then
  /opt/homebrew/bin/python3.11 -m venv backend/.venv
fi

backend/.venv/bin/python -m pip install -e "backend[dev]"

if [ ! -d frontend/node_modules ]; then
  (cd frontend && npm install)
fi

trap 'kill 0' EXIT

(cd backend && .venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000) &
(cd frontend && npm run dev -- --hostname 127.0.0.1 --port 3000) &

echo "SourceHunter is starting:"
echo "Frontend: http://127.0.0.1:3000"
echo "Backend:  http://127.0.0.1:8000"

wait
