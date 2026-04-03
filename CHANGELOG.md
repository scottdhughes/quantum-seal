# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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

[0.2.0]: https://github.com/scottdhughes/quantum-seal/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/scottdhughes/quantum-seal/releases/tag/v0.1.0
