"""
Pyvelv — Async Python SDK for the Velvpay payment gateway.

Usage:
    from pyvelv import Velvpay

    async with Velvpay(secret_key="sk_...") as client:
        link = await client.payment_links.create(...)
"""

from pyvelv.client import VelvpayClient

# Ergonomic alias so users can do: from pyvelv import Velvpay
Velvpay = VelvpayClient

__version__ = "0.1.3"

__all__ = [
    "Velvpay",
    "VelvpayClient",
    "__version__",
]
