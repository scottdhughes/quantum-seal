#!/usr/bin/env bash
# Local verification entry point. Runs CI-equivalent lint and structural
# checks, plus behavioral tests when the liboqs stack is importable.
#
# This does NOT install liboqs from source the way CI does — see
# CONTRIBUTING.md "Behavioral integration tests" for full setup.
#
# Environment isolation: if a venv is already active ($VIRTUAL_ENV set),
# the script uses it. Otherwise it auto-creates/uses ./.venv/ at the repo
# root, seeded from $PYTHON (default: python3). This sidesteps PEP 668
# externally-managed-environment errors on Homebrew/uv-managed Pythons.
#
# Exit codes:
#   0 - clean (or ALLOW_DEGRADED=1 override)
#   1 - lint or test failure
#   2 - prerequisite/install failure (Python version, venv, pip)
#   3 - degraded coverage (liboqs-python or cryptography missing)
set -uo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT"

ALLOW_DEGRADED="${ALLOW_DEGRADED:-0}"
SEED_PYTHON="${PYTHON:-python3}"

bold() { printf '\033[1m%s\033[0m' "$1"; }
red()  { printf '\033[31m%s\033[0m' "$1"; }
yel()  { printf '\033[33m%s\033[0m' "$1"; }
grn()  { printf '\033[32m%s\033[0m' "$1"; }

step() { printf '\n%s %s\n' "$(bold '==>')" "$1"; }
ok()   { printf '   %s %s\n' "$(grn '✓')" "$1"; }
warn() { printf '   %s %s\n' "$(yel '⚠')" "$1"; }
fail() { printf '   %s %s\n' "$(red '✗')" "$1"; }

step "Resolving Python environment"
# Precedence: active $VIRTUAL_ENV > existing .venv/ > bootstrap new .venv/
# from $SEED_PYTHON. We always end up running everything through a venv
# Python so pip installs work regardless of PEP 668.
if [ -n "${VIRTUAL_ENV:-}" ] && [ -x "$VIRTUAL_ENV/bin/python" ]; then
  PYTHON="$VIRTUAL_ENV/bin/python"
  ok "using active venv at $VIRTUAL_ENV"
elif [ -x ".venv/bin/python" ]; then
  PYTHON="$REPO_ROOT/.venv/bin/python"
  ok "using existing .venv/"
else
  if ! command -v "$SEED_PYTHON" >/dev/null 2>&1; then
    fail "$SEED_PYTHON not found. Set PYTHON=/path/to/python3.10+ and re-run"
    exit 2
  fi
  if ! "$SEED_PYTHON" -c "import sys; sys.exit(0 if sys.version_info >= (3,10) else 1)" 2>/dev/null; then
    fail "$SEED_PYTHON is $("$SEED_PYTHON" --version 2>&1) — need 3.10+ to seed venv"
    fail "set PYTHON=/path/to/python3.10+ and re-run"
    exit 2
  fi
  ok "creating .venv/ from $("$SEED_PYTHON" --version 2>&1)"
  "$SEED_PYTHON" -m venv .venv || { fail "venv creation failed"; exit 2; }
  PYTHON="$REPO_ROOT/.venv/bin/python"
fi

step "Checking Python version"
if ! "$PYTHON" -c "import sys; sys.exit(0 if sys.version_info >= (3,10) else 1)" 2>/dev/null; then
  fail "Python 3.10+ required (got: $("$PYTHON" --version 2>&1 || echo unknown))"
  exit 2
fi
ok "$("$PYTHON" --version 2>&1)"

ensure_pkg() {
  local mod="$1" pkg="$2"
  if ! "$PYTHON" -c "import $mod" >/dev/null 2>&1; then
    "$PYTHON" -m pip install --quiet "$pkg" || { fail "failed to install $pkg"; exit 2; }
    ok "installed $pkg"
  else
    ok "$pkg already present"
  fi
}

step "Installing dev dependencies"
ensure_pkg pytest          pytest
ensure_pkg pytest_asyncio  pytest-asyncio
ensure_pkg ruff            ruff

LINT_FAIL=0
TEST_FAIL=0

step "Lint (ruff check + format)"
if ! "$PYTHON" -m ruff check tests/; then
  LINT_FAIL=1
  fail "ruff check failed"
fi
if ! "$PYTHON" -m ruff format --check tests/; then
  LINT_FAIL=1
  fail "ruff format failed"
fi
[ $LINT_FAIL -eq 0 ] && ok "lint clean"

step "Detecting crypto coverage"
# Pre-flight every importorskip in tests/test_behavioral_mcp.py. If any
# fail, the behavioral module skips entirely and the FULL banner would lie.
COVERAGE="full"
MISSING=""
for mod in oqs cryptography; do
  if ! "$PYTHON" -c "import $mod" >/dev/null 2>&1; then
    COVERAGE="degraded"
    MISSING="$MISSING $mod"
    warn "$mod not importable"
  fi
done
[ "$COVERAGE" = "full" ] && ok "oqs + cryptography importable — full behavioral coverage available"

step "Running tests"
if ! "$PYTHON" -m pytest tests/ -rs -q; then
  TEST_FAIL=1
  fail "pytest reported failures"
fi

# Banner: always print, regardless of pass/fail above. The user needs to
# see code-health AND coverage-state in a single run, not two trips.
printf '\n'
printf '============================================================\n'
if [ "$COVERAGE" = "full" ]; then
  printf '  %s FULL — crypto behavioral tests exercised\n' "$(grn '✓')"
else
  printf '  %s STRUCTURAL ONLY — crypto path NOT exercised\n' "$(yel '⚠')"
fi
printf '============================================================\n'

if [ "$COVERAGE" = "degraded" ]; then
  printf '  Missing:%s\n' "$MISSING"
  printf '  Behavioral tests for the hybrid PQC envelopes were\n'
  printf '  SKIPPED. A green run here does NOT guarantee the\n'
  printf '  crypto engine still works.\n\n'
  printf '  Enable full coverage:\n'
  printf '    see CONTRIBUTING.md → "Behavioral integration tests"\n\n'
fi

# Exit precedence: code-broken (1) > coverage-gap (3) > clean (0).
# Lint and test failures are more urgent than missing coverage — fix the
# code first, then come back for coverage.
if [ $LINT_FAIL -ne 0 ] || [ $TEST_FAIL -ne 0 ]; then
  fail "exiting 1 (lint or test failures)"
  exit 1
fi
if [ "$COVERAGE" = "degraded" ]; then
  if [ "$ALLOW_DEGRADED" = "1" ]; then
    warn "exiting 0 because ALLOW_DEGRADED=1"
    exit 0
  else
    fail "exiting 3 (degraded coverage). Set ALLOW_DEGRADED=1 to override."
    exit 3
  fi
fi
ok "exiting 0 (clean, full coverage)"
exit 0
