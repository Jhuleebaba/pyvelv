"""
Tests for the crypto module — EVP_BytesToKey derivation and AES-256-CBC.
"""

from __future__ import annotations

import base64
from unittest.mock import patch

import pytest

from pyvelv.crypto import (
    _evp_bytes_to_key,
    decrypt_aes_256_cbc,
    encrypt_aes_256_cbc,
    generate_api_key_header,
)


class TestEvpBytesToKey:
    """Unit tests for the raw EVP_BytesToKey derivation function."""

    def test_key_and_iv_lengths(self):
        """Derived key must be 32 bytes and IV must be 16 bytes."""
        key, iv = _evp_bytes_to_key(b"password", b"saltsalt")
        assert len(key) == 32
        assert len(iv) == 16

    def test_deterministic_with_same_inputs(self):
        """Same password + salt must always produce the same key/IV."""
        a = _evp_bytes_to_key(b"secret", b"12345678")
        b = _evp_bytes_to_key(b"secret", b"12345678")
        assert a == b

    def test_different_salts_produce_different_keys(self):
        """Different salts must produce different derived material."""
        a = _evp_bytes_to_key(b"secret", b"salt_aaa")
        b = _evp_bytes_to_key(b"secret", b"salt_bbb")
        assert a != b

    def test_none_salt_accepted(self):
        """A None salt must not raise and must produce valid output."""
        key, iv = _evp_bytes_to_key(b"password", None)
        assert len(key) == 32
        assert len(iv) == 16


class TestEncryptDecrypt:
    """Round-trip tests for AES-256-CBC encrypt/decrypt."""

    @pytest.mark.parametrize(
        "plaintext",
        [
            "hello world",
            "",
            "sk_testpk_testref_123",
            "a" * 1024,  # multi-block plaintext
        ],
    )
    def test_round_trip(self, plaintext: str):
        """Encrypting then decrypting must yield the original plaintext."""
        passphrase = "my-secret-key"
        encrypted = encrypt_aes_256_cbc(plaintext, passphrase)
        decrypted = decrypt_aes_256_cbc(encrypted, passphrase)
        assert decrypted == plaintext

    def test_output_is_valid_base64(self):
        """The encrypted output must be valid base64."""
        encrypted = encrypt_aes_256_cbc("test", "key")
        raw = base64.b64decode(encrypted)
        assert isinstance(raw, bytes)

    def test_output_starts_with_salted_magic(self):
        """The decoded envelope must begin with the 'Salted__' magic header."""
        encrypted = encrypt_aes_256_cbc("test", "key")
        raw = base64.b64decode(encrypted)
        assert raw[:8] == b"Salted__"

    def test_deterministic_with_fixed_salt(self):
        """With a patched os.urandom, output must be deterministic."""
        fixed_salt = b"\x01\x02\x03\x04\x05\x06\x07\x08"
        with patch("pyvelv.crypto.os.urandom", return_value=fixed_salt):
            a = encrypt_aes_256_cbc("payload", "key123")
            b = encrypt_aes_256_cbc("payload", "key123")
        assert a == b

    def test_invalid_envelope_raises(self):
        """Decrypting garbage that lacks the Salted__ header must raise."""
        bogus = base64.b64encode(b"not_salted_data_here_1234567890").decode()
        with pytest.raises(ValueError, match="Salted__"):
            decrypt_aes_256_cbc(bogus, "key")


class TestGenerateApiKeyHeader:
    """Tests for the high-level api-key header generator."""

    def test_returns_base64_string(self):
        """The header value must be a valid base64 string."""
        header = generate_api_key_header(
            secret_key="sk_test",
            public_key="pk_test",
            reference_id="ref_123",
            encryption_key="enc_key",
        )
        raw = base64.b64decode(header)
        assert raw[:8] == b"Salted__"

    def test_correct_decryption_with_encryption_key(self):
        """The generated header must decrypt back to secretKey + publicKey + referenceId using the encryption key."""
        sec = "sk_test"
        pub = "pk_test"
        ref = "ref_123"
        enc = "enc_key"
        header = generate_api_key_header(sec, pub, ref, enc)
        decrypted = decrypt_aes_256_cbc(header, enc)
        assert decrypted == sec + pub + ref
