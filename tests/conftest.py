"""Shared fixtures for quantum-seal tests."""

import json
import pathlib

import pytest

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent


@pytest.fixture
def repo_root():
    return REPO_ROOT


@pytest.fixture
def plugin_json(repo_root):
    path = repo_root / ".claude-plugin" / "plugin.json"
    return json.loads(path.read_text())


@pytest.fixture
def mcp_json(repo_root):
    path = repo_root / ".mcp.json"
    return json.loads(path.read_text())
