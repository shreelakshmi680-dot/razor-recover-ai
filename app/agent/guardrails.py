"""
RazorRecover AI - Deterministic Guardrail Engine
Enforces stopping rules, discount safety margins, and escalation triggers.
"""

def evaluate_stopping_rules(payload: dict) -> dict:
    """
    Deterministic stopping rules to avoid spam or invalid retries:
    1. Hard declines (INSUFFICIENT_FUNDS, CARD_BLOCKED) -> STOP immediately.
    2. Retry count >= 2 -> STOP immediately.
    3. User opt-out -> STOP immediately.
    """
    error_code = payload.get("error_code", "")
    retry_count = payload.get("retry_count", 0)
    opt_out = payload.get("opted_out", False)

    if opt_out:
        return {
            "stop": True,
            "reason": "STOP: Customer has opted out of further recovery communications. Continuing would violate compliance policies."
        }

    if error_code in ["INSUFFICIENT_FUNDS", "CARD_BLOCKED", "ACCOUNT_CLOSED"]:
        return {
            "stop": True,
            "reason": f"STOP: Hard decline encountered ({error_code}). Automated retries prohibited."
        }

    if retry_count >= 2:
        return {
            "stop": True,
            "reason": f"STOP: Retry count ({retry_count}) has reached or exceeded the maximum allowed retries (2). Further automated intervention ceased to avoid spam."
        }

    return {"stop": False, "reason": "Passed all stopping rule checks."}


def evaluate_escalation_rules(payload: dict) -> dict:
    """
    Deterministic escalation rules to human ops queue:
    1. High-value transactions (amount >= ₹25,000)
    2. Enterprise accounts with active failures
    """
    amount = float(payload.get("amount_inr", 0.0))
    tier = payload.get("customer_tier", "standard").lower()
    retry_count = payload.get("retry_count", 0)

    if tier == "enterprise" and retry_count >= 1:
        return {
            "escalate": True,
            "reason": f"ESCALATED_TO_HUMAN: Enterprise-tier customer has already failed {retry_count} time(s). Enterprise accounts require dedicated relationship manager handling."
        }

    if amount >= 25000.0:
        return {
            "escalate": True,
            "reason": f"ESCALATED_TO_HUMAN: Transaction amount ₹{amount:,.2f} exceeds high-value threshold (₹25,000). Escalating to finance operations team for manual verification."
        }

    return {"escalate": False, "reason": "No escalation triggered."}


def validate_discount_margin(amount: float, requested_discount_pct: float) -> tuple[float, float, str]:
    """
    Financial Margin Guardrail:
    - Maximum allowed discount: 10%
    - Maximum absolute discount cap: ₹500
    """
    MAX_PCT = 10.0
    MAX_CAP_INR = 500.0

    if requested_discount_pct <= 0:
        return 0.0, 0.0, "APPROVED: Discount of 0.00% (₹0.00) applied without adjustment."

    approved_pct = min(requested_discount_pct, MAX_PCT)
    discount_amount = (approved_pct / 100.0) * amount

    if discount_amount > MAX_CAP_INR:
        discount_amount = MAX_CAP_INR
        approved_pct = (discount_amount / amount) * 100.0
        return approved_pct, discount_amount, f"Capped at max ₹{MAX_CAP_INR}"

    if approved_pct < requested_discount_pct:
        return approved_pct, discount_amount, f"Capped at max {MAX_PCT}%"

    return approved_pct, discount_amount, f"APPROVED: Discount of {approved_pct:.2f}% (₹{discount_amount:.2f}) applied."
# Alias to support engine.py legacy import
apply_discount_guardrail = validate_discount_margin