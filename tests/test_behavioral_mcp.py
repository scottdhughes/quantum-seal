"""Behavioral end-to-end tests for the post-quantum-mcp + quantum-seal stack.

Tests full cryptographic flows: keygen → seal → verify → open.
Requires liboqs and the post-quantum-mcp package to be installed.
Skips gracefully if dependencies are unavailable.

These replace file-presence-only tests with actual behavioral verification.
"""

import base64
import pytest

oqs = pytest.importorskip("oqs", reason="liboqs-python not installed")
pytest.importorskip("cryptography", reason="cryptography not installed")

from pqc_mcp_server.hybrid import (
    ENVELOPE_VERSION,
    hybrid_keygen,
    hybrid_seal,
    hybrid_auth_verify,
    SenderVerificationError,
)
from pqc_mcp_server.handlers_hybrid import (
    handle_hybrid_keygen,
    handle_hybrid_auth_seal,
    handle_hybrid_auth_open,
    handle_hybrid_auth_verify,
)
from pqc_mcp_server.handlers_pqc import handle_generate_keypair
from pqc_mcp_server.key_store import clear_store
from pqc_mcp_server.replay_cache import ReplayCache
from pqc_mcp_server.security_policy import SecurityPolicy


@pytest.fixture(autouse=True)
def clean_key_store():
    """Clear key store before each test."""
    clear_store()
    yield
    clear_store()


@pytest.fixture
def sender_identity():
    """Generate sender hybrid + signing keys via handles."""
    enc = handle_hybrid_keygen({"store_as": "test-sender"})
    sig = handle_generate_keypair({"algorithm": "ML-DSA-65", "store_as": "test-sender-signing"})
    return {"encryption": enc, "signing": sig}


@pytest.fixture
def recipient_identity():
    """Generate recipient hybrid keys via handles."""
    return handle_hybrid_keygen({"store_as": "test-recipient"})


class TestFullMessageFlow:
    """End-to-end: keygen → auth_seal → auth_verify → auth_open."""

    @pytest.mark.asyncio
    async def test_keygen_seal_verify_open(self, sender_identity, recipient_identity):
        """Full happy path using handles."""
        # Seal
        result = handle_hybrid_auth_seal(
            {
                "plaintext": "Hello from behavioral test!",
                "recipient_classical_public_key": recipient_identity["classical"]["public_key"],
                "recipient_pqc_public_key": recipient_identity["pqc"]["public_key"],
                "sender_key_store_name": "test-sender-signing",
            }
        )
        envelope = result["envelope"]
        assert envelope["version"] == ENVELOPE_VERSION
        assert "timestamp" in envelope
        assert "signature" in envelope

        # Verify (no secret keys needed)
        verify_result = handle_hybrid_auth_verify(
            {
                "envelope": envelope,
                "expected_sender_fingerprint": sender_identity["signing"]["fingerprint"],
            }
        )
        assert verify_result["verified"] is True
        assert verify_result["replay_seen"] is False

        # Open (requires recipient secret keys)
        open_result = await handle_hybrid_auth_open(
            {
                "envelope": envelope,
                "key_store_name": "test-recipient",
                "expected_sender_fingerprint": sender_identity["signing"]["fingerprint"],
            }
        )
        assert open_result["plaintext"] == "Hello from behavioral test!"
        assert open_result["authenticated"] is True

    @pytest.mark.asyncio
    async def test_wrong_recipient_cannot_open(self, sender_identity, recipient_identity):
        """Wrong recipient keys must fail at decryption."""
        from cryptography.exceptions import InvalidTag

        # Create a second recipient
        handle_hybrid_keygen({"store_as": "test-other"})

        result = handle_hybrid_auth_seal(
            {
                "plaintext": "secret",
                "recipient_classical_public_key": recipient_identity["classical"]["public_key"],
                "recipient_pqc_public_key": recipient_identity["pqc"]["public_key"],
                "sender_key_store_name": "test-sender-signing",
            }
        )

        with pytest.raises(InvalidTag):
            await handle_hybrid_auth_open(
                {
                    "envelope": result["envelope"],
                    "key_store_name": "test-other",
                    "expected_sender_fingerprint": sender_identity["signing"]["fingerprint"],
                }
            )

    def test_wrong_sender_fingerprint_rejected(self, sender_identity, recipient_identity):
        """Wrong expected sender must fail at verification."""
        result = handle_hybrid_auth_seal(
            {
                "plaintext": "data",
                "recipient_classical_public_key": recipient_identity["classical"]["public_key"],
                "recipient_pqc_public_key": recipient_identity["pqc"]["public_key"],
                "sender_key_store_name": "test-sender-signing",
            }
        )

        with pytest.raises(SenderVerificationError, match="does not match"):
            handle_hybrid_auth_verify(
                {
                    "envelope": result["envelope"],
                    "expected_sender_fingerprint": "0" * 64,
                }
            )


