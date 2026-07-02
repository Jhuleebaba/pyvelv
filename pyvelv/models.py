"""
Pydantic v2 schemas for Velvpay API request and response payloads.

All models use ``populate_by_name=True`` so they accept both the Python
attribute name and the optional JSON alias.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any, Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field

T = TypeVar("T")


# ---------------------------------------------------------------------------
# Generic API response wrapper
# ---------------------------------------------------------------------------

class APIResponse(BaseModel, Generic[T]):
    """
    Standard envelope returned by every Velvpay API endpoint.
    """

    model_config = ConfigDict(populate_by_name=True)

    status: str | None = None
    msg: str | None = None
    success: bool | None = None
    message: str | None = None
    reason: str | None = None
    err: str | None = None
    data: T | None = None

    @property
    def is_success(self) -> bool:
        """Helper property to check if the API call was successful."""
        if self.status == "success":
            return True
        if self.success is True:
            return True
        if self.message == "Successful" or self.msg == "successful":
            return True
        return False


# ---------------------------------------------------------------------------
# Payment Links / Initiation
# ---------------------------------------------------------------------------

class CreatePaymentLinkRequest(BaseModel):
    """Request body for ``POST /payment/initiate``."""

    model_config = ConfigDict(populate_by_name=True)

    title: str = Field(..., description="Payment title or name")
    description: str = Field(..., description="Human-readable description")
    amount: int = Field(..., description="Payment amount in kobo (100 kobo = ₦1). Example: 50000 = ₦500.00")
    is_naira: bool = Field(
        default=False,
        alias="isNaira",
        description="True if amount is in Naira, False if in Kobo",
    )
    charge_customer: bool = Field(
        default=True,
        alias="chargeCustomer",
        description="True if transaction fees should be charged to the customer",
    )
    post_payment_instructions: str | None = Field(
        default=None,
        alias="postPaymentInstructions",
        description="Instructions to show after payment is complete",
    )


class PaymentLink(BaseModel):
    """A Velvpay payment link object."""

    model_config = ConfigDict(populate_by_name=True)

    status: str
    msg: str | None = None
    link: str
    short: str
    amount_in_naira: Decimal | None = Field(default=None, alias="amountInNaira")
    currency: str | None = None
    title: str | None = None
    is_test: bool | None = Field(default=None, alias="isTest")



# ---------------------------------------------------------------------------
# Transactions
# ---------------------------------------------------------------------------

class TransactionData(BaseModel):
    """Inner transaction details data."""

    model_config = ConfigDict(populate_by_name=True)

    status: str
    message: str
    account_number: str = Field(alias="accountNumber")
    reference: str


class Transaction(BaseModel):
    """A Velvpay transaction record."""

    model_config = ConfigDict(populate_by_name=True)

    id: str = Field(alias="_id")
    account_number: str = Field(alias="accountNumber")
    tx_id: str = Field(alias="txId")
    link: str | None = None
    name: str | None = None
    amount: Decimal
    status: str
    channel: str
    type: str | None = None
    method: str | None = None
    date: str | None = None
    description: str | None = None
    metadata: list[dict[str, Any]] | None = None
    webhook_url: str | None = Field(default=None, alias="webhook_url")
    data: TransactionData | None = None


class TransactionList(BaseModel):
    """Paginated list of transactions."""

    model_config = ConfigDict(populate_by_name=True)

    data: list[Transaction]
    total: int
    page: int
