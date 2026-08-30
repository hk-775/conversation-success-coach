#!/usr/bin/env bash
set -euo pipefail
export PYTHONDONTWRITEBYTECODE=1

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT_DIR}"

PORT="${CSC_PORT:-8103}"
BASE_URL="http://127.0.0.1:${PORT}"
TEMP_DIR="$(mktemp -d)"
SERVER_LOG="${TEMP_DIR}/server.log"
SERVER_PID=""

cleanup() {
    if [[ -n "${SERVER_PID}" ]] && kill -0 "${SERVER_PID}" >/dev/null 2>&1; then
        kill "${SERVER_PID}" >/dev/null 2>&1 || true
        wait "${SERVER_PID}" 2>/dev/null || true
    fi
    rm -rf "${TEMP_DIR}"
}
trap cleanup EXIT

if [[ -z "${CSC_PYTHON_BIN:-}" ]] && command -v uv >/dev/null 2>&1; then
    CSC_DATABASE_PATH="${TEMP_DIR}/smoke.db" \
        uv run --python 3.12 --extra dev conversation-success-coach serve \
        --host 127.0.0.1 --port "${PORT}" >"${SERVER_LOG}" 2>&1 &
else
    PYTHON_BIN="${CSC_PYTHON_BIN:-python3}"
    CSC_DATABASE_PATH="${TEMP_DIR}/smoke.db" \
        PYTHONPATH=src "${PYTHON_BIN}" -m conversation_success_coach serve \
        --host 127.0.0.1 --port "${PORT}" >"${SERVER_LOG}" 2>&1 &
fi
SERVER_PID=$!

for _ in $(seq 1 40); do
    if curl --fail --silent "${BASE_URL}/api/v1/health" >/dev/null; then
        break
    fi
    if ! kill -0 "${SERVER_PID}" >/dev/null 2>&1; then
        cat "${SERVER_LOG}" >&2
        exit 1
    fi
    sleep 0.25
done

curl --fail --silent "${BASE_URL}/" | grep -q "Better conversations"
curl --fail --silent "${BASE_URL}/index.html" | grep -q "Better conversations"
curl --fail --silent "${BASE_URL}/dashboard.html" | grep -q "Live conversation workspace"
curl --fail --silent "${BASE_URL}/architecture.html" | grep -q "Interactive architecture"
curl --fail --silent "${BASE_URL}/api/v1/conversations" | grep -q "conv_support_bluebird"

ANALYSIS_RESPONSE="$(
    curl --fail --silent \
        -X POST "${BASE_URL}/api/v1/analyze" \
        -H "Content-Type: application/json" \
        -d '{
          "mode": "support",
          "turns": [
            {
              "speaker": "Case participant",
              "role": "participant",
              "text": "This is blocking our deadline. When will it be fixed?"
            },
            {
              "speaker": "Case operator",
              "role": "operator",
              "text": "I am checking the worker now."
            }
          ]
        }'
)"
printf '%s' "${ANALYSIS_RESPONSE}" | grep -q '"manual_only"'
printf '%s' "${ANALYSIS_RESPONSE}" | grep -q '"can_auto_send":false'

echo "Smoke test passed on ${BASE_URL}."
