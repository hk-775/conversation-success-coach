#!/usr/bin/env bash
set -euo pipefail
export PYTHONDONTWRITEBYTECODE=1

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT_DIR}"

PORT="${CSC_PORT:-8103}"
HOST="${CSC_HOST:-127.0.0.1}"

echo "Conversation Success Coach"
echo "  Dashboard:    http://${HOST}:${PORT}/dashboard"
echo "  Architecture: http://${HOST}:${PORT}/architecture"
echo "  API docs:     http://${HOST}:${PORT}/docs"
echo "  External calls and message delivery: disabled"
echo

if [[ -z "${CSC_PYTHON_BIN:-}" ]] && command -v uv >/dev/null 2>&1; then
    exec uv run --python 3.12 \
        conversation-success-coach serve --host "${HOST}" --port "${PORT}"
fi

PYTHON_BIN="${CSC_PYTHON_BIN:-python3}"
if ! "${PYTHON_BIN}" -c 'import sys; raise SystemExit(sys.version_info < (3, 11))'; then
    echo "Python 3.11+ is required. Install uv or set CSC_PYTHON_BIN." >&2
    exit 1
fi

if ! "${PYTHON_BIN}" -c 'import fastapi, uvicorn' >/dev/null 2>&1; then
    echo "Installing the local package and runtime dependencies…"
    "${PYTHON_BIN}" -m pip install -e .
fi

exec "${PYTHON_BIN}" -m conversation_success_coach serve \
    --host "${HOST}" --port "${PORT}"
