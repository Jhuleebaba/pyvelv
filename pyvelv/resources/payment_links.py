"""
Payment Links resource — ``client.payment_links.*`` operations.
"""

from __future__ import annotations

from pyvelv.models import APIResponse, CreatePaymentLinkRequest, PaymentLink, Transaction
from pyvelv.resources.base import BaseResource


class PaymentLinksResource(BaseResource):
    """
    Operations on Velvpay payment links (Payment Initiation).
    """

    async def create(self, data: CreatePaymentLinkRequest) -> PaymentLink:
        """
        Initiate a new payment.

        Args:
            data: The payment initiation payload.

        Returns:
            A :class:`~pyvelv.models.PaymentLink` object representing the flat response.
        """
        payload = data.model_dump(mode="json", by_alias=True, exclude_none=True)
        raw = await self._client._request("POST", "/payment/initiate", json=payload)
        return PaymentLink.model_validate(raw)

    async def get(self, transaction_id: str) -> APIResponse[Transaction]:
        """
        Retrieve details of an initiated payment.

        Args:
            transaction_id: The unique transaction identifier (e.g. FR-...).
        """
        raw = await self._client._request(
            "GET",
            "/payment/collection/transaction/details",
            params={"transaction_id": transaction_id},
        )
        return APIResponse[Transaction].model_validate(raw)
