"""Tests for plugin.json validity and file reference integrity."""

import json
import pathlib
import re

import pytest

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent


def test_plugin_json_exists(repo_root):
    assert (repo_root / ".claude-plugin" / "plugin.json").exists()


def test_plugin_json_valid(plugin_json):
    assert "name" in plugin_json
    assert "version" in plugin_json
    assert "description" in plugin_json
    assert "skills" in plugin_json
    assert "agents" in plugin_json


def test_plugin_version_is_semver(plugin_json):
    assert re.match(r"^\d+\.\d+\.\d+$", plugin_json["version"])


def test_all_skill_files_exist(repo_root, plugin_json):
    for skill_path in plugin_json["skills"]:
        full = repo_root / skill_path
        assert full.exists(), f"Skill file missing: {skill_path}"


def test_all_agent_files_exist(repo_root, plugin_json):
    for agent_path in plugin_json["agents"]:
        full = repo_root / agent_path
        assert full.exists(), f"Agent file missing: {agent_path}"


def test_mcp_json_exists(repo_root):
    assert (repo_root / ".mcp.json").exists()


def test_mcp_json_has_pqc_server(mcp_json):
    assert "mcpServers" in mcp_json
    assert "pqc" in mcp_json["mcpServers"]
    server = mcp_json["mcpServers"]["pqc"]
    assert server["type"] == "stdio"
    assert "command" in server
