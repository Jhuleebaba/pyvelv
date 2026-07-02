"""
Async HTTP client for the Velvpay payment gateway.

Usage::

    async with VelvpayClient(
        secret_key="sk_...",
        public_key="pk_...",
        encryption_key="enc_...",
    ) as client:
        link = await client.payment_links.create(...)
"""

from __future__ import annotations

from typing import Any
import hmac
import logging
import uuid

import httpx

from pyvelv.crypto import generate_api_key_header
from pyvelv.exceptions import VelvpayAPIError, VelvpayAuthError

_logger = logging.getLogger("pyvelv")


class VelvpayClient:
    """
    Asynchronous client for the Velvpay API.

    Args:
        secret_key: Your Velvpay merchant secret key.
        public_key: Your Velvpay merchant public key.
        encryption_key: Your Velvpay encryption key/passphrase.
        base_url: API base URL. If not provided, it is chosen based on the sandbox flag.
        sandbox: If True, uses the test sandbox base URL.
        timeout: Request timeout in seconds.
    """

    _PRODUCTION_BASE_URL = "https://api.velvpay.com/api/v1/service"
    _SANDBOX_BASE_URL = "https://testapi.velvpay.io"

    def __init__(
        self,
        secret_key: str,
        public_key: str,
        encryption_key: str,
        *,
        base_url: str | None = None,
        sandbox: bool = False,
        timeout: float = 30.0,
    ) -> None:
        if not secret_key:
            raise ValueError("secret_key must not be empty")
        if not public_key:
            raise ValueError("public_key must not be empty")
        if not encryption_key:
            raise ValueError("encryption_key must not be empty")

        self._secret_key = secret_key
        self._public_key = public_key
        self._encryption_key = encryption_key



        if base_url:
            self._base_url = base_url.rstrip("/")
        else:
            self._base_url = (self._SANDBOX_BASE_URL if sandbox else self._PRODUCTION_BASE_URL).rstrip("/")

        self._timeout = timeout
        self._http: httpx.AsyncClient | None = None

        # Lazily-initialised resource namespaces
        self._payment_links: PaymentLinksResource | None = None
        self._transactions: TransactionsResource | None = None

    # ------------------------------------------------------------------
    # HTTP transport helpers
    # ------------------------------------------------------------------

    @property
    def http(self) -> httpx.AsyncClient:
        """Return (or lazily create) the underlying ``httpx.AsyncClient``."""
        if self._http is None or self._http.is_closed:
            self._http = httpx.AsyncClient(
                base_url=self._base_url,
                timeout=self._timeout,
                verify=True,  # Never disable for payment traffic
            )
        return self._http

    async def _request(
        self,
        method: str,
        path: str,
        *,
        json: Any | None = None,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Send an authenticated request to the Velvpay API.

        Dynamic headers including the encrypted `api-key` and `reference-id`
        are generated for each call.
        """
        reference_id = f"ref_{uuid.uuid4().hex}"
        api_key = generate_api_key_header(
            secret_key=self._secret_key,
            public_key=self._public_key,
            reference_id=reference_id,
            encryption_key=self._encryption_key,
        )

        headers = {
            "Content-Type": "application/json",
            "api-key": api_key,
            "public-key": self._public_key,
            "reference-id": reference_id,
        }

        if method.upper() == "POST":
            headers["idempotencykey"] = str(uuid.uuid4())

        response = await self.http.request(
            method,
            path,
            json=json,
            params=params,
            headers=headers,
        )

        # --- Error handling ---
        if response.status_code in (401, 403):
            body = self._safe_json(response)
            raise VelvpayAuthError(
                message=body.get("reason", "Authentication failed") if isinstance(body, dict) else "Authentication failed",
                status_code=response.status_code,
                response_body=body,
            )

        if not (200 <= response.status_code < 300):
            body = self._safe_json(response)
            msg = None
            if isinstance(body, dict):
                msg = body.get("reason") or body.get("msg") or body.get("err") or body.get("message")
            raise VelvpayAPIError(
                message=msg or response.reason_phrase or "API request failed",
                status_code=response.status_code,
                response_body=body,
            )

        return response.json()

    @staticmethod
    def _safe_json(response: httpx.Response) -> Any:
        """Attempt to parse JSON from a response, falling back to the raw text."""
        try:
            return response.json()
        except Exception:
            return response.text

    def verify_webhook(self, api_key_header: str, reference_id_header: str) -> bool:
        """
        Verify that a webhook request was sent by Velvpay.

        Decrypts the 'api-key' signature header using the client's encryption key
        and validates that it matches the concatenated credentials and reference ID.

        Args:
            api_key_header: The 'api-key' value from the request headers.
            reference_id_header: The 'reference-id' value from the request headers.

        Returns:
            True if the signature is valid, False otherwise.
        """
        from pyvelv.crypto import decrypt_aes_256_cbc

        try:
            decrypted = decrypt_aes_256_cbc(api_key_header, self._encryption_key)
            expected = self._secret_key + self._public_key + reference_id_header
            return hmac.compare_digest(decrypted, expected)
        except (ValueError, KeyError) as exc:
            _logger.debug("Webhook verification failed: %s", exc)
            return False

    # ------------------------------------------------------------------
    # Resource namespaces (lazy properties)
    # ------------------------------------------------------------------


    @property
    def payment_links(self) -> PaymentLinksResource:
        """Access payment link operations."""
        if self._payment_links is None:
            from pyvelv.resources.payment_links import PaymentLinksResource
            self._payment_links = PaymentLinksResource(self)
        return self._payment_links

    @property
    def transactions(self) -> TransactionsResource:
        """Access transaction operations."""
        if self._transactions is None:
            from pyvelv.resources.transactions import TransactionsResource
            self._transactions = TransactionsResource(self)
        return self._transactions

    # ------------------------------------------------------------------
    # Context manager & lifecycle
    # ------------------------------------------------------------------

    async def close(self) -> None:
        """Close the underlying HTTP client and release resources."""
        if self._http and not self._http.is_closed:
            await self._http.aclose()

    async def __aenter__(self) -> VelvpayClient:
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        await self.close()

    def __repr__(self) -> str:
        return f"<VelvpayClient base_url={self._base_url!r} keys=***>"

    def __str__(self) -> str:
        return self.__repr__()


# Forward-reference imports so the type annotations above resolve at runtime.
# Actual classes are imported lazily inside the properties to avoid circular
# imports.
from pyvelv.resources.payment_links import PaymentLinksResource  # noqa: E402
from pyvelv.resources.transactions import TransactionsResource  # noqa: E402
