---
name: secure-send
description: Send a quantum-resistant encrypted and sender-authenticated message to a contact. Seals the message with hybrid X25519 + ML-KEM-768 encryption and signs it with ML-DSA-65 using opaque key handles. Supports both agent-readable mode (plaintext in conversation) and courier mode (plaintext from file, agent never sees content). Delivers the sealed envelope to the recipient's inbox.
---

# Secure Send — Quantum-Resistant Authenticated Messaging

You are sending an encrypted, sender-authenticated message. The message will be:
- **Encrypted** with hybrid X25519 + ML-KEM-768 (quantum-resistant confidentiality)
- **Signed** with ML-DSA-65 (quantum-resistant sender authentication)
- **Sealed** as a self-contained envelope that can be transmitted over any channel

## Prerequisites

Before sending, you need:
1. Your own identity set up (run `setup-identity` skill if not done)
2. The recipient imported as a contact (run `key-exchange` skill if not done)

Check: `~/.pqc/identities/<your-name>.json` and `~/.pqc/contacts/<recipient>.json` must exist.

## Two Modes

### Agent-Readable Mode (default)
The message plaintext is passed directly in the tool call. The agent sees the content. Use this when the agent is composing or acting on the message.

### Courier Mode
The message plaintext is read from a file. The agent never sees the content — it only orchestrates encryption and delivery. Use this when the user says something like "encrypt the file at /path/to/message.txt" or "send this file securely."

## Procedure

### Step 1: Identify sender and recipient

- Sender: load identity from `~/.pqc/identities/`. Get handle names from `handles.encryption` and `handles.signing`.
- Recipient: load contact from `~/.pqc/contacts/`. Get their public keys.

### Step 2: Determine mode

- If the user provides a message directly → **agent-readable mode**, use `plaintext` parameter
- If the user provides a file path → **courier mode**, use `plaintext_base64` with the file contents base64-encoded (read the file, base64-encode, pass as `plaintext_base64`)

### Step 3: Seal the message

Call `pqc_hybrid_auth_seal`:

**Agent-readable mode:**
```
Tool: pqc_hybrid_auth_seal
Arguments: {
  "plaintext": "<message text>",
  "recipient_key_store_name": "<recipient-handle>",
  "sender_key_store_name": "<your-signing-handle>"
}
```

**Courier mode:**
```
Tool: pqc_hybrid_auth_seal
Arguments: {
  "plaintext_base64": "<base64 of file contents>",
  "recipient_key_store_name": "<recipient-handle>",
  "sender_key_store_name": "<your-signing-handle>"
}
```

Note: `recipient_key_store_name` won't work here because the recipient's keys are in the contact file, not the key store. Instead, pass the raw public keys from the contact file:

```
Tool: pqc_hybrid_auth_seal
Arguments: {
  "plaintext": "<message>",
  "recipient_classical_public_key": "<from contact.encryption.classical_public_key>",
  "recipient_pqc_public_key": "<from contact.encryption.pqc_public_key>",
  "sender_key_store_name": "<your-signing-handle>"
}
```

### Step 4: Write the envelope

Create `~/.pqc/outbox/` if it doesn't exist. Write the envelope JSON to:
```
~/.pqc/outbox/<recipient>-<timestamp>.envelope.json
```

Also create the recipient's inbox directory if using local delivery:
```
~/.pqc/inboxes/<recipient>/
```

Copy the envelope there for local same-machine delivery.

### Step 5: Confirm to the user

Report:
- Recipient name
- Your signing fingerprint
- Envelope file path
- Mode used (agent-readable or courier)
- Envelope size
- "Message sealed and delivered. The recipient can open it with their secret keys and your fingerprint."

## Error Handling

- **Contact not found:** "No contact named '<name>' found in ~/.pqc/contacts/. Run the key-exchange skill to import their identity card."
- **Identity not set up:** "No identity found. Run the setup-identity skill first."
- **Seal failure:** Report the structured error from the MCP tool (e.g., invalid keys, base64 errors).

## Security Notes

- In agent-readable mode, the plaintext appears in this conversation. It may reach the AI platform's servers as part of the conversation transcript.
- In courier mode, the plaintext is read from a file and base64-encoded. The agent handles it as opaque bytes but the base64 encoding is still in the tool call. For true content-blindness, the MCP server would need file-path-based I/O (not yet implemented).
- The sender's signing secret key is referenced by handle — it never appears in tool output.
- The sealed envelope is safe to transmit over any channel. It is encrypted and tamper-evident.
