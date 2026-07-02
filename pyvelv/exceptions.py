"""
Exception hierarchy for the Pyvelv SDK.

All exceptions inherit from :class:`VelvpayError` so callers can catch
a single base class for broad error handling.
"""

from __future__ import annotations

from typing import Any


class VelvpayError(Exception):
    """Base exception for all Velvpay SDK errors."""

    def __init__(self, message: str = "An unexpected Velvpay error occurred") -> None:
        self.message = message
        super().__init__(self.message)


class VelvpayAPIError(VelvpayError):
    """
    Raised when the Velvpay API returns a non-2xx HTTP response.

    Attributes:
        status_code: The HTTP status code.
        response_body: The raw response body (decoded JSON or string).
    """

    def __init__(
        self,
        message: str,
        status_code: int,
        response_body: Any = None,
    ) -> None:
        self.status_code = status_code
        self.response_body = response_body
        super().__init__(f"[HTTP {status_code}] {message}")


class VelvpayAuthError(VelvpayAPIError):
    """
    Raised when the API rejects the request due to authentication failure.

    Triggered by HTTP 401 (Unauthorized) and 403 (Forbidden) responses.
    """

    def __init__(
        self,
        message: str = "Authentication failed",
        status_code: int = 401,
        response_body: Any = None,
    ) -> None:
        super().__init__(message, status_code, response_body)


class VelvpayValidationError(VelvpayError):
    """
    Raised when request data fails Pydantic validation before being sent.

    Attributes:
        errors: The list of validation error details from Pydantic.
    """

    def __init__(self, message: str, errors: list[Any] | None = None) -> None:
        self.errors = errors or []
        super().__init__(message)
