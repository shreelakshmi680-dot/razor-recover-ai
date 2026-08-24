import hmac
import hashlib
import json

def verify_razorpay_signature(payload_body: str, received_signature: str, secret: str = "rzp_secret_recover_2026") -> bool:
    """Verifies standard Razorpay HMAC-SHA256 webhook signatures."""
    if not received_signature:
        return False
    computed = hmac.new(secret.encode('utf-8'), payload_body.encode('utf-8'), hashlib.sha256).hexdigest()
    return hmac.compare_digest(computed, received_signature)

def parse_webhook_payload(payload_json: dict) -> dict:
    """Extracts recovery-critical parameters from standard Razorpay payment.failed webhooks."""
    payment = payload_json.get("payload", {}).get("payment", {}).get("entity", {})
    notes = payment.get("notes", {})
    
    return {
        "record_id": f"WH_{payment.get('id', 'pay_live_001')}",
        "order_id": payment.get("order_id", "order_live_wh"),
        "customer_name": notes.get("customer_name", "Valued Customer"),
        "customer_email": payment.get("email", "customer@example.com"),
        "failure_type": "PAYMENT_DEGRADATION" if "timeout" in payment.get("error_code", "").lower() else "CHECKOUT_DROPOFF",
        "error_code": payment.get("error_code", "GATEWAY_TIMEOUT"),
        "amount_inr": float(payment.get("amount", 250000)) / 100.0 if payment.get("amount") else 2500.0,
        "retry_count": notes.get("retry_count", 0),
        "customer_tier": notes.get("tier", "standard")
    }