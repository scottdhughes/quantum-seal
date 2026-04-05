---
name: verify-sender
description: Verify the sender identity and signature integrity of an authenticated envelope without decrypting it. Uses pqc_hybrid_auth_verify to validate the ML-DSA-65 signature, sender binding, fingerprint consistency, and timestamp freshness in a single call. This is a verification-only operation — no secret keys are used, no plaintext is revealed.
---

# Verify Sender — Signature Verification Without Decryption

You are verifying that an authenticated envelope was genuinely signed by its claimed sender, without decrypting the contents. This is useful when you want to confirm authenticity before committing to decryption, or when you are acting as a gateway/relay that verifies but does not read messages.

## What This Proves

A successful verification confirms:
1. The ML-DSA-65 signature over the canonical transcript is mathematically valid
2. The signer holds the private key corresponding to the embedded sender public key
3. The sender's embedded fingerprint is consistent with their embedded public key (not forged)
4. No field in the envelope has been tampered with (signature covers version, suite, all ciphertexts, sender identity, and recipient fingerprints)
5. For v2/v3 envelopes: the signed timestamp is within the freshness window (stale envelopes are rejected)

A successful verification does NOT prove:
- That you know who the sender is (that requires matching the fingerprint to a trusted contact)
- That the message content is safe or truthful
- That this is the first time you've seen this envelope (the replay cache persists to `~/.pqc/state/replay-cache.json`; `pqc_hybrid_auth_verify` reports `replay_seen` as an advisory flag but does not reject duplicates — use `pqc_hybrid_auth_open` for full replay rejection of previously-opened envelopes)

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

Call `pqc_hybrid_auth_verify` with the envelope and the expected sender's fingerprint from Step 3:
```
Tool: pqc_hybrid_auth_verify
Arguments: {
  "envelope": <envelope JSON>,
  "expected_sender_fingerprint": "<fingerprint from contact file>"
}
```

Note: you must provide either `expected_sender_fingerprint` or `expected_sender_public_key`. The tool will not verify without a sender binding — this prevents accepting envelopes from arbitrary signers.

This tool performs all verification checks:
- Validates that the sender's fingerprint matches the embedded public key
- Verifies the ML-DSA-65 signature over the canonical transcript
- Checks timestamp freshness for v2/v3 envelopes (rejects stale signatures)

On success, the tool returns:
- `verified` — always `true` (the tool raises an exception on failure)
- `sender_key_fingerprint` — the fingerprint of the signing key
- `sender_signature_algorithm` — the signature algorithm used (e.g., `ML-DSA-65`)
- `timestamp` — the signed timestamp (v2/v3 envelopes)
- `replay_seen` — advisory flag if this exact envelope has been seen before (checked against the persistent replay cache at `~/.pqc/state/replay-cache.json`)
- `warning` — present only for v1 envelopes, warns about missing freshness protection

On failure, the tool raises `SenderVerificationError` (wrong sender, bad signature, inconsistent fingerprint) or `ValueError` (bad version, missing fields, stale timestamp). Catch the error and report it — do not trust the envelope.

### Step 5: Report

```
Sender Verification Report:
  Sender fingerprint:    a1b2c3d4...
  Fingerprint consistent with embedded public key: Yes
  Contact match:         alice (verified)
  Signature algorithm:   ML-DSA-65 (FIPS 204, NIST Level 3)
  Timestamp:             2026-04-01T12:34:56Z
  Replay advisory:       No

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
- `pqc_hybrid_auth_verify` checks fingerprint consistency internally, but Step 2 is retained as defense-in-depth so you can surface a clear warning before the full verification call.
- For v2/v3 envelopes, signed timestamps provide bounded freshness. The replay cache persists to `~/.pqc/state/replay-cache.json` and provides bounded dedup. `pqc_hybrid_auth_verify` reports `replay_seen` as an advisory flag; `pqc_hybrid_auth_open` rejects previously-opened envelopes.
- This skill does not decrypt the message. It answers one question: "Did the claimed sender actually sign this envelope?"
