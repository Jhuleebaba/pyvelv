"""
Base resource class that all Velvpay API resource namespaces inherit from.

Each resource receives a reference to the parent :class:`~pyvelv.client.VelvpayClient`
so it can make authenticated HTTP requests through the shared transport.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pyvelv.client import VelvpayClient


class BaseResource:
    """
    Abstract base for API resource namespaces.

    Subclasses access ``self._client._request(...)`` to call the API.
    """

    def __init__(self, client: VelvpayClient) -> None:
        self._client = client

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} client={self._client!r}>"
