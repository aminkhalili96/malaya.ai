#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
REPORT_DIR="${ROOT_DIR}/reports"

mkdir -p "${REPORT_DIR}"

python "${ROOT_DIR}/scripts/validate_shortforms.py"
python "${ROOT_DIR}/scripts/lexicon_report.py" \
  --json "${REPORT_DIR}/lexicon_report.json" \
  --report "${REPORT_DIR}/lexicon_report.md"
python "${ROOT_DIR}/src/validation/benchmark.py" \
  --json "${REPORT_DIR}/benchmark_report.json" \
  --report "${REPORT_DIR}/benchmark_report.md"

pytest "${ROOT_DIR}/tests" -m "not integration" -q
