#!/usr/bin/env bash
# local-ci.sh: One-click local CI runner for document_converter
# Runs locally in Antigravity Terminal with zero cloud spend.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

BOLD="\033[1m"
GREEN="\033[0;32m"
YELLOW="\033[0;33m"
RED="\033[0;31m"
CYAN="\033[0;36m"
RESET="\033[0m"

log_info()  { echo -e "${CYAN}${BOLD}[LOCAL-CI]${RESET} $*"; }
log_step()  { echo -e "\n${BOLD}${CYAN}==>${RESET} ${BOLD}$*${RESET}"; }
log_pass()  { echo -e "${GREEN}${BOLD}[PASS]${RESET} $*"; }
log_fail()  { echo -e "${RED}${BOLD}[FAIL]${RESET} $*"; }
log_warn()  { echo -e "${YELLOW}${BOLD}[WARN]${RESET} $*"; }

VENV_PYTHON="${REPO_ROOT}/.venv/bin/python"
VENV_PYTEST="${REPO_ROOT}/.venv/bin/pytest"
VENV_AUDIT="${REPO_ROOT}/.venv/bin/pip-audit"
VENV_LICENSES="${REPO_ROOT}/.venv/bin/pip-licenses"

if [[ ! -x "${VENV_PYTHON}" ]]; then
  log_fail "Virtual environment not found at .venv. Please create one with python3 -m venv .venv."
  exit 1
fi

MODE="fast"
if [[ $# -gt 0 ]]; then
  case "$1" in
    --fast) MODE="fast" ;;
    --audit) MODE="audit" ;;
    --release) MODE="release" ;;
    --all) MODE="all" ;;
    -h|--help)
      echo "Usage: $(basename "$0") [--fast | --audit | --release | --all]"
      exit 0
      ;;
    *)
      log_fail "Unknown option: $1"
      exit 1
      ;;
  esac
fi

run_fast() {
  log_step "Stage 1: Unit & Functional Tests"
  log_info "Running pytest suite..."
  "${VENV_PYTEST}" tests/ -m "not slow" -k "not test_release_packaging"
  log_pass "Fast test suite passed."
}

run_audit() {
  log_step "Stage 2: Security & License Audit (Fail-Closed)"
  if ! command -v gitleaks >/dev/null 2>&1; then
    log_fail "Security scanner 'gitleaks' is required for audit but not found in PATH (fail-closed)."
    exit 1
  fi
  log_info "Running Gitleaks secret scan..."
  gitleaks detect --source . --verbose --redact
  log_pass "Gitleaks clean."

  if [[ ! -x "${VENV_LICENSES}" ]]; then
    log_fail "License checker 'pip-licenses' is required for audit but not found in ${REPO_ROOT}/.venv (fail-closed)."
    exit 1
  fi
  log_info "Checking third-party licenses for viral infectivity (AGPL/GPL)..."
  "${VENV_LICENSES}" --fail-on="AGPL;GPLv3"
  log_pass "License check passed."
}

run_release() {
  log_step "Stage 3: Release Packaging Runtime Tests (Strict)"
  local release_python="build/private-release/venv-pdf/bin/python"
  if [[ ! -f "${release_python}" ]]; then
    log_fail "Release packaging virtual environment missing: ${release_python}. Tests cannot run. Run scripts/packaging/bootstrap_macos.sh first."
    exit 1
  fi
  log_info "Running packaging verification..."
  "${release_python}" -I -m unittest discover -s tests -p test_release_packaging.py -v
  log_pass "Release runtime verification passed."
}

START_TIME=$(date +%s)
log_info "Starting document_converter local CI in mode: [${MODE}]"

case "${MODE}" in
  fast) run_fast ;;
  audit) run_audit ;;
  release) run_release ;;
  all)
    run_fast
    run_audit
    run_release
    ;;
esac

END_TIME=$(date +%s)
log_step "Summary"
log_pass "Completed [${MODE}] in $((END_TIME - START_TIME))s."
