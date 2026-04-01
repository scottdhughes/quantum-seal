# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
