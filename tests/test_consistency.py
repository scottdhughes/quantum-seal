"""Cross-reference consistency tests for quantum-seal plugin."""

import json
import pathlib

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
