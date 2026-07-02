"""
Tests for the VelvpayClient core — headers, error handling, lifecycle.
"""

from __future__ import annotations

import pytest
import respx
from httpx import Response

from pyvelv import Velvpay, VelvpayClient
from pyvelv.exceptions import VelvpayAPIError, VelvpayAuthError
from tests.conftest import TEST_BASE_URL


class TestClientInit:
    """Construction and ergonomics."""

    def test_velvpay_alias(self):
        """``Velvpay`` must be the same class as ``VelvpayClient``."""
        assert Velvpay is VelvpayClient

    def test_import_from_root(self):
        """Users must be able to ``from pyvelv import Velvpay``."""
        from pyvelv import Velvpay as V  # noqa: F401
        assert V is VelvpayClient

    def test_missing_keys_raises(self):
        """Empty keys must raise immediately."""
        with pytest.raises(ValueError, match="secret_key"):
            VelvpayClient(secret_key="", public_key="pk", encryption_key="enc")
        with pytest.raises(ValueError, match="public_key"):
            VelvpayClient(secret_key="sk", public_key="", encryption_key="enc")
        with pytest.raises(ValueError, match="encryption_key"):
            VelvpayClient(secret_key="sk", public_key="pk", encryption_key="")

    def test_sandbox_url_mapping(self):
        """Sandbox flag must resolve to the test API base URL."""
        client = VelvpayClient(secret_key="sk", public_key="pk", encryption_key="enc", sandbox=True)
        assert client._base_url == "https://testapi.velvpay.io"

        client_prod = VelvpayClient(secret_key="sk", public_key="pk", encryption_key="enc", sandbox=False)
        assert client_prod._base_url == "https://api.velvpay.com/api/v1/service"


class TestRequestHeaders:
    """Ensure the required headers are present and well-formed."""

    @respx.mock
    async def test_required_headers_present(self, velvpay_client: VelvpayClient, public_key: str):
        """Every request must carry all required headers."""
        route = respx.get(f"{TEST_BASE_URL}/ping").mock(
            return_value=Response(200, json={"status": "success", "msg": "pong", "data": None})
        )

        await velvpay_client._request("GET", "/ping")

        assert route.called
        request = route.calls.last.request
        assert "api-key" in request.headers
        assert "public-key" in request.headers
        assert "reference-id" in request.headers
        assert "Content-Type" in request.headers

        assert request.headers["public-key"] == public_key
        assert request.headers["Content-Type"] == "application/json"
        assert len(request.headers["api-key"]) > 0
        assert len(request.headers["reference-id"]) > 0

    @respx.mock
    async def test_idempotency_key_on_post(self, velvpay_client: VelvpayClient):
        """POST requests must carry an ``idempotencykey`` header."""
        route = respx.post(f"{TEST_BASE_URL}/payment/initiate").mock(
            return_value=Response(200, json={"status": "success", "msg": "ok", "data": None})
        )

        await velvpay_client._request("POST", "/payment/initiate", json={"test": "data"})

        assert route.called
        request = route.calls.last.request
        assert "idempotencykey" in request.headers
        assert len(request.headers["idempotencykey"]) > 0


class TestErrorHandling:
    """HTTP error responses must raise the correct exception."""

    @respx.mock
    async def test_401_raises_auth_error(self, velvpay_client: VelvpayClient):
        respx.get(f"{TEST_BASE_URL}/secure").mock(
            return_value=Response(401, json={"status": "error", "reason": "invalid secret key provided"})
        )
        with pytest.raises(VelvpayAuthError) as exc_info:
            await velvpay_client._request("GET", "/secure")
        assert exc_info.value.status_code == 401
        assert "invalid secret key" in exc_info.value.message

    @respx.mock
    async def test_403_raises_auth_error(self, velvpay_client: VelvpayClient):
        respx.get(f"{TEST_BASE_URL}/admin").mock(
            return_value=Response(403, json={"status": "error", "reason": "Forbidden"})
        )
        with pytest.raises(VelvpayAuthError) as exc_info:
            await velvpay_client._request("GET", "/admin")
        assert exc_info.value.status_code == 403

    @respx.mock
    async def test_500_raises_api_error(self, velvpay_client: VelvpayClient):
        respx.get(f"{TEST_BASE_URL}/fail").mock(
            return_value=Response(500, json={"status": "error", "reason": "Internal Server Error"})
        )
        with pytest.raises(VelvpayAPIError) as exc_info:
            await velvpay_client._request("GET", "/fail")
        assert exc_info.value.status_code == 500

    @respx.mock
    async def test_api_error_contains_response_body(self, velvpay_client: VelvpayClient):
        body = {"status": "error", "reason": "Rate limited", "err": "check limit"}
        respx.get(f"{TEST_BASE_URL}/limited").mock(
            return_value=Response(429, json=body)
        )
        with pytest.raises(VelvpayAPIError) as exc_info:
            await velvpay_client._request("GET", "/limited")
        assert exc_info.value.response_body == body



class TestWebhookVerification:
    """Webhook signature verification."""

    def test_verify_webhook_success(self, velvpay_client: VelvpayClient, secret_key: str, public_key: str, encryption_key: str):
        """Should return True for a valid signature matching the keys and reference ID."""
        from pyvelv.crypto import generate_api_key_header

        ref_id = "test_webhook_ref_99"
        valid_api_key = generate_api_key_header(secret_key, public_key, ref_id, encryption_key)

        assert velvpay_client.verify_webhook(valid_api_key, ref_id) is True

    def test_verify_webhook_failure(self, velvpay_client: VelvpayClient):
        """Should return False if signature is invalid or reference ID does not match."""
        assert velvpay_client.verify_webhook("garbage_signature", "some_ref") is False


class TestContextManager:
    """Lifecycle / context-manager behaviour."""

    async def test_async_context_manager(self, secret_key: str, public_key: str, encryption_key: str):
        """``async with`` must open and cleanly close the client."""
        async with VelvpayClient(
            secret_key=secret_key,
            public_key=public_key,
            encryption_key=encryption_key,
        ) as client:
            assert client.http is not None
            assert not client.http.is_closed
        # After exiting, the HTTP client should be closed
        assert client._http.is_closed
