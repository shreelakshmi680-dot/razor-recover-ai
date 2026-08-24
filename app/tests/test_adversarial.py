import pytest
import concurrent.futures
from app.agent.guardrails import evaluate_stopping_rules, evaluate_escalation_rules, validate_discount_margin
from app.agent.engine import process_recovery_pipeline
from app.services.db_svc import save_recovery_record, init_db

def test_negative_amount_margin_handling():
    pct, amount, note = validate_discount_margin(-1500.0, 10.0)
    assert pct == 0.0
    assert amount == 0.0

def test_extreme_discount_percentage_attack():
    pct, amount, note = validate_discount_margin(10000.0, 99.0)
    assert pct <= 10.0
    assert amount == 500.0
    assert "Capped at absolute max" in note

def test_empty_corrupted_payload():
    res = evaluate_stopping_rules({})
    assert res["stop"] is False
    res_none = evaluate_stopping_rules(None)
    assert res_none["stop"] is True

def test_sql_injection_in_customer_name():
    payload = {
        "record_id": "INJ_01",
        "order_id": "ord_999",
        "customer_name": "'; DROP TABLE recovery_audits; --",
        "amount_inr": "1200.00",
        "retry_count": "0",
        "error_code": "GATEWAY_TIMEOUT"
    }
    result = process_recovery_pipeline(payload)
    assert result["status"] == "RECOVERED"
    assert "DROP TABLE" in result["customer_name"]

def test_opt_out_compliance_rule():
    payload = {
        "record_id": "OPT_01",
        "opted_out": True,
        "error_code": "NETWORK_TIMEOUT",
        "retry_count": 0
    }
    res = evaluate_stopping_rules(payload)
    assert res["stop"] is True
    assert "opted out" in res["reason"]

def test_enterprise_escalation_threshold():
    payload = {
        "amount_inr": 5000.0,
        "customer_tier": "enterprise",
        "retry_count": 1
    }
    res = evaluate_escalation_rules(payload)
    assert res["escalate"] is True
    assert "Enterprise-tier" in res["reason"]

def test_concurrent_batch_throughput():
    init_db()
    payloads = [
        {
            "record_id": f"CONC_REC_{i}",
            "order_id": f"order_conc_{i}",
            "customer_name": f"Enterprise User {i}",
            "amount_inr": 1500.0 + (i * 100),
            "failure_type": "CHECKOUT_DROPOFF",
            "retry_count": 0
        }
        for i in range(10)
    ]
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        results = list(executor.map(process_recovery_pipeline, payloads))

    assert len(results) == 10
    for res in results:
        assert res["status"] == "RECOVERED"
        assert save_recovery_record(res) is True