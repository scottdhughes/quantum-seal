---
name: inspect-envelope
description: Forensic inspection of a sealed quantum-resistant envelope without decrypting it. Reveals metadata — suite, sender identity, fingerprints, ciphertext sizes, authentication status — using zero secret keys. Useful for auditing, routing, policy enforcement, and trust decisions before committing to decryption.
---

# Inspect Envelope — Forensic Metadata Without Decryption

You are inspecting a sealed envelope to understand its properties without decrypting it. This requires NO secret keys — anyone can inspect an envelope.

## When to Use This

- **Before decrypting:** Check who sent it and whether you trust them
- **Auditing:** Log envelope metadata without accessing content
- **Routing:** Decide where to forward an envelope based on sender/recipient fingerprints
- **Policy enforcement:** Reject envelopes that don't meet criteria (wrong suite, unknown sender, etc.)
- **Debugging:** Verify envelope structure and sizes

## Procedure

### Step 1: Load the envelope

Parse the envelope JSON from a file path, pasted content, or another tool's output.

### Step 2: Inspect

Call `pqc_envelope_inspect`:
```
Tool: pqc_envelope_inspect
Arguments: {"envelope": <envelope JSON>}
```

### Step 3: Analyze and report

The inspection reveals:

**For any envelope:**
- `version` — protocol version (`pqc-mcp-v2` for current envelopes, `pqc-mcp-v1` for legacy)
- `suite` — hybrid KEM suite (should be `mlkem768-x25519-sha3-256`)
- `ciphertext_size` — size of the AES-256-GCM ciphertext in bytes
- `plaintext_size_approx` — estimated plaintext size (ciphertext minus 16-byte GCM tag)
- `pqc_ciphertext_size` — ML-KEM-768 ciphertext size (~1088 bytes)
- `x25519_ephemeral_public_key_size` — should be exactly 32 bytes
- `authenticated` — boolean: is this a sender-authenticated envelope?

**For authenticated envelopes additionally:**
- `sender_signature_algorithm` — should be `ML-DSA-65`
- `sender_key_fingerprint` — SHA3-256 hex fingerprint of the sender's public key
- `recipient_classical_key_fingerprint` — X25519 recipient fingerprint
- `recipient_pqc_key_fingerprint` — ML-KEM-768 recipient fingerprint
- `signature_size` — ML-DSA-65 signature size (~3309 bytes)

### Step 4: Cross-reference with contacts

If authenticated, look up `sender_key_fingerprint` in `~/.pqc/contacts/`:
- **Match found:** Report sender name and whether the contact is verified
- **No match:** Report "Unknown sender" and display the full fingerprint

Also check `recipient_classical_key_fingerprint` and `recipient_pqc_key_fingerprint` against your own identity to confirm the envelope is addressed to you.

### Step 5: Present findings

Format as a clear summary:

```
Envelope Analysis:
  Version:        pqc-mcp-v2
  Suite:          mlkem768-x25519-sha3-256
  Authenticated:  Yes
  Sender:         alice (fingerprint: a1b2c3...)
  Addressed to:   You (fingerprints match your identity)
  Content size:   ~142 bytes (estimated)
  Signature:      ML-DSA-65 (3309 bytes)

  Recommendation: Safe to decrypt. Sender is a known, verified contact.
```

Or for suspicious envelopes:

```
Envelope Analysis:
  Version:        pqc-mcp-v2
  Suite:          mlkem768-x25519-sha3-256
  Authenticated:  Yes
  Sender:         UNKNOWN (fingerprint: d4e5f6...)
  Addressed to:   You (fingerprints match)

  Warning: Sender is not in your contacts. The signature may be valid
  (proving someone with this key signed it) but you cannot confirm
  who that person is. Import their identity card before trusting.
```
