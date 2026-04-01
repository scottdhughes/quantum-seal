# Contributing to Quantum Seal

Thank you for your interest in contributing!

## Structure

Quantum Seal is a Claude Code plugin. All cryptographic operations are handled by the [post-quantum-mcp](https://github.com/scottdhughes/post-quantum-mcp) MCP server — this repo contains only skills (markdown procedures), an autonomous agent, and plugin configuration.

## Development

### Prerequisites

- Python 3.10+ (for running tests)
- pytest (`pip install pytest`)

### Running Tests

```bash
python -m pytest tests/ -v
```

Tests validate:
- Plugin structure (plugin.json schema, file references)
- Skill/agent frontmatter (required fields, description quality)
- Cross-reference consistency (README ↔ skills, no orphan files)

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
