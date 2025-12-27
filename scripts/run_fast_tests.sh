#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

python "${ROOT_DIR}/scripts/validate_shortforms.py"
pytest "${ROOT_DIR}/tests/security_test.py" "${ROOT_DIR}/tests/north_star_eval.py" -m "not integration" -q
