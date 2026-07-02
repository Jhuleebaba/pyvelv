"""
Tests for the TransactionsResource.
"""

from __future__ import annotations

import respx
import pytest
from httpx import Response

from pyvelv.client import VelvpayClient
from pyvelv.models import Transaction
from tests.conftest import (
    MOCK_TRANSACTION,
    TEST_BASE_URL,
    make_success_response,
)


class TestTransactionsGet:
    """GET /payment/collection/transaction/details?transaction_id=..."""

    @respx.mock
    async def test_get_returns_transaction(self, velvpay_client: VelvpayClient):
        respx.get(f"{TEST_BASE_URL}/payment/collection/transaction/details?transaction_id=FR-IM5N2MKNJ40HHKOKNWIV").mock(
            return_value=Response(200, json=make_success_response(MOCK_TRANSACTION))
        )

        result = await velvpay_client.transactions.get("FR-IM5N2MKNJ40HHKOKNWIV")

        assert result.is_success is True
        assert isinstance(result.data, Transaction)
        assert result.data.id == "6329a83ffeff1341b81c451b"
        assert result.data.status == "pending"
        assert result.data.tx_id == "FR-IM5N2MKNJ40HHKOKNWIV"
        assert result.data.data.reference == "VELV-ET84wRey8lMe01ArLqfK"


class TestTransactionsVerify:
    """GET /payment/collection/transaction/resolve?transaction_id=..."""

    @respx.mock
    async def test_verify_returns_transaction(self, velvpay_client: VelvpayClient):
        respx.get(f"{TEST_BASE_URL}/payment/collection/transaction/resolve?transaction_id=FR-IM5N2MKNJ40HHKOKNWIV").mock(
            return_value=Response(200, json=make_success_response(MOCK_TRANSACTION))
        )

        result = await velvpay_client.transactions.verify("FR-IM5N2MKNJ40HHKOKNWIV")

        assert result.is_success is True
        assert isinstance(result.data, Transaction)
        assert result.data.tx_id == "FR-IM5N2MKNJ40HHKOKNWIV"
        assert int(result.data.amount) == 100
