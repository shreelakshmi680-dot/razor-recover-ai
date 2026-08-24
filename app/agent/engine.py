"""
RazorRecover AI - Autonomous Decision Engine
Orchestrates diagnosis, guardrails, link creation, and message generation.
"""

from app.agent.guardrails import (
    evaluate_stopping_rules,
    evaluate_escalation_rules,
    validate_discount_margin
)
from app.services.razorpay_svc import create_recovery_payment_link

def process_recovery_pipeline(payload: dict) -> dict:
    if not isinstance(payload, dict):
        payload = {}

    record_id = str(payload.get("record_id", "REC_ERR"))
    order_id = str(payload.get("order_id", "order_000"))
    customer_name = str(payload.get("customer_name", "Valued Customer"))
    customer_email = str(payload.get("customer_email", ""))
    
    try:
        amount = max(0.0, float(payload.get("amount_inr", 0.0)))
    except (ValueError, TypeError):
        amount = 0.0

    failure_type = str(payload.get("failure_type", "CHECKOUT_DROPOFF"))
    audit_trail = []

    # 1. Evaluate Stopping Rules
    stop_res = evaluate_stopping_rules(payload)
    audit_trail.append({
        "step": "STOPPING_RULES",
        "status": "TERMINATED" if stop_res["stop"] else "PASSED",
        "reason": stop_res["reason"]
    })
    if stop_res["stop"]:
        return {
            "record_id": record_id,
            "order_id": order_id,
            "customer_name": customer_name,
            "failure_type": failure_type,
            "money_at_risk": amount,
            "money_recovered": 0.0,
            "status": "STOPPED",
            "reason": stop_res["reason"],
            "message": "",
            "payment_link": "",
            "audit_trail": audit_trail
        }

    # 2. Evaluate Escalation Gates
    esc_res = evaluate_escalation_rules(payload)
    audit_trail.append({
        "step": "ESCALATION_GATE",
        "status": "ESCALATED" if esc_res["escalate"] else "PASSED",
        "reason": esc_res["reason"]
    })
    if esc_res["escalate"]:
        return {
            "record_id": record_id,
            "order_id": order_id,
            "customer_name": customer_name,
            "failure_type": failure_type,
            "money_at_risk": amount,
            "money_recovered": 0.0,
            "status": "ESCALATED_TO_HUMAN",
            "reason": esc_res["reason"],
            "message": "",
            "payment_link": "",
            "audit_trail": audit_trail
        }

    # 3. Apply Margin Guardrails
    requested_discount = 5.0 if failure_type == "CHECKOUT_DROPOFF" else 0.0
    approved_pct, discount_amount, note = validate_discount_margin(amount, requested_discount)
    final_amount = max(0.0, amount - discount_amount)

    audit_trail.append({
        "step": "MARGIN_GUARDRAIL",
        "status": "PASSED",
        "notes": note,
        "discount_applied_pct": approved_pct,
        "discount_inr": discount_amount,
        "final_amount": final_amount
    })

    # 4. Generate Razorpay Payment Link
    link_info = create_recovery_payment_link(order_id, final_amount, customer_name, customer_email)
    payment_link = link_info["payment_url"]
    audit_trail.append({
        "step": "LINK_DISPATCH",
        "status": link_info["status"],
        "source": link_info["source"],
        "url": payment_link
    })

    # 5. Formulate Recovery Notification Message
    if failure_type == "CHECKOUT_DROPOFF":
        msg = f"Namaste {customer_name}, your cart for order #{order_id} was saved. We've unlocked an exclusive {approved_pct:.0f}% recovery discount. Complete your checkout securely below."
    elif failure_type == "PAYMENT_DEGRADATION":
        msg = f"Namaste {customer_name}, we detected a bank network timeout on order #{order_id}. No duplicate charge occurred. Resume your transaction below."
    elif failure_type == "SUBSCRIPTION_MANDATE_FAIL":
        msg = f"Namaste {customer_name}, your recurring mandate sync encountered a bank delay. Re-sync your payment method below."
    else:
        msg = f"Namaste {customer_name}, please complete your pending settlement of ₹{final_amount:,.2f} below."

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