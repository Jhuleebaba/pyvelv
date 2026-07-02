"""
Transactions resource — ``client.transactions.*`` operations.
"""

from __future__ import annotations

from pyvelv.models import APIResponse, Transaction
from pyvelv.resources.base import BaseResource


class TransactionsResource(BaseResource):
    """
    Operations on Velvpay transactions.
    """

    async def get(self, transaction_id: str) -> APIResponse[Transaction]:
        """
        Retrieve details of a transaction.

        Args:
            transaction_id: The unique transaction identifier (e.g. FR-...).
        """
        raw = await self._client._request(
            "GET",
            "/payment/collection/transaction/details",
            params={"transaction_id": transaction_id},
        )
        return APIResponse[Transaction].model_validate(raw)

    async def verify(self, transaction_id: str) -> APIResponse[Transaction]:
        """
        Resolve/verify a transaction status.

        Args:
            transaction_id: The unique transaction identifier (e.g. FR-...).
        """
        raw = await self._client._request(
            "GET",
            "/payment/collection/transaction/resolve",
            params={"transaction_id": transaction_id},
        )
        return APIResponse[Transaction].model_validate(raw)
