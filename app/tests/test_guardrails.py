import pytest
import os
import sys

# Ensure root directory is on the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.agent.guardrails import validate_discount_margin, evaluate_stopping_rules
from app.agent.engine import process_recovery_pipeline

def test_hard_decline_stopping_rule():
    payload = {
        "record_id": "TEST_01",
        "error_code": "INSUFFICIENT_FUNDS",
        "retry_count": 0,
        "amount_inr": 2000.0
    }
    stop_rule = evaluate_stopping_rules(payload)
    assert stop_rule["stop"] is True
    assert "INSUFFICIENT_FUNDS" in stop_rule["reason"]

def test_max_retries_exceeded_stopping_rule():
    payload = {
        "record_id": "TEST_02",
        "error_code": "GATEWAY_TIMEOUT",
        "retry_count": 3,
        "amount_inr": 1500.0
    }
    stop_rule = evaluate_stopping_rules(payload)
    assert stop_rule["stop"] is True
    assert "maximum allowed retries" in stop_rule["reason"].lower()

def test_discount_margin_guardrail_cap():
    amount = 10000.0
    requested_discount_pct = 25.0
    approved_pct, discount_amount, note = validate_discount_margin(amount, requested_discount_pct)
    
    assert approved_pct <= 10.0
    assert discount_amount <= 500.0
    assert "Capped" in note

def test_high_value_enterprise_escalation():
    payload = {
        "record_id": "TEST_04",
        "order_id": "ORD_HIGH_01",
        "customer_name": "Acme Corp",
        "customer_email": "ops@acme.com",
        "failure_type": "B2B_RECEIVABLE_OVERDUE",
        "error_code": "INVOICE_OVERDUE_15D",
        "amount_inr": 45000.0,
        "retry_count": 0,
        "customer_tier": "enterprise"
    }
    result = process_recovery_pipeline(payload)
    assert result["status"] == "ESCALATED_TO_HUMAN"