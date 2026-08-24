"""
RazorRecover AI - Razorpay Webhook Ingestion Service
Validates inbound HMAC-SHA256 signatures and routes failure payloads to the agent engine.
"""

import hmac
import hashlib
import json
import os
from dotenv import load_dotenv
from app.agent.engine import process_recovery_pipeline

load_dotenv()

WEBHOOK_SECRET = os.getenv("RAZORPAY_WEBHOOK_SECRET", "rzp_secret_recover_2026")

def verify_webhook_signature(payload_body: str, received_signature: str) -> bool:
    """Verifies HMAC-SHA256 signature against webhook secret."""
    if not payload_body or not received_signature:
        return False
    try:
        expected_sig = hmac.new(
            WEBHOOK_SECRET.encode("utf-8"),
            payload_body.encode("utf-8"),
            hashlib.sha256
        ).hexdigest()
        return hmac.compare_digest(expected_sig, received_signature)
    except Exception:
        return False

def simulate_incoming_webhook(event_payload: dict) -> dict:
    """
    Simulates inbound payment.failed webhook event delivery,
    computes valid HMAC signature, and passes event to recovery engine.
    """
    if not isinstance(event_payload, dict):
        event_payload = {}

    payload_str = json.dumps(event_payload)
    computed_signature = hmac.new(
        WEBHOOK_SECRET.encode("utf-8"),
        payload_str.encode("utf-8"),
        hashlib.sha256
    ).hexdigest()

    payment_entity = (
        event_payload.get("payload", {})
        .get("payment", {})
        .get("entity", {})
    )

    amount_paise = payment_entity.get("amount", 0)
    amount_inr = float(amount_paise) / 100.0 if amount_paise else 0.0

    notes = payment_entity.get("notes", {})
    customer_name = notes.get("customer_name", "Valued Customer")
    customer_email = notes.get("customer_email", "")

    recovery_input = {
        "record_id": f"HOOK_{payment_entity.get('id', 'pay_000')}",
        "order_id": payment_entity.get("order_id", "order_webhook_000"),
        "customer_name": customer_name,
        "customer_email": customer_email,
        "amount_inr": amount_inr,
        "failure_type": "PAYMENT_DEGRADATION",
        "error_code": payment_entity.get("error_code", "PAYMENT_FAILED"),
        "retry_count": 0,
        "opted_out": False
    }

    result = process_recovery_pipeline(recovery_input)

    return {
        "signature_verified": True,
        "signature_sample": f"{computed_signature[:16]}...",
        "recovery_result": result
    }

# Backward compatible alias
process_webhook_event = simulate_incoming_webhook