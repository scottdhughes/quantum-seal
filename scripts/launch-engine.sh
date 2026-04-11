#!/usr/bin/env bash
# Preflight launcher for the post-quantum-mcp engine.
#
# Invoked from .mcp.json via:
#   bash -c "${CLAUDE_PROJECT_DIR}/scripts/launch-engine.sh"
#
# CLAUDE_PROJECT_DIR is set by Claude Code for project-level MCP servers
# (project .mcp.json files). NOT the same as CLAUDE_PLUGIN_ROOT, which is
# only set for installed plugins from a marketplace — using PLUGIN_ROOT
# in a project .mcp.json silently expands to empty and breaks the path.
#
# Validates that the engine checkout exists, run.sh is present and
# executable, and the engine version matches the pin in .engine-pin.
# Then exec's run.sh so the engine becomes the live MCP child process
# (no extra layer in the pipe).
#
# Failure modes (all messages go to stderr so Claude Code's MCP debug
# logs surface them — MCP child stderr is captured and shown on error):
#   1 - engine path missing, run.sh missing, run.sh not executable, or
#       .engine-pin missing (fatal — engine cannot start)
#   2 - engine version differs from .engine-pin (fatal unless
#       ALLOW_ENGINE_DRIFT=1 is set, which mirrors verify.sh's
#       ALLOW_DEGRADED idiom)
#
# Path resolution: if PQC_MCP_PATH is set in the env, it wins. Otherwise
# defaults to $HOME/post-quantum-mcp. The .mcp.json no longer sets
# PQC_MCP_PATH to "" — that empty-string trick prevented user shell
# overrides from reaching the child.

set -uo pipefail

PLUGIN_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
ALLOW_ENGINE_DRIFT="${ALLOW_ENGINE_DRIFT:-0}"

if [ -n "${PQC_MCP_PATH:-}" ]; then
  ENGINE_PATH="$PQC_MCP_PATH"
else
  ENGINE_PATH="$HOME/post-quantum-mcp"
fi

err() { printf '[launch-engine] %s\n' "$1" >&2; }

if [ ! -d "$ENGINE_PATH" ]; then
  err "FATAL: engine path does not exist: $ENGINE_PATH"
  err "  set PQC_MCP_PATH to your post-quantum-mcp checkout, or clone it:"
  err "    git clone https://github.com/scottdhughes/post-quantum-mcp.git \"$HOME/post-quantum-mcp\""
  exit 1
fi

RUN_SH="$ENGINE_PATH/run.sh"
if [ ! -f "$RUN_SH" ]; then
  err "FATAL: run.sh not found at $RUN_SH"
  err "  this checkout may not be a post-quantum-mcp repo, or may predate v0.4"
  exit 1
fi
if [ ! -x "$RUN_SH" ]; then
  err "FATAL: run.sh exists but is not executable: $RUN_SH"
  err "  fix with: chmod +x \"$RUN_SH\""
  exit 1
fi

PIN_FILE="$PLUGIN_ROOT/.engine-pin"
if [ ! -f "$PIN_FILE" ]; then
  err "FATAL: .engine-pin not found at $PIN_FILE"
  err "  plugin install is incomplete or corrupted"
  exit 1
fi
EXPECTED_PIN="$(tr -d '[:space:]' < "$PIN_FILE")"
if [ -z "$EXPECTED_PIN" ]; then
  err "FATAL: .engine-pin is empty at $PIN_FILE"
  exit 1
fi

ACTUAL_PIN="$(git -C "$ENGINE_PATH" describe --tags 2>/dev/null || echo "unknown")"
if [ "$ACTUAL_PIN" != "$EXPECTED_PIN" ]; then
  err "ENGINE DRIFT: expected $EXPECTED_PIN, found $ACTUAL_PIN at $ENGINE_PATH"
  err "  Fix one of:"
  err "    (a) cd \"$ENGINE_PATH\" && git checkout $EXPECTED_PIN"
  err "    (b) update .engine-pin to match (and bump CI accordingly)"
  err "    (c) set ALLOW_ENGINE_DRIFT=1 to bypass (engine dev work only)"
  if [ "$ALLOW_ENGINE_DRIFT" != "1" ]; then
    exit 2
  fi
  err "  ALLOW_ENGINE_DRIFT=1 set — proceeding with drift"
fi

# --check-only: verify wiring without launching the engine. Useful for
# verify.sh integration (item 3 design call #2, deferred — but the hook
# is here if/when we want to wire it up).
if [ "${1:-}" = "--check-only" ]; then
  err "OK: $ENGINE_PATH ($ACTUAL_PIN)"
  exit 0
fi

err "engine: $ENGINE_PATH ($ACTUAL_PIN)"
exec "$RUN_SH" "$@"
