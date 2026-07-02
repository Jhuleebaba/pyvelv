"""
Tests for the PaymentLinksResource.
"""

from __future__ import annotations

import respx
import pytest
from httpx import Response

from pyvelv.client import VelvpayClient
from pyvelv.models import CreatePaymentLinkRequest, PaymentLink, Transaction
from tests.conftest import MOCK_PAYMENT_LINK, MOCK_TRANSACTION, TEST_BASE_URL, make_success_response


class TestPaymentLinksCreate:
    """POST /payment/initiate."""

    @respx.mock
    async def test_create_returns_payment_link(self, velvpay_client: VelvpayClient):
        """Creating a payment link must return a properly deserialised PaymentLink."""
        respx.post(f"{TEST_BASE_URL}/payment/initiate").mock(
            return_value=Response(200, json=MOCK_PAYMENT_LINK)
        )

        req = CreatePaymentLinkRequest(
            title="Test payment",
            description="Test payment link description",
            amount=100000,
            isNaira=False,
            chargeCustomer=True,
            postPaymentInstructions="hello",
        )
        result = await velvpay_client.payment_links.create(req)

        assert isinstance(result, PaymentLink)
        assert result.status == "success"
        assert result.link == "https://api.velvpay.com/payment/link/XYZ"
        assert result.short == "XYZ"
        assert int(result.amount_in_naira) == 1000
        assert result.currency == "NGN"
        assert result.is_test is True


class TestPaymentLinksGet:
    """GET /payment/collection/transaction/details?transaction_id=..."""

    @respx.mock
    async def test_get_returns_transaction(self, velvpay_client: VelvpayClient):
        respx.get(f"{TEST_BASE_URL}/payment/collection/transaction/details?transaction_id=FR-ORETLB1VGHWZOJLAJTSY").mock(
            return_value=Response(200, json=make_success_response(MOCK_TRANSACTION))
        )

        result = await velvpay_client.payment_links.get("FR-ORETLB1VGHWZOJLAJTSY")

        assert result.is_success is True
        assert isinstance(result.data, Transaction)
        assert result.data.id == "6329a83ffeff1341b81c451b"
        assert result.data.tx_id == "FR-IM5N2MKNJ40HHKOKNWIV"
