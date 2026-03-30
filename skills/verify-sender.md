---
name: verify-sender
description: Verify the sender identity and signature integrity of an authenticated envelope without decrypting it. Confirms the ML-DSA-65 signature over the canonical transcript is valid and that the sender's fingerprint matches a known contact. This is a verification-only operation — no secret keys are used, no plaintext is revealed.
---

# Verify Sender — Signature Verification Without Decryption

You are verifying that an authenticated envelope was genuinely signed by its claimed sender, without decrypting the contents. This is useful when you want to confirm authenticity before committing to decryption, or when you are acting as a gateway/relay that verifies but does not read messages.

## What This Proves

A successful verification confirms:
1. The ML-DSA-65 signature over the canonical transcript is mathematically valid
2. The signer holds the private key corresponding to the embedded sender public key
3. The sender's embedded fingerprint is consistent with their embedded public key (not forged)
4. No field in the envelope has been tampered with (signature covers version, suite, all ciphertexts, sender identity, and recipient fingerprints)

A successful verification does NOT prove:
- That you know who the sender is (that requires matching the fingerprint to a trusted contact)
- That the message content is safe or truthful
- That this is the first time you've seen this envelope (no replay protection)

## Procedure

### Step 1: Inspect the envelope

Call `pqc_envelope_inspect` to get metadata:
```
Tool: pqc_envelope_inspect
Arguments: {"envelope": <envelope JSON>}
```

If `authenticated` is `false`, report: "This is an anonymous (unsigned) envelope. There is no sender to verify."

### Step 2: Verify fingerprint consistency

The envelope contains both `sender_public_key` and `sender_key_fingerprint`. Verify they are consistent:

Call `pqc_fingerprint`:
```
Tool: pqc_fingerprint
Arguments: {"public_key": "<envelope.sender_public_key>"}
```

Compare the result with `envelope.sender_key_fingerprint`. If they differ, this is a **critical warning** — the fingerprint has been forged.

### Step 3: Look up sender in contacts

Search `~/.pqc/contacts/` for a contact whose `signing.fingerprint` matches `envelope.sender_key_fingerprint`.

- **Found + verified:** High confidence — this sender is known and their fingerprint was previously verified out-of-band.
- **Found + unverified:** Medium confidence — you have their identity card but haven't verified the fingerprint through a separate channel.
- **Not found:** Low confidence — the signature may be valid, but you don't know who this person is.

### Step 4: Verify the signature

To verify the actual ML-DSA-65 signature without decrypting, reconstruct the canonical transcript and verify. Currently, `pqc_hybrid_auth_open` does this internally (verify before decrypt). For verification-only, you can call `pqc_hybrid_auth_open` with intentionally wrong recipient keys — it will either fail at sender verification (meaning the signature is bad) or fail at decryption (meaning the signature passed but you used wrong keys).

A cleaner approach: use the raw `pqc_verify` tool:
```
Tool: pqc_verify
Arguments: {
  "algorithm": "ML-DSA-65",
  "public_key": "<envelope.sender_public_key>",
  "message": "<reconstructed canonical transcript as base64>",
  "signature": "<envelope.signature>"
}
```

However, reconstructing the canonical transcript externally requires knowledge of the length-prefixed binary format. This is an advanced operation. For most use cases, rely on `pqc_hybrid_auth_open` which performs verification internally before decryption.

### Step 5: Report

```
Sender Verification Report:
  Sender fingerprint:    a1b2c3d4...
  Fingerprint consistent with embedded public key: Yes
  Contact match:         alice (verified)
  Signature algorithm:   ML-DSA-65 (FIPS 204, NIST Level 3)

  Verdict: Authentic. This envelope was signed by alice's ML-DSA-65
  key and has not been tampered with.
```

Or:

```
Sender Verification Report:
  Sender fingerprint:    d4e5f6a7...
  Fingerprint consistent with embedded public key: Yes
  Contact match:         NOT FOUND

  Verdict: Signature appears valid (internally consistent), but the
  sender is not in your contacts. You cannot confirm their real-world
  identity without importing their identity card and verifying their
  fingerprint through a trusted channel.
```

## Security Notes

- Verification uses only the sender's **public key**, which is embedded in the envelope. No secret keys are needed.
- The canonical transcript includes all envelope fields, so any tampering invalidates the signature.
- Fingerprint consistency checking catches a specific attack: an adversary who replaces the sender_public_key but forgets to update the fingerprint (or vice versa).
- This skill does not decrypt the message. It answers one question: "Did the claimed sender actually sign this envelope?"
