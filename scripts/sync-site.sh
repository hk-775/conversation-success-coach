#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SOURCE_DIR="${ROOT_DIR}/src/conversation_success_coach/web/"
TARGET_DIR="${ROOT_DIR}/site/"

mkdir -p "${TARGET_DIR}"
rsync -a --delete "${SOURCE_DIR}" "${TARGET_DIR}"
echo "Static site synchronized from the served web source."

