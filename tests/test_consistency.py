"""Cross-reference consistency tests for quantum-seal plugin."""

import json
import pathlib
import re

import pytest

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent


@pytest.fixture
def all_skill_names():
    """Extract skill names from frontmatter."""
    names = []
    for path in sorted((REPO_ROOT / "skills").glob("*.md")):
        for line in path.read_text().splitlines():
            if line.startswith("name:"):
                names.append(line.split(":", 1)[1].strip())
                break
    return names


@pytest.fixture
def readme_text():
    return (REPO_ROOT / "README.md").read_text()


def test_readme_exists():
    assert (REPO_ROOT / "README.md").exists()


def test_readme_mentions_all_skills(all_skill_names, readme_text):
    for name in all_skill_names:
        assert name in readme_text, f"README doesn't mention skill '{name}'"


def test_readme_mentions_agent(readme_text):
    assert "quantum-messenger" in readme_text


def test_license_exists():
    assert (REPO_ROOT / "LICENSE").exists()


def test_gitignore_exists():
    assert (REPO_ROOT / ".gitignore").exists()


def test_no_orphan_skill_files():
    """Every .md in skills/ should be referenced in plugin.json."""
    plugin = json.loads((REPO_ROOT / ".claude-plugin" / "plugin.json").read_text())
    registered = {pathlib.Path(p).name for p in plugin["skills"]}
    actual = {p.name for p in (REPO_ROOT / "skills").glob("*.md")}
    orphans = actual - registered
    assert not orphans, f"Orphan skill files not in plugin.json: {orphans}"


def test_no_orphan_agent_files():
    """Every .md in agents/ should be referenced in plugin.json."""
    plugin = json.loads((REPO_ROOT / ".claude-plugin" / "plugin.json").read_text())
    registered = {pathlib.Path(p).name for p in plugin["agents"]}
    actual = {p.name for p in (REPO_ROOT / "agents").glob("*.md")}
    orphans = actual - registered
    assert not orphans, f"Orphan agent files not in plugin.json: {orphans}"


# ═══════════════════════════════════════════════
# Skill-to-engine contract tests
# ═══════════════════════════════════════════════

# Engine tool names — must match pqc_mcp_server/tools.py PQC_TOOLS list.
# Update this set when tools are added/removed from the engine.
ENGINE_TOOLS = frozenset(
    {
        "pqc_list_algorithms",
        "pqc_algorithm_info",
        "pqc_generate_keypair",
        "pqc_encapsulate",
        "pqc_decapsulate",
        "pqc_sign",
        "pqc_verify",
        "pqc_hash",
        "pqc_security_analysis",
        "pqc_hybrid_keygen",
        "pqc_hybrid_encap",
        "pqc_hybrid_decap",
        "pqc_hybrid_seal",
        "pqc_hybrid_open",
        "pqc_hybrid_auth_seal",
        "pqc_hybrid_auth_open",
        "pqc_hybrid_auth_verify",
        "pqc_fingerprint",
        "pqc_envelope_inspect",
        "pqc_benchmark",
        "pqc_key_store_save",
        "pqc_key_store_load",
        "pqc_key_store_list",
        "pqc_key_store_delete",
    }
)


# Field/parameter names that start with pqc_ but are NOT tool names.
# These appear in skill prose as data fields, not tool invocations.
_PQC_NON_TOOL_NAMES = frozenset(
    {
        "pqc_ciphertext",
        "pqc_ciphertext_size",
        "pqc_key_fingerprint",
        "pqc_mcp",
        "pqc_mcp_server",
        "pqc_mcp_v3",
        "pqc_public_key",
        "pqc_secret_key",
    }
)


def _extract_pqc_tools(text: str) -> set[str]:
    """Extract pqc_* tool references from markdown text.

    Returns all pqc_* identifiers except known non-tool field names.
    Typos are intentionally NOT filtered — the test should catch them.
    """
    all_matches = set(re.findall(r"pqc_[a-z_]+", text))
    return all_matches - _PQC_NON_TOOL_NAMES


def test_skill_tools_exist_in_engine():
    """Every pqc_* tool referenced in skills must exist in the engine."""
    missing = {}
    for path in sorted((REPO_ROOT / "skills").glob("*.md")):
        tools = _extract_pqc_tools(path.read_text())
        unknown = tools - ENGINE_TOOLS
        if unknown:
            missing[path.name] = unknown
    assert not missing, f"Skills reference unknown engine tools: {missing}"


def test_agent_tools_exist_in_engine():
    """Every pqc_* tool in agent frontmatter must exist in the engine."""
    missing = {}
    for path in sorted((REPO_ROOT / "agents").glob("*.md")):
        tools = _extract_pqc_tools(path.read_text())
        unknown = tools - ENGINE_TOOLS
        if unknown:
            missing[path.name] = unknown
    assert not missing, f"Agent references unknown engine tools: {missing}"


def test_agent_has_no_bash():
    """quantum-messenger agent should not have Bash in its tool list."""
    agent = (REPO_ROOT / "agents" / "quantum-messenger.md").read_text()
    # Parse frontmatter tools line
    for line in agent.splitlines():
        if line.startswith("tools:"):
            assert '"Bash"' not in line, "Agent should not have Bash access"
            break
