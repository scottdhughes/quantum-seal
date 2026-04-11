# Contributing to Quantum Seal

Thank you for your interest in contributing!

## Structure

Quantum Seal is a Claude Code plugin. All cryptographic operations are handled by the [post-quantum-mcp](https://github.com/scottdhughes/post-quantum-mcp) MCP server — this repo contains only skills (markdown procedures), an autonomous agent, and plugin configuration.

## Compatibility Matrix

| Component | Version | Notes |
|-----------|---------|-------|
| **post-quantum-mcp** | see [`.engine-pin`](.engine-pin) | Single source of truth — read by CI and `scripts/launch-engine.sh`. Update this file to bump the engine. |
| **liboqs** (C library) | 0.15.0 | liboqs-python 0.14.1 emits a cosmetic `UserWarning` against 0.15.x — documented and accepted upstream |
| **liboqs-python** | 0.14.1 | PyPI package — latest available; no 0.15.x binding shipped yet |
| **pytest-asyncio** | latest | Required for async behavioral tests |
| **Python** | 3.12 | CI-tested |

## Runtime: post-quantum-mcp engine

When Claude Code starts the `pqc` MCP server, it runs `scripts/launch-engine.sh`, which:

1. Resolves the engine path: `$PQC_MCP_PATH` if set, else `$HOME/post-quantum-mcp`.
2. Checks the path exists and `run.sh` is present and executable.
3. Compares the engine's `git describe --tags` against [`.engine-pin`](.engine-pin).
4. **Fatal** if any of the above fail. Errors are written to stderr and surfaced in Claude Code's MCP debug logs (`claude --debug`).
5. exec's `run.sh` so the engine becomes the live MCP child (no extra layer in the pipe).

If you're doing engine development and your local checkout is intentionally ahead of the pin, set `ALLOW_ENGINE_DRIFT=1` in the env before launching Claude Code. The launcher will still print the drift warning to stderr but won't block startup.

To bump the engine version: edit `.engine-pin`, then `git -C $HOME/post-quantum-mcp checkout <new-tag>`. CI reads the same file at `Read engine pin from .engine-pin` step.

## Development

### Quick start

One command runs lint, all tests, and prints whether the crypto path was actually exercised:

```bash
./scripts/verify.sh
```

On first run, the script auto-creates `./.venv/` (already gitignored) seeded from `python3` and installs `pytest`, `pytest-asyncio`, and `ruff` into it. If you have a venv already active (`$VIRTUAL_ENV` set), it uses that instead. To seed from a specific interpreter: `PYTHON=/path/to/python3.12 ./scripts/verify.sh`.

It then runs CI-equivalent lint and structural checks locally, plus behavioral tests when `liboqs-python` and `cryptography` are both importable. It does **not** build liboqs from source — see "Behavioral integration tests" below for the full setup CI uses. **Exits non-zero** if either dependency is absent (behavioral tests would skip) so degraded coverage cannot masquerade as a clean run. Override with `ALLOW_DEGRADED=1 ./scripts/verify.sh` for pure-markdown changes where you accept structural-only confidence.

Exit codes: `0` clean, `1` lint or test failure, `2` dependency install failure, `3` degraded coverage (no liboqs).

### Prerequisites

- Python 3.10+
- pytest (`pip install pytest`)
- ruff (`pip install ruff`) — for lint/format checks

### Test Tiers

**1. Structural tests (no dependencies needed):**
```bash
python -m pytest tests/test_plugin_structure.py tests/test_skill_frontmatter.py tests/test_consistency.py -v
```
Validates plugin structure, skill frontmatter, and cross-reference consistency.

**2. Behavioral integration tests (requires liboqs + engine):**
```bash
pip install liboqs-python==0.14.1 hypothesis pytest-asyncio
pip install git+https://github.com/scottdhughes/post-quantum-mcp.git@v0.9.0
LD_LIBRARY_PATH=/path/to/liboqs/lib python -m pytest tests/test_behavioral_mcp.py -v
```
Exercises full crypto flows: keygen → seal → verify → open, replay cache, key-handle policy.
**Skipped automatically if liboqs is not installed.**

**3. Lint and formatting:**
```bash
ruff check tests/
ruff format --check tests/
```

### Understanding test results

| Result | Meaning |
|--------|---------|
| All passing | Full confidence |
| Behavioral skipped | liboqs not installed — structural only (degraded confidence) |
| Lint not run | ruff not installed — formatting not verified |

CI always runs all three tiers. Local runs may skip behavioral tests if liboqs is absent.

### Adding a Skill

1. Create `skills/<skill-name>.md` with YAML frontmatter (`name`, `description`)
2. Add the path to `plugin.json` → `skills` array
3. Mention the skill in `README.md`
4. Run tests to verify consistency

### Adding an Agent

1. Create `agents/<agent-name>.md` with frontmatter (`name`, `description`, `model`, `tools`)
2. Add the path to `plugin.json` → `agents` array
3. Mention the agent in `README.md`
4. Run tests to verify consistency

## Commits

Use [Conventional Commits](https://www.conventionalcommits.org/):
- `feat:` new skill or agent
- `fix:` bug fix in a procedure
- `docs:` documentation changes
- `test:` test additions or fixes
- `ci:` CI pipeline changes

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
