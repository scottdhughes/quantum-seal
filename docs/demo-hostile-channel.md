# Hostile Channel Demo: PQC Encrypted Messaging Between AI Agents

Two Claude Code instances (Alice and Bob) exchange post-quantum encrypted messages through Eve's relay. Eve can read, copy, delay, or replay anything on the wire -- but she cannot forge messages or read plaintext.

## Cast
- **Alice** -- Claude Code with quantum-seal plugin (Terminal 1)
- **Bob** -- Claude Code with quantum-seal plugin (Terminal 2)
- **Eve** -- The attacker. Controls the relay. Sees all traffic.

---

## Act 1: Identity Setup

**Alice** (Terminal 1):
```
/setup-identity
```
Tool calls: `pqc_hybrid_keygen(store_as="alice-enc")`, `pqc_generate_keypair(algorithm="ML-DSA-65", store_as="alice-sig")`

Output:
```
Identity: alice
Encryption: mlkem768-x25519-sha3-256
  Classical fingerprint: a1b2c3d4...
  Words: sailboat-Eskimo-cobra-Atlantic-deadbolt-fortune
Signing: ML-DSA-65
  Fingerprint: e5f6a7b8...
  Words: dragon-December-crusade-hamburger-bison-frequency
```

**Bob** does the same on Terminal 2.

---

## Act 2: Key Exchange (Through Eve's Relay)

Alice publishes her identity card to the relay:
```
POST /mailboxes/<bob-fingerprint>
Body: { "type": "identity_card", "name": "alice", ... public keys ... }
```

**What Eve sees:** Alice's public keys and fingerprints. This is fine -- public material is meant to be public. Eve cannot derive secret keys from public keys (that's the whole point of asymmetric crypto).

Bob discovers Alice's card, verifies the fingerprint words out-of-band:
> "Alice, is your signing key **dragon-December-crusade-hamburger-bison-frequency**?"

---

## Act 3: Alice Sends a Sealed Message

**Alice**:
```
/secure-send "The quantum fox jumps over the lazy qubit" to bob
```
Tool call: `pqc_hybrid_auth_seal(plaintext="The quantum fox...", recipient_key_store_name="bob-enc", sender_key_store_name="alice-sig")`

The envelope transits through Eve's relay.

---

## Act 4: Eve Intercepts

**Eve** runs `pqc_envelope_inspect` on the intercepted envelope:

```json
{
  "version": "pqc-mcp-v3",
  "mode": "auth-seal",
  "suite": "mlkem768-x25519-sha3-256",
  "authenticated": true,
  "sender_key_fingerprint": "e5f6a7b8...",
  "ciphertext_size": 89,
  "pqc_ciphertext_size": 1088,
  "signature_size": 3309
}
```

**What Eve sees:** Metadata only. She knows Alice sent Bob a message, she knows the protocol version and ciphertext sizes. She does NOT see "The quantum fox jumps over the lazy qubit."

**Eve tries to decrypt:**
```
pqc_hybrid_auth_open(envelope=..., key_store_name="eve-keys", ...)
```
Result: `Error: Decryption failed: ciphertext, key, or envelope metadata is invalid`

**Eve tries to tamper with the ciphertext:**
She flips one byte in the `ciphertext` field and forwards it to Bob.

Bob's result: `Error: Decryption failed: ciphertext, key, or envelope metadata is invalid`
AES-256-GCM detects the tampering via its authentication tag.

**Eve tries to replay the message 25 hours later:**
Bob's result: `Error: Envelope is stale (90001s old, max 86400s). Possible replay attack.`

---

## Act 5: Bob Receives

**Bob**:
```
/verify-sender <envelope>
```
Tool call: `pqc_hybrid_auth_verify(envelope=..., expected_sender_fingerprint="e5f6a7b8...")`

Result: `verified: true, replay_seen: false`

```
/secure-receive <envelope>
```
Tool call: `pqc_hybrid_auth_open(envelope=..., key_store_name="bob-enc", expected_sender_fingerprint="e5f6a7b8...")`

Result:
```
plaintext: "The quantum fox jumps over the lazy qubit"
authenticated: true
sender_key_fingerprint: "e5f6a7b8..."
```

---

## Act 6: What Eve Cannot Do

| Attack | Protection | Algorithm |
|--------|-----------|-----------|
| Read plaintext | Hybrid encryption | X25519 + ML-KEM-768 + AES-256-GCM |
| Forge sender identity | Digital signature | ML-DSA-65 (FIPS 204) |
| Replay old messages | Signed timestamp + replay cache | SHA3-256 digest dedup |
| Tamper with any field | Authenticated encryption + AAD | GCM tag covers all headers |
| Downgrade auth to anon | Mode-bound key derivation | HKDF info includes mode label |
| Harvest now, decrypt later | Post-quantum KEM | ML-KEM-768 (FIPS 203) |
| Strip sender signature | Mode-bound AEAD | Different keys for anon vs auth |

## Performance (pqc_compare)

```
ML-KEM-768 vs X25519:  keygen 0.4x (faster!), public key 37x larger
ML-DSA-65 vs Ed25519:  sign 2.7x slower, verify 0.4x (faster!), signature 52x larger
```

The tradeoff: quantum resistance costs key/signature size, not speed.

## Self-Destruct Mode

Alice can set a sender-controlled TTL:
```
pqc_hybrid_auth_seal(plaintext="...", ..., max_decrypt_time=3600)
```
After 1 hour, Bob's decryption attempt returns:
```
Error: Envelope has expired (sender-imposed TTL of 3600s exceeded).
The sender set this message to self-destruct.
```

---

*Built with [post-quantum-mcp](https://github.com/scottdhughes/post-quantum-mcp) + [quantum-seal](https://github.com/scottdhughes/quantum-seal)*
