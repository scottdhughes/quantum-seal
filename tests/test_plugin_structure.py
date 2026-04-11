"""Tests for plugin.json validity and file reference integrity."""

import os
import pathlib
import re


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


def test_mcp_json_uses_launch_engine_script(mcp_json):
    # The pqc server must invoke the preflight launcher, not run.sh directly,
    # so engine path/version drift is caught before the engine starts.
    args = mcp_json["mcpServers"]["pqc"].get("args", [])
    joined = " ".join(args)
    assert "scripts/launch-engine.sh" in joined, (
        "pqc MCP server must invoke scripts/launch-engine.sh "
        "(see CONTRIBUTING.md → Runtime: post-quantum-mcp engine)"
    )


def test_engine_pin_file_exists_and_valid(repo_root):
    pin_file = repo_root / ".engine-pin"
    assert pin_file.exists(), ".engine-pin missing — single source of truth for engine version"
    pin = pin_file.read_text().strip()
    assert pin, ".engine-pin is empty"
    assert re.match(r"^v\d+\.\d+\.\d+", pin), f".engine-pin has unexpected format: {pin!r}"


def test_launch_engine_script_exists_and_executable(repo_root):
    script = repo_root / "scripts" / "launch-engine.sh"
    assert script.exists(), "scripts/launch-engine.sh missing"
    assert os.access(script, os.X_OK), "scripts/launch-engine.sh is not executable"
