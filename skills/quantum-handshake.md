---
name: quantum-handshake
description: Automated quantum-resistant first-contact key bootstrap between two AI agents. Establishes trust-on-first-use (TOFU) by exchanging identity cards through a shared discovery directory, performing a signed challenge-response handshake to prove liveness and key possession, and importing verified contacts — all without manual key copying. After handshake completes, secure-send and secure-receive just work. Uses ML-DSA-65 signatures for handshake authentication and hybrid X25519 + ML-KEM-768 for subsequent encrypted messaging.
---

# Quantum Handshake — Zero-Friction Key Bootstrap

You are establishing quantum-resistant secure communications with another agent. This skill automates the entire first-contact flow: identity generation, key discovery, mutual verification via signed challenge-response, and contact import. When it completes, both agents can exchange encrypted authenticated messages with zero manual key management.

## Trust Model: Trust-On-First-Use (TOFU)

Like SSH's `known_hosts`, the first contact with a new agent is accepted and recorded. Every subsequent interaction is verified against the stored fingerprint. If a fingerprint changes unexpectedly, this is a **critical warning** — the agent's identity may have been compromised or an impersonator may be present.

TOFU does NOT protect against a man-in-the-middle during the initial handshake. For high-security environments, fingerprints should be verified out-of-band after the handshake completes. The handshake skill will remind the user of this.

## Prerequisites

- The post-quantum-mcp server must be running (provides all crypto tools)
- Both agents must have access to a shared discovery directory (default: `~/.pqc/discovery/`)
- For same-machine agents: the filesystem is the shared directory
- For network agents: the discovery directory could be a shared mount, synced folder, or replaced with a future network transport

## The Handshake Protocol

```
Agent A                    Discovery Dir                    Agent B
  |                            |                              |
  | 1. Write identity card     |                              |
  | ────────────────────────>  |                              |
  |                            |  2. Write identity card      |
  |                            |  <────────────────────────── |
  |                            |                              |
  | 3. Discover B's card       |                              |
  | <──────────────────────    |                              |
  |                            |    4. Discover A's card      |
  |                            |    ──────────────────────>   |
  |                            |                              |
  | 5. Import B's public keys  |                              |
  |    Generate challenge      |                              |
  |    Sign + seal handshake   |                              |
  | ───────── envelope ──────> | ──────── envelope ────────> |
  |                            |                              |
  |                            |    6. Verify A's signature   |
  |                            |       Import A's public keys |
  |                            |       Generate own challenge |
  |                            |       Sign + seal ack        |
  |                            |  <──────── ack ──────────── |
  | <──────── ack ──────────── |                              |
  |                            |                              |
  | 7. Verify B's ack          |                              |
  |    Confirm challenge resp  |                              |
  |    Mark contact verified   |                              |
  |                            |    8. Receive A's final ack  |
  |                            |       Mark contact verified  |
  |                            |                              |
  | ✓ HANDSHAKE COMPLETE       |     ✓ HANDSHAKE COMPLETE    |
```

## Procedure

### Step 1: Ensure your identity exists

Check `~/.pqc/identities/` for an identity card. If none exists, invoke the `setup-identity` skill to generate one. You need both:
- Hybrid encryption handle (e.g., `scott`)
- ML-DSA-65 signing handle (e.g., `scott-signing`)

### Step 2: Publish to discovery

Create the discovery directory if it doesn't exist: `~/.pqc/discovery/`

Copy your identity card to the discovery directory:
```
cp ~/.pqc/identities/<your-name>.json ~/.pqc/discovery/<your-name>.identity.json
```

This makes your public keys discoverable by other agents on the same machine.

### Step 3: Wait for the other agent

The user will tell you who to establish comms with (e.g., "establish secure comms with alice").

Watch `~/.pqc/discovery/` for `<their-name>.identity.json` to appear. Check every 2 seconds for up to 60 seconds. If the user specified a file path or pasted an identity card, use that directly instead of waiting.

If the file doesn't appear within 60 seconds, prompt the user: "No identity card found for <name> in ~/.pqc/discovery/ after 60 seconds. Options: (1) Keep waiting, (2) Provide their identity card directly, (3) Abort."

### Step 4: Validate the discovered identity card

When the other agent's identity card appears:

1. Read and parse the JSON
2. Verify it has required fields: `name`, `suite`, `signing_algorithm`, `encryption`, `signing`
3. Verify the suite is `mlkem768-x25519-sha3-256`
4. **Verify fingerprint consistency**: compute fingerprints from the embedded public keys using `pqc_fingerprint` and check they match the claimed fingerprints
5. If any check fails, abort and warn the user

### Step 5: Check for existing contact (TOFU)

Check if `~/.pqc/contacts/<their-name>.json` already exists:

- **New contact (first use):** Proceed to handshake. This is the TOFU case — we'll trust this identity on first sight and record it.
- **Existing contact, same fingerprint:** Already known. Skip to step 9 (handshake complete — already trusted).
- **Existing contact, DIFFERENT fingerprint:** **CRITICAL WARNING.** Display:

```
⚠ IDENTITY CHANGE DETECTED ⚠

Contact '<name>' was previously known with signing fingerprint:
  <old fingerprint>

The newly discovered identity has signing fingerprint:
  <new fingerprint>

This could mean:
  1. The contact legitimately regenerated their keys
  2. An attacker is impersonating this contact

DO NOT proceed without out-of-band verification.
Verify the new fingerprint with the contact directly.
```

Ask the user whether to accept the new identity or abort. Only proceed with explicit user approval.

