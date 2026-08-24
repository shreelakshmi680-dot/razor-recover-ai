"""
RazorRecover AI - Deterministic Guardrail Engine
Enforces stopping rules, discount safety margins, and escalation triggers.
"""

def evaluate_stopping_rules(payload: dict) -> dict:
    """Deterministic stopping rules to avoid spam or compliance violations."""
    if not isinstance(payload, dict):
        return {"stop": True, "reason": "STOP: Invalid or corrupted payload format."}

    error_code = str(payload.get("error_code", "")).strip().upper()
    
    try:
        retry_count = int(payload.get("retry_count", 0))
    except (ValueError, TypeError):
        retry_count = 0

    opt_out = bool(payload.get("opted_out", False))

    if opt_out:
        return {
            "stop": True,
            "reason": "STOP: Customer has opted out of communications. Further automated intervention ceased."
        }

    if error_code in ["INSUFFICIENT_FUNDS", "CARD_BLOCKED", "ACCOUNT_CLOSED", "FRAUD_SUSPECTED"]:
        return {
            "stop": True,
            "reason": f"STOP: Hard decline encountered ({error_code}). Automated retries prohibited."
        }

    if retry_count >= 2:
        return {
            "stop": True,
            "reason": f"STOP: Retry count ({retry_count}) has reached or exceeded the maximum allowed retries (2). Further automated intervention ceased to avoid spam."
        }

    return {"stop": False, "reason": "Passed all stopping checks."}


def evaluate_escalation_rules(payload: dict) -> dict:
    """Escalation rules to route high-risk transactions to human operations."""
    if not isinstance(payload, dict):
        return {"escalate": True, "reason": "ESCALATED_TO_HUMAN: Unparseable payload structure."}

    try:
        amount = float(payload.get("amount_inr", 0.0))
    except (ValueError, TypeError):
        amount = 0.0

    tier = str(payload.get("customer_tier", "standard")).strip().lower()
    
    try:
        retry_count = int(payload.get("retry_count", 0))
    except (ValueError, TypeError):
        retry_count = 0

    if tier == "enterprise" and retry_count >= 1:
        return {
            "escalate": True,
            "reason": f"ESCALATED_TO_HUMAN: Enterprise-tier customer has already failed {retry_count} time(s). Enterprise accounts require dedicated human handling."
        }

    if amount >= 25000.0:
        return {
            "escalate": True,
            "reason": f"ESCALATED_TO_HUMAN: Amount ₹{amount:,.2f} exceeds high-value desk threshold (₹25,000)."
        }

    return {"escalate": False, "reason": "No escalation triggered."}


def validate_discount_margin(amount: float, requested_discount_pct: float) -> tuple[float, float, str]:
    """
    Financial Margin Guardrail:
    - Maximum allowed discount rate: 10%
    - Maximum absolute discount cap: ₹500
    - Negative/invalid inputs safely zeroed
    """
    try:
        amount = float(amount)
        requested_discount_pct = float(requested_discount_pct)
    except (ValueError, TypeError):
        return 0.0, 0.0, "REJECTED: Malformed numeric values."

    if amount <= 0.0 or requested_discount_pct <= 0.0:
        return 0.0, 0.0, "APPROVED: 0.00% discount applied."

    MAX_PCT = 10.0
    MAX_CAP_INR = 500.0

    approved_pct = min(requested_discount_pct, MAX_PCT)
    discount_amount = (approved_pct / 100.0) * amount

    if discount_amount > MAX_CAP_INR:
        discount_amount = MAX_CAP_INR
        approved_pct = (discount_amount / amount) * 100.0
        return approved_pct, discount_amount, f"Capped at absolute max ₹{MAX_CAP_INR}"

    if approved_pct < requested_discount_pct:
        return approved_pct, discount_amount, f"Capped at max rate {MAX_PCT}%"

    return approved_pct, discount_amount, f"APPROVED: {approved_pct:.2f}% (₹{discount_amount:.2f}) discount applied."