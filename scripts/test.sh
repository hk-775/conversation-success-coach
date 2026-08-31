#!/usr/bin/env bash
set -euo pipefail
export PYTHONDONTWRITEBYTECODE=1

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT_DIR}"

if ! command -v uv >/dev/null 2>&1; then
    echo "uv is required. Install it from the official Astral distribution, then retry." >&2
    exit 1
fi

exec uv run --locked --extra dev pytest tests -q --tb=short \
    --cov=conversation_success_coach \
    --cov-branch \
    --cov-report=term-missing
