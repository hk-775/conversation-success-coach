#!/usr/bin/env bash
set -euo pipefail
export PYTHONDONTWRITEBYTECODE=1

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT_DIR}"

PYTHON_BIN="${CSC_PYTHON_BIN:-}"
if [[ -z "${PYTHON_BIN}" ]]; then
    if command -v uv >/dev/null 2>&1; then
        PYTHON_BIN="$(uv python find 3.12)"
    else
        PYTHON_BIN="python3"
    fi
fi

PYCACHE_DIR="$(mktemp -d)"
cleanup() {
    rm -rf "${PYCACHE_DIR}"
}
trap cleanup EXIT

PYTHONPYCACHEPREFIX="${PYCACHE_DIR}" "${PYTHON_BIN}" -m compileall -q src tests

if command -v node >/dev/null 2>&1; then
    node --check src/conversation_success_coach/web/assets/site.js
    node --check src/conversation_success_coach/web/assets/architecture.js
    node --check src/conversation_success_coach/web/assets/dashboard.js
fi

if ! diff -qr src/conversation_success_coach/web site >/dev/null; then
    echo "site/ is not an exact mirror of the served landing/dashboard/architecture source." >&2
    echo "Run ./scripts/sync-site.sh and commit the result." >&2
    exit 1
fi

if rg -n \
    'github\.com/example|example/conversation|localhost:8080|127\.0\.0\.1:8080|MatchMind|Hinge|dating-specific' \
    . \
    --hidden \
    --glob '!.git/**' \
    --glob '!scripts/validate.sh'
then
    echo "Found placeholder URL, stale port, or removed source branding." >&2
    exit 1
fi

if command -v git >/dev/null 2>&1 && git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    tracked_generated="$(
        git ls-files -- . |
            rg '(^|/)(node_modules|__pycache__|\.pytest_cache|\.ruff_cache|\.mypy_cache)(/|$)|\.py[co]$' ||
            true
    )"
    if [[ -n "${tracked_generated}" ]]; then
        echo "Generated cache or bytecode is tracked as a package artifact:" >&2
        printf '%s\n' "${tracked_generated}" >&2
        exit 1
    fi
fi

required=(
    README.md QUICKSTART.md LICENSE SECURITY.md CONTRIBUTING.md
    CODE_OF_CONDUCT.md CHANGELOG.md NOTICE Dockerfile docker-compose.yml
    docs/ARCHITECTURE.md docs/ETHICS.md docs/API.md docs/DEMO.md
    docs/DEPLOYMENT.md site/index.html site/dashboard.html
    site/architecture.html .github/workflows/ci.yml
)
for path in "${required[@]}"; do
    if [[ ! -f "${path}" ]]; then
        echo "Missing required artifact: ${path}" >&2
        exit 1
    fi
done

echo "Package validation passed."
