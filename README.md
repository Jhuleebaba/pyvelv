# pyvelv

> Asynchronous Python SDK for the Velvpay payment gateway. Production-ready with automatic OpenSSL-compliant AES-256-CBC header signature generation, Pydantic v2 validation, and constant-time webhook verification.

---

## Installation

```bash
pip install pyvelv
```

---

## Quick Start

### 1. Configuration
Store your Velvpay credentials in your application's environment configuration (e.g., a `.env` file):

```env
VELVPAY_SECRET_KEY=SK_LIVE_your_secret_key_here
VELVPAY_PUBLIC_KEY=PK_LIVE_your_public_key_here
VELVPAY_ENCRYPTION_KEY=your_encryption_key_here
```

### 2. Client Initialization
Initialize the client explicitly with the loaded credentials:

```python
import os
from dotenv import load_dotenv
from pyvelv import Velvpay

load_dotenv()

client = Velvpay(
    secret_key=os.getenv("VELVPAY_SECRET_KEY"),
    public_key=os.getenv("VELVPAY_PUBLIC_KEY"),
    encryption_key=os.getenv("VELVPAY_ENCRYPTION_KEY"),
    sandbox=False,  # Set True for test environment
)
```

---

## Usage Guide

### A. Initiate a Payment

All amounts are specified in **kobo** (100 kobo = ₦1). For example, `50000` kobo = ₦500.00.

```python
from pyvelv.models import CreatePaymentLinkRequest

async def run_checkout():
    req = CreatePaymentLinkRequest(
        title="Order #9024",
        description="Premium Plan Subscription",
        amount=50000,  # ₦500.00 in kobo
    )

    async with client:
        link = await client.payment_links.create(req)

        print(f"Status:       {link.status}")
        print(f"Payment Link: {link.link}")
        print(f"Short Code:   {link.short}")
        print(f"Amount (NGN): ₦{link.amount_in_naira}")
        print(f"Currency:     {link.currency}")
```

### B. Verify Webhooks (Backend-to-Backend Security)

Protect your webhook routes by validating Velvpay request signatures. The SDK uses constant-time comparison to prevent timing attacks.

```python
from fastapi import FastAPI, Request, Header, HTTPException
import json

app = FastAPI()

@app.post("/webhooks/velvpay")
async def velvpay_webhook(
    request: Request,
    api_key: str = Header(..., alias="api-key"),
    reference_id: str = Header(..., alias="reference-id"),
):
    # 1. Validate signature authenticity
    is_valid = client.verify_webhook(
        api_key_header=api_key,
        reference_id_header=reference_id,
    )
    if not is_valid:
        raise HTTPException(status_code=401, detail="Invalid signature")

    # 2. Parse event body
    event = await request.json()

    # 3. Handle confirmed transactions
    if event.get("status") == "successful":
        transaction_id = event.get("txId")
        # Update order status in your database...

    return {"status": "accepted"}
```

### C. Verify / Get Transaction Status

Fetch or resolve a transaction's status using its unique transaction ID:

```python
async def check_status(transaction_id: str):
    async with client:
        # Fetch current details
        details = await client.transactions.get(transaction_id)
        print(f"Status: {details.data.status}")

        # Explicitly verify/resolve on Velvpay's servers
        resolution = await client.transactions.verify(transaction_id)
        print(f"Verified: {resolution.data.status}")
```

---

## Security

- **Constant-time signature verification** — Webhook validation uses `hmac.compare_digest()` to prevent timing attacks.
- **TLS enforced** — All API requests are made over HTTPS with certificate verification explicitly enabled.
- **No credential leakage** — API keys are never included in logs, repr output, or error messages.
- **Scoped exception handling** — Crypto failures in webhook verification are caught narrowly and logged at DEBUG level for diagnostics.

## Features

- **Zero-Abstraction Crypto Layer** — Automatic generation of the required encrypted `api-key` header on every request.
- **Auto-injected Headers** — Correct headers (`public-key`, fresh `reference-id`, and `idempotencykey`) are automatically handled.
- **Pydantic v2 Validation** — All request payloads and response bodies are typed and parsed with Pydantic v2.
- **Context Manager Support** — Uses `async with` for automatic connection pooling and clean disposal of `httpx` clients.
- **Kobo-first Amounts** — All amounts are in kobo (100 kobo = ₦1) to avoid floating-point decimal issues.

---

## License

MIT
