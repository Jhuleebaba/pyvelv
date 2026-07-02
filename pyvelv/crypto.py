"""
Crypto module for Velvpay API key header generation.

Implements the legacy OpenSSL EVP_BytesToKey key derivation routine
for AES-256-CBC encryption. The generated ciphertext is used as the
`api-key` header value on every API request.

OpenSSL envelope format:
    base64( b"Salted__" + salt(8 bytes) + ciphertext )
"""

from __future__ import annotations

import base64
import hashlib

import os
from typing import Any

from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad


def _evp_bytes_to_key(
    password: bytes,
    salt: bytes | None,
    key_len: int = 32,
    iv_len: int = 16,
) -> tuple[bytes, bytes]:
    """
    Derive key and IV using the OpenSSL EVP_BytesToKey algorithm.

    This replicates the behaviour of ``openssl enc -aes-256-cbc`` with MD5 as
    the digest function.

    Args:
        password: The passphrase as raw bytes.
        salt: An 8-byte salt, or ``None`` for unsalted derivation.
        key_len: Desired key length in bytes (32 for AES-256).
        iv_len: Desired IV length in bytes (16 for AES-CBC).

    Returns:
        A ``(key, iv)`` tuple of the derived key and initialisation vector.
    """
    d_tot = b""
    d_list: list[bytes] = []

    while len(d_tot) < (key_len + iv_len):
        prev = d_list[-1] if d_list else b""
        # MD5 is required here to match the OpenSSL EVP_BytesToKey algorithm
        # used by CryptoJS on the Velvpay server. Do not replace with SHA-256.
        d_i = hashlib.md5(prev + password + (salt or b"")).digest()
        d_tot += d_i
        d_list.append(d_i)

    return d_tot[:key_len], d_tot[key_len : key_len + iv_len]


def encrypt_aes_256_cbc(plaintext: str, passphrase: str) -> str:
    """
    Encrypt *plaintext* with AES-256-CBC using the OpenSSL envelope format.

    1. Generate a random 8-byte salt.
    2. Derive ``(key, iv)`` via :func:`_evp_bytes_to_key`.
    3. PKCS#7-pad the plaintext and encrypt.
    4. Return ``base64(b"Salted__" + salt + ciphertext)``.

    Args:
        plaintext: The data to encrypt (UTF-8 string).
        passphrase: The secret passphrase used for key derivation.

    Returns:
        A base64-encoded string in the standard OpenSSL format.
    """
    salt = os.urandom(8)
    key, iv = _evp_bytes_to_key(passphrase.encode("utf-8"), salt)

    cipher = AES.new(key, AES.MODE_CBC, iv)
    padded = pad(plaintext.encode("utf-8"), AES.block_size)
    ciphertext = cipher.encrypt(padded)

    # OpenSSL envelope: "Salted__" magic + salt + ciphertext
    envelope = b"Salted__" + salt + ciphertext
    return base64.b64encode(envelope).decode("ascii")


def decrypt_aes_256_cbc(encoded: str, passphrase: str) -> str:
    """
    Decrypt an OpenSSL-format AES-256-CBC ciphertext.

    This is the inverse of :func:`encrypt_aes_256_cbc` and is provided
    primarily for testing round-trip correctness.

    Args:
        encoded: The base64-encoded OpenSSL envelope.
        passphrase: The passphrase that was used for encryption.

    Returns:
        The original plaintext string.

    Raises:
        ValueError: If the envelope does not start with ``Salted__``.
    """
    raw = base64.b64decode(encoded)

    if not raw.startswith(b"Salted__"):
        raise ValueError("Invalid OpenSSL envelope: missing 'Salted__' magic header")

    salt = raw[8:16]
    ciphertext = raw[16:]

    key, iv = _evp_bytes_to_key(passphrase.encode("utf-8"), salt)
    cipher = AES.new(key, AES.MODE_CBC, iv)
    plaintext = unpad(cipher.decrypt(ciphertext), AES.block_size)

    return plaintext.decode("utf-8")


def generate_api_key_header(
    secret_key: str,
    public_key: str,
    reference_id: str,
    encryption_key: str,
) -> str:
    """
    Generate the ``api-key`` header value for a Velvpay API request.

    The payload (secretKey + publicKey + referenceId) is encrypted
    using AES-256-CBC with the merchant's encryption key.

    Args:
        secret_key: The merchant's Velvpay secret key.
        public_key: The merchant's Velvpay public key.
        reference_id: The unique reference ID for the request.
        encryption_key: The merchant's Velvpay encryption key.

    Returns:
        A base64-encoded encrypted string suitable for the ``api-key`` header.
    """
    payload = secret_key + public_key + reference_id
    return encrypt_aes_256_cbc(payload, encryption_key)

