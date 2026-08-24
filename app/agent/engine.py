"""
RazorRecover AI - Autonomous Decision Engine
Orchestrates diagnosis, guardrails, link creation, and message generation.
"""

from app.agent.guardrails import (
    evaluate_stopping_rules,
    evaluate_escalation_rules,
    validate_discount_margin
)
from app.services.checkout_page import generate_interactive_checkout_url

def process_recovery_pipeline(payload: dict) -> dict:
    record_id = payload.get("record_id", "REC_UNKNOWN")
    order_id = payload.get("order_id", "order_live_000")
    customer_name = payload.get("customer_name", "Valued Customer")
    amount = float(payload.get("amount_inr", 0.0))
    failure_type = payload.get("failure_type", "CHECKOUT_DROPOFF")
    error_code = payload.get("error_code", "GENERIC_ERROR")

    audit_trail = []

    # 1. Stopping Rules Evaluation
    stop_check = evaluate_stopping_rules(payload)
    audit_trail.append({
        "step": "STOPPING_RULE",
        "status": "TERMINATED" if stop_check["stop"] else "PASSED",
        "reason": stop_check["reason"]
    })

    if stop_check["stop"]:
        return {
            "record_id": record_id,
            "order_id": order_id,
            "customer_name": customer_name,
            "failure_type": failure_type,
            "money_at_risk": amount,
            "money_recovered": 0.0,
            "status": "STOPPED",
            "reason": stop_check["reason"],
            "message": "",
            "payment_link": "",
            "audit_trail": audit_trail
        }

    # 2. Escalation Gate Evaluation
    esc_check = evaluate_escalation_rules(payload)
    audit_trail.append({
        "step": "ESCALATION_GATE",
        "status": "ESCALATED" if esc_check["escalate"] else "PASSED",
        "reason": esc_check["reason"]
    })

    if esc_check["escalate"]:
        return {
            "record_id": record_id,
            "order_id": order_id,
            "customer_name": customer_name,
            "failure_type": failure_type,
            "money_at_risk": amount,
            "money_recovered": 0.0,
            "status": "ESCALATED_TO_HUMAN",
            "reason": esc_check["reason"],
            "message": "",
            "payment_link": "",
            "audit_trail": audit_trail
        }

    # 3. Diagnosis & Guardrail Margin Check
    requested_discount = 5.0 if failure_type == "CHECKOUT_DROPOFF" else 0.0
    approved_pct, discount_amount, note = validate_discount_margin(amount, requested_discount)
    final_amount = max(0.0, amount - discount_amount)

    audit_trail.append({
        "step": "GUARDRAIL_CHECK",
        "status": "PASSED",
        "notes": note,
        "discount_applied_pct": approved_pct,
        "discount_inr": discount_amount,
        "final_amount": final_amount
    })

    # 4. Interactive Razorpay Link Generation
    payment_link = generate_interactive_checkout_url(order_id, final_amount, customer_name)
    audit_trail.append({
        "step": "PAYMENT_LINK_GENERATION",
        "status": "SUCCESS",
        "url": payment_link
    })

    # 5. Clean Outreach Messaging (Clean Text for Email/SMS)
    if failure_type == "CHECKOUT_DROPOFF":
        msg = f"Namaste {customer_name}, your order #{order_id} was left in your cart. We've unlocked an exclusive {approved_pct:.0f}% recovery discount for you! Please complete your checkout below."
    elif failure_type == "PAYMENT_DEGRADATION":
        msg = f"Namaste {customer_name}, your recent payment experienced a network timeout. No double-debits occurred. You can safely complete your transaction below."
    elif failure_type == "SUBSCRIPTION_MANDATE_FAIL":
        msg = f"Namaste {customer_name}, your recurring mandate sync encountered a temporary bank delay. Please update your payment method below to prevent interruption."
    else:
        msg = f"Namaste {customer_name}, please complete your pending payment of ₹{final_amount:,.2f} safely using the link below."

    return {
        "record_id": record_id,
        "order_id": order_id,
        "customer_name": customer_name,
        "failure_type": failure_type,
        "money_at_risk": amount,
        "money_recovered": final_amount,
        "status": "RECOVERED",
        "reason": f"Autonomous recovery executed with {approved_pct:.1f}% discount margin.",
        "message": msg,
        "payment_link": payment_link,
        "audit_trail": audit_trail
    }