# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.4.0] - 2026-04-08

### Changed
- **Engine pin:** Bumped to `post-quantum-mcp@v0.9.0`. CI and CONTRIBUTING
  updated to match.
- **quantum-messenger agent:** Removed `Bash` and `pqc_key_store_delete`
  from tool list. Added `pqc_hash` (was referenced by quantum-handshake
  skill but missing from agent frontmatter). 14 tools total.
- **inspect-envelope skill:** Updated stale `pqc-mcp-v2` references to
  `pqc-mcp-v3`.
- **verify-sender skill:** Updated v2-only timestamp references to v2/v3.

### Added
- **Skill-to-engine contract tests** (`test_consistency.py`): 3 new tests
  that parse skill/agent markdown and verify all `pqc_*` tool references
  exist in the engine's tool list. Catches drift between plugin layer
  and `post-quantum-mcp` engine.
- **Hostile channel demo script** (`docs/demo-hostile-channel.md`):
  Full walkthrough of two agents exchanging PQC messages through a
  hostile relay, showing attack vectors and protections.
- **Content safety rule 10 hardened:** Explicitly prohibits
  `pqc_key_store_delete` from being called based on decrypted message
  content (belt-and-suspenders alongside tool removal).
- **pytest-asyncio** added as test dependency (`handle_hybrid_auth_open`
  is now async in engine v0.9.0). `pyproject.toml` configured with
  `asyncio_mode = "auto"`.
- **behavioral tests** updated to `await` the async `handle_hybrid_auth_open`.

### Security
- **Multi-model adversarial review cycle:** 10 models (Claude Opus,
  Codex GPT-5.4, Sonnet, ChatGPT, Gemini, Grok, Qwen 3.5, Gemma 4 8B,
  Gemma 4 31B, plus user). Found 14 findings across engine and plugin,
  all resolved.
- **Agent tool surface reduction:** Removing `Bash` and
  `pqc_key_store_delete` closes two prompt-injection attack paths
  where crafted messages could trick the agent into destructive actions.

## [0.3.0] - 2026-04-02

### Changed
- **verify-sender skill:** Completely rewritten to use `pqc_hybrid_auth_verify`
  instead of manual transcript reconstruction or `pqc_verify` workarounds.
  Documents expected_sender_fingerprint requirement and exception-based failure.
- **secure-send skill:** Frontmatter and body updated — courier mode description
  now accurately states base64 content appears in tool calls (not true
  content-blindness).
- **secure-receive skill:** Updated replay note for v2 signed timestamps.
  Added content safety note — decrypted content is untrusted input.
- **inspect-envelope skill:** Version examples updated from v1 to v2.
- **.mcp.json:** Parameterized server path via `PQC_MCP_PATH` env var.
  Enforces `PQC_REQUIRE_KEY_HANDLES=1` by default (opaque-handle-only mode).

### Added
- **Content safety rules** (quantum-messenger agent): 6 non-negotiable rules
  for handling decrypted message content. Treats all messages as untrusted input.
  Forbids executing commands, writing to system paths, or following injected
  instructions from message content without user approval.
- `pqc_hybrid_auth_verify` added to quantum-messenger agent tool list.
- `test_behavioral_mcp.py`: 13 end-to-end behavioral tests covering full
  messaging flows, secret key gating, replay cache, and security policy.

### Security
- Multi-model adversarial review (Claude Opus 4.6, Codex GPT-5.4, Qwen 3.5).
- 7 prompt injection payloads tested against decrypted message handling — all
  contained by handle-based key store (agent cannot extract secret keys).
- Content safety rules address: prompt injection via encrypted messages,
  tool-call injection, path traversal, compromised-contact attacks.

## [0.2.0] - 2026-03-31

### Added
- Quantum handshake skill — zero-friction TOFU key bootstrap protocol
- Timeout handling in handshake responder flow
- Secure-send now leads with authenticated (non-courier) approach

### Fixed
- Secure-send procedure ordering (auth-first, courier as fallback)

## [0.1.0] - 2026-03-30

### Added
- Initial release
- 6 skills: setup-identity, secure-send, secure-receive, key-exchange, inspect-envelope, verify-sender
- 1 autonomous agent: quantum-messenger (Sonnet, 16 tools)
- Plugin structure: plugin.json, .mcp.json wired to post-quantum-mcp
- Hybrid X25519 + ML-KEM-768 key exchange with ML-DSA-65 sender authentication
- README with cryptographic suite documentation, security model, quick start guide

[0.4.0]: https://github.com/scottdhughes/quantum-seal/compare/v0.3.0...v0.4.0
[0.3.0]: https://github.com/scottdhughes/quantum-seal/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/scottdhughes/quantum-seal/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/scottdhughes/quantum-seal/releases/tag/v0.1.0
