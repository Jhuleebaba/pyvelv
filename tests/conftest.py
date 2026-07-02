"""
Shared fixtures for the pyvelv test suite.
"""

from __future__ import annotations

import pytest

from pyvelv.client import VelvpayClient


TEST_SECRET_KEY = "test_sk_live_abcdef1234567890"
TEST_PUBLIC_KEY = "test_pk_live_1234567890abcdef"
TEST_ENCRYPTION_KEY = "test_enc_passphrase_secret"
TEST_BASE_URL = "https://api.velvpay.com/api/v1/service"


@pytest.fixture
def secret_key() -> str:
    """Return a deterministic test secret key."""
    return TEST_SECRET_KEY


@pytest.fixture
def public_key() -> str:
    """Return a deterministic test public key."""
    return TEST_PUBLIC_KEY


@pytest.fixture
def encryption_key() -> str:
    """Return a deterministic test encryption key."""
    return TEST_ENCRYPTION_KEY


@pytest.fixture
async def velvpay_client(secret_key: str, public_key: str, encryption_key: str):
    """Yield a VelvpayClient wired to the test base URL."""
    async with VelvpayClient(
        secret_key=secret_key,
        public_key=public_key,
        encryption_key=encryption_key,
        base_url=TEST_BASE_URL,
    ) as client:
        yield client


# ---------------------------------------------------------------------------
# Canonical mock response payloads matching official API specification
# ---------------------------------------------------------------------------

MOCK_PAYMENT_LINK = {
    "status": "success",
    "msg": "payment instantiated successfully",
    "link": "https://api.velvpay.com/payment/link/XYZ",
    "short": "XYZ",
    "amountInNaira": 1000.00,
    "currency": "NGN",
    "title": "Test Title",
    "isTest": True,
}


MOCK_TRANSACTION = {
    "_id": "6329a83ffeff1341b81c451b",
    "accountNumber": "4600555555",
    "txId": "FR-IM5N2MKNJ40HHKOKNWIV",
    "link": "b-velv_technology",
    "name": "velv technology link",
    "amount": 100,
    "status": "pending",
    "channel": "API",
    "type": "primary",
    "method": "Payment Link",
    "date": "2022-09-20T11:47:10.000Z",
    "data": {
        "status": "00",
        "message": "Successful",
        "accountNumber": "4600555555",
        "reference": "VELV-ET84wRey8lMe01ArLqfK"
    }
}


def make_success_response(data: dict | list) -> dict:
    """Wrap *data* in a standard Velvpay API success envelope."""
    return {
        "status": "success",
        "msg": "successful",
        "data": data,
    }
