# Quantum Seal

### Post-Quantum Encrypted Messaging for AI Agents

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Suite](https://img.shields.io/badge/suite-mlkem768--x25519--sha3--256-blue.svg)]()
[![Signature](https://img.shields.io/badge/signature-ML--DSA--65-green.svg)]()

> **Research and Prototyping Only.** Powered by [post-quantum-mcp](https://github.com/scottdhughes/post-quantum-mcp) and [liboqs](https://github.com/open-quantum-safe/liboqs). Not recommended for production use or protecting sensitive data.

---

**Quantum Seal** gives AI agents the ability to send and receive quantum-resistant encrypted, sender-authenticated messages. Generate cryptographic identities, exchange keys, seal messages that only the intended recipient can open, and verify who sent them — all with algorithms designed to withstand both classical and quantum attacks.

Secret keys stay in the MCP server's process memory when using opaque handles.

## Why

Current encryption will be broken by quantum computers running Shor's algorithm. Harvest-now-decrypt-later attacks are already a concern — adversaries recording encrypted traffic today to decrypt when quantum hardware matures.

Quantum Seal uses NIST-standardized post-quantum algorithms so that messages sealed today remain confidential even against future quantum adversaries. The hybrid construction means both classical *and* quantum cryptography must be broken simultaneously.

## How It Works

```
Alice                                    Bob
  |                                       |
  |  1. Generate identity (store_as)      |  1. Generate identity (store_as)
  |     Secret keys: opaque handles       |     Secret keys: opaque handles
  |     Public keys: shareable            |     Public keys: shareable
  |                                       |
  |  2. Exchange identity cards           |
  |  <─────── public keys ───────>        |
  |                                       |
  |  3. Seal message to Bob               |
  |     X25519 + ML-KEM-768 encrypt       |
  |     ML-DSA-65 sign                    |
  |     ──────── envelope ────────>       |
  |                                       |  4. Verify Alice + decrypt
  |                                       |     Check ML-DSA-65 signature FIRST
  |                                       |     Then decrypt with own keys
  |                                       |     → "The quantum computers are coming"
```

## Cryptographic Suite

**Fixed suite: `mlkem768-x25519-sha3-256`**

| Layer | Algorithm | Standard | Security |
|-------|-----------|----------|----------|
| Key exchange | X25519 + ML-KEM-768 | RFC 7748 + FIPS 203 | Hybrid: classical + NIST Level 3 quantum |
| KEM combiner | SHA3-256 | LAMPS composite ML-KEM draft | Context-binding with public values |
| Encryption | AES-256-GCM | NIST | Authenticated encryption with full-header AAD |
| Signature | ML-DSA-65 | FIPS 204 | NIST Level 3 post-quantum |
| Fingerprints | SHA3-256 | NIST | Public key identity binding |
| Nonce | HKDF-derived | RFC 5869 | Deterministic, not transmitted |

## Quick Start

### Prerequisites

- [Claude Code](https://claude.ai/code) (or any MCP-compatible AI agent)
- [post-quantum-mcp](https://github.com/scottdhughes/post-quantum-mcp) checked out at `~/post-quantum-mcp` (override with the `PQC_MCP_PATH` env var). The engine's git-tag must match [`.engine-pin`](.engine-pin).
- [liboqs](https://github.com/open-quantum-safe/liboqs) 0.14.0, vendored at `~/post-quantum-mcp/.vendor/liboqs-0.14/` or installed system-wide. Must match `liboqs-python==0.14.1`.

### Install

```bash
# 1. The plugin (this repo)
git clone https://github.com/scottdhughes/quantum-seal.git ~/quantum-seal

# 2. The crypto engine, pinned to the version in .engine-pin
git clone https://github.com/scottdhughes/post-quantum-mcp.git ~/post-quantum-mcp
git -C ~/post-quantum-mcp checkout "$(cat ~/quantum-seal/.engine-pin)"

# 3. Build liboqs — see post-quantum-mcp's README for the full setup
```

When Claude Code starts the `pqc` MCP server, [`scripts/launch-engine.sh`](scripts/launch-engine.sh) validates the engine path, `run.sh` presence, and engine version against [`.engine-pin`](.engine-pin) before exec'ing the engine. If anything is wrong you'll see `[launch-engine] FATAL: ...` (or `ENGINE DRIFT: ...`) in `claude --debug`, with actionable next steps. To bypass drift detection during engine development, set `ALLOW_ENGINE_DRIFT=1`.

For local development workflow (lint, structural tests, behavioral tests, auto-venv), see the **Quick start** section in [CONTRIBUTING.md](CONTRIBUTING.md) — `./scripts/verify.sh` is the canonical "is my dev environment healthy" command.

### Use

```
> Set up my quantum-safe identity as "scott"

> Import alice's identity card from ~/alice-identity.json

> Send "The quantum computers are coming. Prepare accordingly." to alice

> Check my messages
```

The agent handles everything — key generation, encryption, signing, delivery, verification, decryption.

## Quantum Handshake — Zero-Friction Key Bootstrap

The hardest part of encrypted messaging is key exchange. Quantum Seal solves this with an automated handshake protocol:

```
> Establish secure comms with alice
```

What happens automatically:
1. Your identity is generated (if needed) with opaque key handles
2. Your public identity card is published to a shared discovery directory
3. Alice's identity card is discovered and validated
4. A signed challenge-response handshake proves both sides hold their claimed keys
5. Contacts are imported, fingerprints recorded, trust established
6. Done — `secure-send` and `secure-receive` just work

**Trust-on-first-use (TOFU):** Like SSH's `known_hosts`. First contact is automatic. If a fingerprint changes later, you get a critical warning — possible impersonation.

## Skills

| Skill | What It Does |
|-------|-------------|
| **quantum-handshake** | Automated first-contact key bootstrap. TOFU key discovery, signed challenge-response, mutual verification. The missing mile between "I have keys" and "we can talk." |
| **setup-identity** | Generate hybrid encryption + ML-DSA-65 signing keys with opaque handles. Secret keys never enter the conversation. |
| **key-exchange** | Import/export identity cards, manage contact directory, verify fingerprints out-of-band. |
| **secure-send** | Encrypt + sign + deliver. Two modes: *agent-readable* (agent composes the message) or *courier* (agent reads from file — base64 content still in tool call). |
| **secure-receive** | Verify sender signature BEFORE decryption. Report authentication status + content. Archive processed messages. |
| **inspect-envelope** | Forensic metadata — sender, sizes, fingerprints, authentication — without any secret keys. |
| **verify-sender** | Verify sender signature using pqc_hybrid_auth_verify — checks ML-DSA-65 signature, fingerprint consistency, and timestamp freshness in one call. No decryption needed. |

## Agent

**quantum-messenger** — autonomous agent that manages the full lifecycle:

```
> Set up encrypted messaging between me and alice, then send her
  "The lattice holds" and wait for a reply
```

It will: check for your identity (create if needed), check for alice's contact (ask to import if missing), seal the message, sign it, deliver the envelope, then monitor your inbox for her response.

## Security Model

### Guarantees
- **Hybrid confidentiality** — both X25519 and ML-KEM-768 must be broken to compromise a message
- **Sender authentication** — ML-DSA-65 signature over a canonical transcript proves identity
- **Verify-before-decrypt** — forged signatures fail at authentication, never reach the AEAD layer
- **Secret key isolation** (when using `store_as`) — opaque handles keep private keys in the MCP server's process memory, out of the AI's context

### Non-Guarantees
- **Not forward-secret** — recipient key compromise exposes past messages
- **Bounded replay protection** — v2 envelopes include signed timestamps; stale envelopes (>24h) are rejected. Stateful dedup available at the handler layer. No protection for v1 envelopes.
- **Not mutually authenticated** — sender proves identity to recipient, not vice versa
- **Agent sees plaintext** in agent-readable mode. Courier mode reads from file but base64 content still appears in tool calls — not true content-blindness.
- **Not production-grade** — liboqs is research/prototyping software

### Content Safety
- Decrypted messages are treated as **untrusted input**, even from verified senders
- The agent will never execute commands from messages without user approval
- Suspicious patterns (shell commands, tool-call JSON, encoded payloads) trigger warnings
- A verified sender does NOT mean safe content — a contact's keys could be compromised

### Security Features (v2 Protocol)
- **Signed timestamps** — v2 envelopes bind freshness to the ML-DSA-65 signature
- **Replay detection** — signature-digest cache rejects duplicate envelopes
- **Envelope validation** — size limits prevent memory bombs; malformed fields rejected before crypto
- **Handle-only mode** — PQC_REQUIRE_KEY_HANDLES=1 enforces opaque handles for hybrid envelope operations
- **Verify-before-decrypt** — authentication failure never reaches the AEAD layer

## Architecture

```
┌─────────────────────────────────────┐
│         quantum-seal plugin         │
│                                     │
│  Skills:       Agent:               │
│  - identity    - quantum-messenger  │
│  - exchange                         │
│  - send        Filesystem:          │
│  - receive     ~/.pqc/identities/   │
│  - inspect     ~/.pqc/contacts/     │
│  - verify      ~/.pqc/inboxes/      │
│  - handshake   ~/.pqc/state/        │
│                                     │
│  ─ ─ ─ ─ ─ ─ MCP ─ ─ ─ ─ ─ ─ ─   │
│                                     │
│  post-quantum-mcp server            │
│  24 tools | hybrid.py | key_store   │
│                                     │
│  ─ ─ ─ ─ ─ ─ FFI ─ ─ ─ ─ ─ ─ ─   │
│                                     │
│  liboqs (C) + cryptography (Python) │
│  ML-KEM-768 | ML-DSA-65 | X25519   │
│  AES-256-GCM | SHA3-256 | HKDF     │
└─────────────────────────────────────┘
```

## Filesystem Layout

```
~/.pqc/
  identities/     # Public identity cards + local state files
  contacts/       # Imported contact identity cards
  inboxes/        # Incoming sealed envelopes
  outbox/         # Outgoing sealed envelopes
  archive/        # Processed messages
  discovery/      # Published identity cards for handshake
  handshakes/     # Pending handshake state
  state/          # Persistent replay cache
```

## Related Projects

- **[post-quantum-mcp](https://github.com/scottdhughes/post-quantum-mcp)** — The cryptographic engine (24 MCP tools)
- **[quantum-proof-bitcoin](https://github.com/scottdhughes/quantum-proof-bitcoin)** — Bitcoin with post-quantum signatures

## License

MIT License — see [LICENSE](LICENSE) for details.

## Author

[Scott Hughes](https://github.com/scottdhughes)
