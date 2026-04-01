"""Tests for skill and agent markdown frontmatter."""

import pathlib
import re

import pytest

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent

SKILL_DIR = REPO_ROOT / "skills"
AGENT_DIR = REPO_ROOT / "agents"

FRONTMATTER_RE = re.compile(
    r"^---\s*\n(.*?)\n---\s*\n",
    re.DOTALL,
)


def _parse_frontmatter(path: pathlib.Path) -> dict[str, str]:
    """Extract YAML-like frontmatter as key: value pairs."""
    text = path.read_text()
    match = FRONTMATTER_RE.match(text)
    assert match, f"No frontmatter block in {path.name}"
    pairs = {}
    for line in match.group(1).strip().splitlines():
        if ":" in line:
            key, _, value = line.partition(":")
            pairs[key.strip()] = value.strip()
    return pairs


def skill_files():
    return sorted(SKILL_DIR.glob("*.md"))


def agent_files():
    return sorted(AGENT_DIR.glob("*.md"))


@pytest.mark.parametrize("path", skill_files(), ids=lambda p: p.stem)
def test_skill_has_name(path):
    fm = _parse_frontmatter(path)
    assert "name" in fm, f"{path.name} missing 'name' in frontmatter"
    assert len(fm["name"]) > 0


@pytest.mark.parametrize("path", skill_files(), ids=lambda p: p.stem)
def test_skill_has_description(path):
    fm = _parse_frontmatter(path)
    assert "description" in fm, f"{path.name} missing 'description' in frontmatter"
    assert len(fm["description"]) > 10, "Description too short to be useful"


@pytest.mark.parametrize("path", skill_files(), ids=lambda p: p.stem)
def test_skill_has_body_content(path):
    text = path.read_text()
    body = FRONTMATTER_RE.sub("", text).strip()
    assert len(body) > 100, f"{path.name} body too short ({len(body)} chars)"


@pytest.mark.parametrize("path", agent_files(), ids=lambda p: p.stem)
def test_agent_has_name(path):
    fm = _parse_frontmatter(path)
    assert "name" in fm, f"{path.name} missing 'name'"


@pytest.mark.parametrize("path", agent_files(), ids=lambda p: p.stem)
def test_agent_has_description(path):
    fm = _parse_frontmatter(path)
    assert "description" in fm, f"{path.name} missing 'description'"


@pytest.mark.parametrize("path", agent_files(), ids=lambda p: p.stem)
def test_agent_has_model(path):
    fm = _parse_frontmatter(path)
    assert "model" in fm, f"{path.name} missing 'model'"


@pytest.mark.parametrize("path", agent_files(), ids=lambda p: p.stem)
def test_agent_has_tools(path):
    fm = _parse_frontmatter(path)
    assert "tools" in fm, f"{path.name} missing 'tools'"
