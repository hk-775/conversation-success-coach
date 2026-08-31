#!/usr/bin/env bash
set -euo pipefail
export PYTHONDONTWRITEBYTECODE=1

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT_DIR}"

PORT="${CSC_PORT:-8103}"
HOST="${CSC_HOST:-127.0.0.1}"

if ! command -v uv >/dev/null 2>&1; then
    echo "uv is required. Install it from the official Astral distribution, then retry." >&2
    exit 1
fi

echo "Conversation Success Coach"
echo "  Dashboard:    http://${HOST}:${PORT}/dashboard"
echo "  Architecture: http://${HOST}:${PORT}/architecture"
echo "  API docs:     http://${HOST}:${PORT}/docs"
echo "  External calls and message delivery: disabled"
echo

exec uv run --locked conversation-success-coach serve \
    --host "${HOST}" --port "${PORT}"
