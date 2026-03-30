---
name: key-exchange
description: Exchange quantum-resistant public keys with another agent or user. Import a contact's identity card to enable encrypted communication, or export your own identity for sharing. Manages the local contact directory at ~/.pqc/contacts/. Use this after setup-identity and before secure-send or secure-receive.
---

# Post-Quantum Key Exchange

You are managing cryptographic contacts for quantum-resistant messaging. Before you can send someone an encrypted message, you need their public keys. Before they can send to you, they need yours.

## Contact Directory

Contacts are stored as JSON files in `~/.pqc/contacts/`. Each file contains the public material needed to encrypt messages to that contact and verify messages from them.

## Operations

### Import a Contact

When the user provides another agent's or person's identity card (as a file path, pasted JSON, or URL):

1. Parse the identity card JSON
2. Validate it has the required fields: `name`, `suite`, `signing_algorithm`, `encryption`, `signing`
3. Verify the suite is `mlkem768-x25519-sha3-256` and signing algorithm is `ML-DSA-65`
4. Compute fingerprints from the embedded public keys using `pqc_fingerprint` to verify they match the claimed fingerprints
5. Save to `~/.pqc/contacts/<name>.json`
6. Report the contact name and fingerprints to the user

**Fingerprint verification is critical.** If the computed fingerprint doesn't match the claimed fingerprint in the identity card, warn the user — the card may have been tampered with.

### Export Your Identity

1. Read your identity card from `~/.pqc/identities/<name>.json`
2. Present it to the user for sharing (display or write to a specified path)
3. Remind them: this contains only public material and is safe to share over any channel

### List Contacts

1. Read all files in `~/.pqc/contacts/`
2. Display a table: name, signing fingerprint (first 16 hex chars), suite, date added
3. This is the user's "address book" for encrypted messaging

### Verify a Contact's Fingerprint

When the user wants to verify a contact out-of-band (e.g., they read a fingerprint over the phone):

1. Load the contact from `~/.pqc/contacts/<name>.json`
2. Display the full signing fingerprint
3. Ask the user to confirm it matches what they received out-of-band
4. If confirmed, mark the contact as `"verified": true` in the JSON

## Security Notes

- **Public keys are safe to share** over any channel — email, chat, public repository, QR code.
- **Fingerprints should be verified out-of-band** for high-security use. If you only import a key from an untrusted channel, an attacker could substitute their own keys (a classic MITM concern).
- **The contact directory contains no secret material.** It can be backed up, synced, or shared without risk.
- **This is research/prototyping tooling.** Do not rely on it for protecting sensitive data in production.
