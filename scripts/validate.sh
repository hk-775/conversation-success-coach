#!/usr/bin/env bash
set -euo pipefail
export PYTHONDONTWRITEBYTECODE=1

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT_DIR}"

if ! command -v uv >/dev/null 2>&1; then
    echo "uv is required. Install it from the official Astral distribution, then retry." >&2
    exit 1
fi

uv run --locked --extra dev ruff check --no-cache src tests scripts
uv run --locked --extra dev bandit -q -r src scripts
uv run --locked --extra dev pytest tests -q --tb=short \
    --cov=conversation_success_coach \
    --cov-branch \
    --cov-report=term-missing
uv run --locked --extra dev python scripts/validate_package.py

while IFS= read -r -d '' script; do
    bash -n "${script}"
done < <(find scripts -type f -name '*.sh' -print0)

echo "Full validation passed."
