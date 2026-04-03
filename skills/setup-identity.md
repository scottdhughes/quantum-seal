---
name: setup-identity
description: Generate a quantum-resistant cryptographic identity for the current agent or user. Creates hybrid encryption keys (X25519 + ML-KEM-768) and post-quantum signing keys (ML-DSA-65), stores them as opaque handles so secret keys never enter the conversation, and writes a shareable identity card to the local filesystem. Use this before any secure messaging operation.
---

# Setup Post-Quantum Identity

You are setting up a quantum-resistant cryptographic identity. This is the foundation for all secure messaging — without an identity, you cannot send or receive encrypted messages.

## What You Are Building

A **post-quantum cryptographic identity** consists of:

1. **Hybrid encryption keypair** (X25519 + ML-KEM-768) — for receiving encrypted messages. The X25519 component provides classical security; the ML-KEM-768 component provides quantum resistance. Both must be broken simultaneously to compromise confidentiality.

2. **ML-DSA-65 signing keypair** (FIPS 204) — for proving your identity when sending messages. ML-DSA-65 is NIST Level 3 post-quantum security, resistant to both classical and quantum attacks.

3. **Identity card** — a JSON file containing only public material (public keys + fingerprints) that can be safely shared with anyone. This is how other agents discover your identity.

## Security Model

- Secret keys are stored as **opaque handles** via `store_as`. They exist only in the MCP server's process memory and **never appear in this conversation or any tool output**.
- Public keys and fingerprints are safe to share, publish, or transmit over any channel.
- Identity handles are **process-local** — they are lost when the MCP server restarts. The identity card on disk allows re-importing public material, but a new identity must be generated for each server session.
- This is research/prototyping tooling. liboqs is not recommended for production use.

## Procedure

### Step 1: Choose an identity name

Ask the user what name to use for this identity. Default to their username or a descriptive name like `"agent-alice"` or `"scott-primary"`. The name must be unique within the current session.

### Step 2: Generate hybrid encryption keys

Call `pqc_hybrid_keygen` with `store_as` set to the identity name:

```
Tool: pqc_hybrid_keygen
Arguments: {"store_as": "<identity-name>"}
```

Record the output — it contains only public material:
- `classical.public_key` and `classical.fingerprint` (X25519)
- `pqc.public_key` and `pqc.fingerprint` (ML-KEM-768)

No secret keys will appear in the response. They are stored as an opaque handle inside the MCP server.

### Step 3: Generate signing keys

Call `pqc_generate_keypair` with ML-DSA-65 and `store_as` set to `<identity-name>-signing`:

```
Tool: pqc_generate_keypair
Arguments: {"algorithm": "ML-DSA-65", "store_as": "<identity-name>-signing"}
```

Record the output:
- `public_key` and `fingerprint` (ML-DSA-65)
- `fingerprint_algorithm`: SHA3-256

Again, no secret key in the response.

### Step 4: Write identity card to disk

Create the directory `~/.pqc/identities/` if it doesn't exist. Write a JSON identity card containing **only public material** -- this file is safe to share with anyone:

```json
{
  "name": "<identity-name>",
  "created": "<ISO-8601 timestamp>",
  "suite": "mlkem768-x25519-sha3-256",
  "signing_algorithm": "ML-DSA-65",
  "encryption": {
    "classical_public_key": "<base64 from step 2>",
    "classical_fingerprint": "<hex from step 2>",
    "pqc_public_key": "<base64 from step 2>",
    "pqc_fingerprint": "<hex from step 2>"
  },
  "signing": {
    "public_key": "<base64 from step 3>",
    "fingerprint": "<hex from step 3>",
    "fingerprint_algorithm": "SHA3-256"
  },
  "warning": "Research/prototyping only. liboqs is not recommended for production use."
}
```

Save to `~/.pqc/identities/<identity-name>.json`.

The identity card contains only public material and is safe to share. Handle names are stored separately in a local state file (see Step 4b).

### Step 4b: Write local state file

Save handle names to a separate local state file so they can be reloaded when needed. This file stays on your machine and is **not** shared:

```json
{
  "name": "<identity-name>",
  "handles": {
    "encryption": "<identity-name>",
    "signing": "<identity-name>-signing"
  },
  "created": "<ISO-8601>",
  "session_note": "Handles are process-local — lost on MCP server restart."
}
```

Save to `~/.pqc/identities/<identity-name>.local.json`.

### Step 5: Confirm to the user

Report:
- Identity name and handle names
- Signing fingerprint (this is what others will use to verify messages from you)
- Encryption fingerprints (classical + PQC)
- Path to the identity card file
- Remind them: "Share your identity card or fingerprints with anyone you want to communicate with. Your secret keys are stored as opaque handles and never leave the server process."

## If Identity Already Exists

If the user runs this again with the same name, warn them that overwriting will generate new keys (the old identity is gone). Ask for confirmation before proceeding with `overwrite: true`.