class TestVerifyRejectsInvalid:
    """Verify-only tool must reject malformed/anonymous envelopes."""

    def test_anonymous_envelope_rejected(self, recipient_identity):
        """Anonymous (unsigned) envelope must fail verification."""
        hybrid_keygen()
        envelope = hybrid_seal(
            b"anonymous",
            base64.b64decode(recipient_identity["classical"]["public_key"]),
            base64.b64decode(recipient_identity["pqc"]["public_key"]),
        )
        with pytest.raises(ValueError, match="not authenticated"):
            hybrid_auth_verify(envelope, expected_sender_fingerprint="0" * 64)

    def test_missing_signature_field(self, sender_identity, recipient_identity):
        """Envelope with signature stripped must fail."""
        result = handle_hybrid_auth_seal(
            {
                "plaintext": "data",
                "recipient_classical_public_key": recipient_identity["classical"]["public_key"],
                "recipient_pqc_public_key": recipient_identity["pqc"]["public_key"],
                "sender_key_store_name": "test-sender-signing",
            }
        )
        envelope = result["envelope"]
        del envelope["signature"]

        with pytest.raises(ValueError, match="Missing required"):
            hybrid_auth_verify(
                envelope,
                expected_sender_fingerprint=sender_identity["signing"]["fingerprint"],
            )


class TestSecretKeyGating:
    """Test include_secret_key redaction in pqc_generate_keypair."""

    def test_default_includes_secret_with_warning(self):
        result = handle_generate_keypair({"algorithm": "ML-DSA-65"})
        assert "secret_key" in result
        assert "warning" in result

    def test_redact_secrets(self):
        result = handle_generate_keypair(
            {
                "algorithm": "ML-DSA-65",
                "include_secret_key": False,
            }
        )
        assert "secret_key" not in result
        assert result["secret_key_redacted"] is True

    def test_store_as_never_includes_secret(self):
        result = handle_generate_keypair(
            {
                "algorithm": "ML-DSA-65",
                "store_as": "redact-test",
            }
        )
        assert "secret_key" not in result
        assert "handle" in result


class TestReplayDedup:
    """Test stateful replay cache behavior."""

    def test_replay_cache_basic(self, tmp_path):
        cache = ReplayCache(cache_file=str(tmp_path / "replay.json"), ttl_seconds=60)
        assert not cache.check("digest-1")
        assert not cache.check_and_mark("digest-1")  # first time = not replay
        assert cache.check("digest-1")  # now it's seen
        assert cache.check_and_mark("digest-1")  # replay

    def test_replay_cache_ttl_expiry(self, tmp_path):
        import time

        cache = ReplayCache(cache_file=str(tmp_path / "replay.json"), ttl_seconds=1)
        cache.check_and_mark("digest-expire")
        assert cache.check("digest-expire")
        # Simulate time passing
        cache._cache["digest-expire"] = time.time() - 1
        assert not cache.check("digest-expire")  # expired → pruned

    def test_replay_cache_persists(self, tmp_path):
        cache_file = str(tmp_path / "replay.json")
        c1 = ReplayCache(cache_file=cache_file, ttl_seconds=3600)
        c1.check_and_mark("persist-test")

        c2 = ReplayCache(cache_file=cache_file, ttl_seconds=3600)
        assert c2.check("persist-test")  # loaded from disk

    def test_replay_cache_corrupt_file(self, tmp_path):
        cache_file = tmp_path / "replay.json"
        cache_file.write_text("not json!!!")
        cache = ReplayCache(cache_file=str(cache_file), ttl_seconds=60)
        assert not cache.check("anything")  # reset, not crash


class TestSecurityPolicy:
    """Test PQC_REQUIRE_KEY_HANDLES enforcement."""

    def test_policy_default_allows_raw(self):
        policy = SecurityPolicy()
        policy.require_key_handles = False
        policy.check_no_raw_secrets(
            {"classical_secret_key": "abc"}, ["classical_secret_key"]
        )  # should not raise

    def test_policy_rejects_raw_when_enabled(self):
        policy = SecurityPolicy()
        policy.require_key_handles = True
        with pytest.raises(ValueError, match="rejected by server policy"):
            policy.check_no_raw_secrets({"classical_secret_key": "abc"}, ["classical_secret_key"])

    def test_policy_allows_handle_when_enabled(self):
        policy = SecurityPolicy()
        policy.require_key_handles = True
        policy.check_no_raw_secrets(
            {"key_store_name": "my-key"}, ["classical_secret_key"]
        )  # no raw secret → no error
