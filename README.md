# pyvelv

> Asynchronous Python SDK for the Velvpay payment gateway. Fully production-ready, featuring automatic OpenSSL-compliant AES-256-CBC header signature generation, request validation using Pydantic v2, and secure webhook verification.

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
VELVPAY_SECRET_KEY=sk_live_your_secret_key_here
VELVPAY_PUBLIC_KEY=pk_live_your_public_key_here
VELVPAY_ENCRYPTION_KEY=enc_live_your_encryption_key_here
VELVPAY_SANDBOX=True
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
    sandbox=os.getenv("VELVPAY_SANDBOX", "False").lower() == "true",
)
```

---

## Usage Guide

### A. Initiate a Payment (Generate Virtual Account)
Request a new virtual account for payment collection. All amounts are specified in **kobo** (e.g., `50000` is NGN 500.00).

```python
from pyvelv.models import CreatePaymentLinkRequest

async def run_checkout():
    # 1. Setup payment details
    req = CreatePaymentLinkRequest(
        title="Order #9024",
        description="Premium Plan Subscription",
        amount=50000,
        isNaira=False,
        chargeCustomer=True,
    )

    # 2. Call endpoint (POST /payment/initiate)
    async with client:
        response = await client.payment_links.create(req)

        if response.is_success:
            print(f"Bank Name:      {response.data.bank}")
            print(f"Account Number: {response.data.account_number}")
            print(f"Amount:         NGN {response.data.amount / 100:.2f}")
            print(f"Transaction ID: {response.data.transaction_id}")
            print(f"Expires in:     {response.data.validity_time} minutes")
        else:
            print(f"Error: {response.reason}")
```

### B. Verify Webhooks (Backend-to-Backend Security)
Protect your webhook routes by validating Velvpay request signatures with a single method call:

```python
from fastapi import FastAPI, Request, Header, HTTPException
import json

app = FastAPI()

@app.post("/webhooks/velvpay")
async def velvpay_webhook(
    request: Request,
    api_key: str = Header(...),       # Velvpay signature header
    reference_id: str = Header(...),  # Unique reference ID header
):
    # 1. Validate signature authenticity
    is_valid = client.verify_webhook(
        api_key_header=api_key,
        reference_id_header=reference_id
    )
    if not is_valid:
        raise HTTPException(status_code=401, detail="Invalid signature")

    # 2. Parse event body
    body_bytes = await request.body()
    event = json.loads(body_bytes.decode("utf-8"))

    # 3. Handle confirmed transactions
    if event.get("status") == "successful":
        transaction_id = event.get("txId")
        reference = event.get("reference")
        # Update order status in database...

    return {"status": "accepted"}
```

### C. Verify / Get Transaction Status
Directly fetch or resolve a transaction's status using its unique transaction ID:

```python
async def check_status(transaction_id: str):
    async with client:
        # Fetch current details
        details = await client.transactions.get(transaction_id)
        print(f"Details status: {details.data.status}")

        # Explicitly verify/resolve on Velvpay's servers
        resolution = await client.transactions.verify(transaction_id)
        print(f"Verified status: {resolution.data.status}")
```

---

## Features
- **Zero-Abstraction Crypto Layer**: Automatic generation of the required encrypted `api-key` header on every request.
- **Auto-injected Headers**: Correct headers (`public-key`, fresh `reference-id`, and `idempotencykey`) are automatically handled.
- **Pydantic Validation**: All request payloads and response bodies are typed and parsed with Pydantic v2.
- **Context Manager Support**: Uses `async with` for automatic connection pooling and clean disposal of `httpx` clients.

---

## License
MIT
# pyvelv
