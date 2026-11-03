#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${PROJECT_ROOT}"

echo "============================================================"
echo "ImporJaga MVP v1.1 — Canonical Verification Runner"
echo "Root: ${PROJECT_ROOT}"
echo "============================================================"

# 1. Protected Files Integrity Check
echo "--> [1/4] Checking protected files integrity..."
if [ ! -f "docs/MVP-v1.1.md" ]; then
    echo "ERROR: docs/MVP-v1.1.md missing!" >&2
    exit 1
fi
if [ ! -f "tests/test_acceptance_protected.py" ]; then
    echo "ERROR: tests/test_acceptance_protected.py missing!" >&2
    exit 1
fi
echo "Protected specification and acceptance tests verified present."

# 2. Ruff Linter & Syntax Check
echo "--> [2/4] Running Ruff linter..."
"${PROJECT_ROOT}/.venv/bin/ruff" check src tests

# 3. Protected Acceptance Tests Execution
echo "--> [3/4] Running Protected Acceptance Test Suite (A01-A18)..."
PYTHONPATH="${PROJECT_ROOT}" "${PROJECT_ROOT}/.venv/bin/pytest" tests/test_acceptance_protected.py -v

# 4. Full Integration Tests Execution
echo "--> [4/5] Running Full Test Suite..."
PYTHONPATH="${PROJECT_ROOT}" "${PROJECT_ROOT}/.venv/bin/pytest" tests/ -v

# 5. Frontend Build Verification
echo "--> [5/5] Checking Frontend TypeScript & Production Build..."
if [ -d "${PROJECT_ROOT}/frontend" ]; then
    (cd "${PROJECT_ROOT}/frontend" && npm run build)
fi

echo "============================================================"
echo "ALL VERIFICATION CHECKS PASSED (100% GREEN)"
echo "============================================================"
