from typing import Dict, Any
from datetime import datetime
from app.agent.guardrails import (
    evaluate_stopping_rules,
    evaluate_escalation_rules,
    apply_discount_guardrail
)
from app.services.razorpay_svc import create_recovery_payment_link

def diagnose_root_cause(record: Dict[str, Any]) -> Dict[str, Any]:
    ftype = record.get("failure_type", "GENERIC")

    if ftype == "HARD_DECLINE":
        return {"category": "UNRECOVERABLE_DECLINE", "action": "HALT", "discount": 0.0, "msg_type": "NONE"}
    elif ftype == "PAYMENT_DEGRADATION":
        return {"category": "TECHNICAL_LATENCY", "action": "SWITCH_TO_UPI_OR_RETRY", "discount": 0.0, "msg_type": "HINGLISH_STATUS"}
    elif ftype == "CHECKOUT_DROPOFF":
        return {"category": "PRICE_OR_FRICTION", "action": "DYNAMIC_DISCOUNT_NUDGE", "discount": 5.0, "msg_type": "HINGLISH_CART"}
    elif ftype == "SUBSCRIPTION_MANDATE_FAIL":
        return {"category": "MANDATE_DESYNC", "action": "DIRECT_RENEWAL_LINK", "discount": 0.0, "msg_type": "MANDATE_RECOVERY"}
    elif ftype == "B2B_RECEIVABLE_OVERDUE":
        return {"category": "OVERDUE_INVOICE", "action": "PROMISE_TO_PAY_LINK", "discount": 0.0, "msg_type": "B2B_REMINDER"}
    
    return {"category": "GENERIC", "action": "PAYMENT_LINK", "discount": 0.0, "msg_type": "STANDARD"}

def generate_contextual_message(msg_type: str, customer_name: str, amount: float, link: str) -> str:
    if msg_type == "HINGLISH_CART":
        return f"Hey {customer_name}! Aapka cart hold pe hai with an exclusive discount. Complete payment safely: {link}"
    elif msg_type == "HINGLISH_STATUS":
        return f"Hi {customer_name}, bank servers me temporary issue tha. Click to retry directly via UPI/Card: {link}"
    elif msg_type == "B2B_REMINDER":
        return f"Dear {customer_name}, your invoice of ₹{amount:,.2f} is pending clearance. Secure settlement portal: {link}"
    return f"Hello {customer_name}, please complete your pending payment of ₹{amount:,.2f} here: {link}"

def process_recovery_pipeline(record: Dict[str, Any]) -> Dict[str, Any]:
    audit_trail = []
    
    # 1. Stopping Rules Check
    should_stop, stop_reason = evaluate_stopping_rules(
        record.get("error_code", "UNKNOWN"), 
        record.get("retry_count", 0), 
        record.get("opt_out", False)
    )
    if should_stop:
        audit_trail.append({"step": "STOPPING_RULE", "status": "TERMINATED", "reason": stop_reason})
        return {
            "record_id": record["record_id"],
            "status": "STOPPED",
            "money_at_risk": record["amount_inr"],
            "money_recovered": 0.0,
            "reason": stop_reason,
            "payment_link": None,
            "message": None,
            "audit_trail": audit_trail
        }

    # 2. Compliant Escalation Check
    should_escalate, escalation_reason = evaluate_escalation_rules(
        record["amount_inr"], 
        record.get("retry_count", 0), 
        record.get("customer_tier", "standard")
    )
    if should_escalate:
        audit_trail.append({"step": "ESCALATION_GATE", "status": "ESCALATED", "reason": escalation_reason})
        return {
            "record_id": record["record_id"],
            "status": "ESCALATED_TO_HUMAN",
            "money_at_risk": record["amount_inr"],
            "money_recovered": 0.0,
            "reason": escalation_reason,
            "payment_link": None,
            "message": None,
            "audit_trail": audit_trail
        }

    # 3. Diagnosis Step
    diagnosis = diagnose_root_cause(record)
    audit_trail.append({"step": "DIAGNOSIS", "status": "SUCCESS", "details": diagnosis})

    # 4. Bounded Discount Guardrail
    discount_pct, final_amount, notes = apply_discount_guardrail(
        record["amount_inr"], 
        diagnosis["discount"]
    )
    audit_trail.append({"step": "GUARDRAIL_CHECK", "status": "PASSED", "notes": notes, "final_amount": final_amount})

    # 5. Dynamic Link Generation
    link = create_recovery_payment_link(
        order_id=record["order_id"],
        amount_inr=final_amount,
        customer_email=record.get("customer_email", "guest@example.com"),
        customer_phone=record.get("customer_phone"),
        description=f"Recovery for {record['order_id']}"
    )
    audit_trail.append({"step": "PAYMENT_LINK_GENERATION", "status": "SUCCESS", "url": link})

    # 6. Contextual Communication Synthesis
    msg = generate_contextual_message(diagnosis["msg_type"], record.get("customer_name", "Customer"), final_amount, link)

    return {
        "record_id": record["record_id"],
        "status": "RECOVERED",
        "money_at_risk": record["amount_inr"],
        "money_recovered": final_amount,
        "reason": f"Autonomous action executed: {diagnosis['action']}",
        "payment_link": link,
        "message": msg,
        "audit_trail": audit_trail
    }