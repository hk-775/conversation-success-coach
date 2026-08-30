#!/usr/bin/env bash
set -euo pipefail
export PYTHONDONTWRITEBYTECODE=1

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT_DIR}"

if [[ -z "${CSC_PYTHON_BIN:-}" ]] && command -v uv >/dev/null 2>&1; then
    exec uv run --python 3.12 --extra dev pytest tests -q --tb=short
fi

PYTHON_BIN="${CSC_PYTHON_BIN:-python3}"
exec env PYTHONPATH=src "${PYTHON_BIN}" -m pytest tests -q --tb=short