### Step 6: Send handshake challenge

Generate a random challenge (32 random bytes, hex-encoded):

```python
import os
challenge = os.urandom(32).hex()
```

Create a handshake message:
```json
{
  "type": "quantum-handshake",
  "protocol_version": "1.0",
  "from": "<your-name>",
  "to": "<their-name>",
  "challenge": "<64 hex chars>",
  "signing_fingerprint": "<your signing fingerprint>",
  "timestamp": "<ISO-8601>"
}
```

Seal this message as an **authenticated envelope** to the other agent:

```
Tool: pqc_hybrid_auth_seal
Arguments: {
  "plaintext": "<handshake JSON>",
  "recipient_classical_public_key": "<their X25519 public key from identity card>",
  "recipient_pqc_public_key": "<their ML-KEM-768 public key from identity card>",
  "sender_key_store_name": "<your-signing-handle>"
}
```

Write the envelope to their inbox:
```
~/.pqc/inboxes/<their-name>/<your-name>-handshake.envelope.json
```

Save the challenge locally for verification:
```
~/.pqc/handshakes/<their-name>.pending.json
```
containing `{"challenge": "<hex>", "timestamp": "<ISO-8601>"}`.

### Step 7: Wait for handshake acknowledgment

Watch `~/.pqc/inboxes/<your-name>/` for `<their-name>-handshake-ack.envelope.json`.

When it arrives:

1. Inspect the envelope with `pqc_envelope_inspect`
2. Verify the sender fingerprint matches the identity card you discovered
3. Open the envelope:

```
Tool: pqc_hybrid_auth_open
Arguments: {
  "envelope": <ack envelope>,
  "key_store_name": "<your-encryption-handle>",
  "expected_sender_fingerprint": "<their signing fingerprint>"
}
```

4. Parse the plaintext as JSON. It should be:
```json
{
  "type": "quantum-handshake-ack",
  "protocol_version": "1.0",
  "from": "<their-name>",
  "to": "<your-name>",
  "challenge_response": "<SHA3-256 of your original challenge>",
  "challenge": "<their 64 hex chars>",
  "signing_fingerprint": "<their signing fingerprint>",
  "timestamp": "<ISO-8601>"
}
```

5. **Verify the challenge response**: compute `SHA3-256` of your original challenge and compare to `challenge_response`. If it doesn't match, abort — this proves the responder actually decrypted your handshake (they have the right keys).

6. **Send your own challenge response**: Create a final ack:
```json
{
  "type": "quantum-handshake-complete",
  "protocol_version": "1.0",
  "from": "<your-name>",
  "to": "<their-name>",
  "challenge_response": "<SHA3-256 of their challenge>",
  "timestamp": "<ISO-8601>"
}
```

Seal and deliver to their inbox as `<your-name>-handshake-complete.envelope.json`.

### Step 8: Import contact and mark verified

1. Save their identity card to `~/.pqc/contacts/<their-name>.json`
2. Add `"verified": true` and `"verified_via": "quantum-handshake"` and `"first_seen": "<timestamp>"`
3. Clean up: remove `~/.pqc/handshakes/<their-name>.pending.json`
4. Clean up: remove handshake envelopes from inboxes

### Step 9: Report to user

```
✓ Quantum handshake complete with <name>

  Their signing fingerprint: <hex>
  Their X25519 fingerprint:  <hex>
  Their ML-KEM fingerprint:  <hex>
  Trust: TOFU (first-use) — verify out-of-band for high security
  Contact saved: ~/.pqc/contacts/<name>.json

  You can now send encrypted messages:
    "Send <message> to <name>"
```

## Being the Responder

If you are the agent being contacted (you find a handshake envelope in your inbox before you've initiated):

1. Inspect the handshake envelope
2. Look up the sender's identity card in `~/.pqc/discovery/`
3. Validate it (same checks as Step 4)
4. Open and verify the handshake envelope
5. Parse the challenge
6. Create and send the handshake-ack (Step 7's ack format)
7. Wait for the handshake-complete message
8. Verify the challenge response
9. Import contact and mark verified

The protocol is symmetric — either side can initiate.

## Handling the Responder Side Automatically

If you detect a `*-handshake.envelope.json` in your inbox that you didn't initiate:

1. Tell the user: "<name> is requesting a quantum handshake. Accept?"
2. If yes, proceed as responder
3. If no, ignore the envelope

## Security Properties

| Property | Status |
|----------|--------|
| Mutual key exchange | Yes — both sides exchange public keys |
| Mutual key-possession proof | Yes — both sides sign challenges, proving they hold their private keys |
| Challenge-response liveness | Yes — proves both sides hold their claimed private keys |
| Replay protection | Partial — challenges are random, but no expiry enforcement |
| MITM protection on first contact | No — TOFU. Verify fingerprints out-of-band for full MITM resistance |
| MITM protection on subsequent contacts | Yes — fingerprint change triggers critical warning |
| Forward secrecy | No — same limitation as the underlying envelope protocol |

## Error Handling

- **Identity card validation fails:** "The identity card for <name> is malformed or uses an unsupported suite. Cannot proceed."
- **Fingerprint mismatch in card:** "DANGER: The fingerprints in <name>'s identity card do not match the embedded public keys. This card may have been tampered with."
- **Challenge response mismatch:** "Handshake failed: challenge response from <name> does not match. This may indicate a MITM attack or a protocol error."
- **Timeout:** "No response from <name> after waiting. They may not have started their agent yet, or their identity card may not be published."
- **Identity change detected:** See Step 5 — critical warning with user decision required.
