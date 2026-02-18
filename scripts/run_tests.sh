#!/usr/bin/env bash
# run_tests.sh — install deps (if needed) and run the full test suite.
# Usage:
#   ./scripts/run_tests.sh              # all tests
#   ./scripts/run_tests.sh unit         # unit tests only
#   ./scripts/run_tests.sh integration  # integration tests only
#   ./scripts/run_tests.sh --cov        # with coverage report

set -euo pipefail

SCOPE="${1:-}"
COV_FLAG=""

if [[ "$*" == *"--cov"* ]]; then
  COV_FLAG="--cov=. --cov-report=term-missing --cov-report=html:htmlcov"
fi

# Verify we're inside the project root
if [[ ! -f "pytest.ini" ]]; then
  echo "Error: run this script from the project root directory." >&2
  exit 1
fi

echo "────────────────────────────────────────"
echo " HumanifyAI Test Runner"
echo "────────────────────────────────────────"

case "$SCOPE" in
  unit)
    echo "Running unit tests..."
    pytest tests/unit $COV_FLAG
    ;;
  integration)
    echo "Running integration tests..."
    pytest tests/integration $COV_FLAG
    ;;
  *)
    echo "Running all tests..."
    pytest $COV_FLAG
    ;;
esac

echo "────────────────────────────────────────"
echo " Done."