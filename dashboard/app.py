import os
import sys

# Ensure the root project directory is in the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import streamlit as st
import json
import pandas as pd
from app.agent.engine import process_recovery_pipeline

st.set_page_config(
    page_title="RazorRecover AI | Track 03",
    layout="wide",
    page_icon="⚡"
)

st.title("⚡ RazorRecover AI — Autonomous Revenue Recovery Engine")
st.caption("Razorpay AI Buildathon Submission | Track 03: AI Revenue Recovery")

# Load synthetic batch dataset
try:
    with open("data/synthetic_batch.json", "r") as f:
        batch_data = json.load(f)
except Exception:
    # Try alternative relative path if running from dashboard folder
    try:
        with open("../data/synthetic_batch.json", "r") as f:
            batch_data = json.load(f)
    except Exception:
        st.error("Missing `data/synthetic_batch.json`. Please make sure the dataset exists.")
        st.stop()

tabs = st.tabs(["📊 Batch Benchmark (50 Scenarios)", "🧪 Single Transaction Sandbox", "📜 Full Audit Trail"])

# -------------------------------------------------------------
# TAB 1: BATCH BENCHMARK
# -------------------------------------------------------------
with tabs[0]:
    st.subheader("Measured Money Recovered Across 50-Record Batch")
    st.write(
        "Autonomous pipeline evaluating payment degradations, cart drop-offs, "
        "failed subscription mandates, and overdue B2B receivables."
    )

    if st.button("🚀 Run 50-Record Batch Benchmark", type="primary"):
        results = [process_recovery_pipeline(item) for item in batch_data]
        st.session_state["batch_results"] = results

    if "batch_results" in st.session_state:
        results = st.session_state["batch_results"]
        
        # Calculate summary metrics
        total_risk = sum(r["money_at_risk"] for r in results)
        total_recovered = sum(r["money_recovered"] for r in results if r["status"] == "RECOVERED")
        stopped_count = sum(1 for r in results if r["status"] == "STOPPED")
        escalated_count = sum(1 for r in results if r["status"] == "ESCALATED_TO_HUMAN")
        recovered_count = sum(1 for r in results if r["status"] == "RECOVERED")
        recovery_rate = (recovered_count / len(results)) * 100 if len(results) > 0 else 0

        # KPI Metric Cards
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Revenue at Risk", f"₹{total_risk:,.2f}")
        col2.metric("Total Recovered", f"₹{total_recovered:,.2f}", delta=f"{recovery_rate:.1f}% Win Rate")
        col3.metric("Stopping Rules Triggered", stopped_count, delta="Zero Hallucination Risk", delta_color="inverse")
        col4.metric("Compliant Escalations (Human Review)", escalated_count)

        st.divider()

        # Batch Results Table
        df_summary = pd.DataFrame([
            {
                "Record ID": r["record_id"],
                "Status": r["status"],
                "Original ₹": f"₹{r['money_at_risk']:,.2f}",
                "Recovered ₹": f"₹{r['money_recovered']:,.2f}",
                "Decision / Reason": r["reason"],
                "Generated Razorpay Link": r["payment_link"] or "N/A"
            }
            for r in results
        ])
        st.dataframe(df_summary, use_container_width=True)

# -------------------------------------------------------------
# TAB 2: LIVE SIMULATION SANDBOX
# -------------------------------------------------------------
with tabs[1]:
    st.subheader("Live Transaction Recovery Simulator")
    st.write("Test single-event interventions in real time.")
    
    col_a, col_b = st.columns(2)
    with col_a:
        order_id = st.text_input("Order ID", "order_live_5501")
        cust_name = st.text_input("Customer Name", "Ananya Sharma")
        cust_email = st.text_input("Customer Email", "ananya@example.com")
        amount = st.number_input("Amount (INR)", min_value=100.0, max_value=100000.0, value=3200.0, step=100.0)
    
    with col_b:
        failure_type = st.selectbox("Failure Type", [
            "CHECKOUT_DROPOFF", 
            "PAYMENT_DEGRADATION", 
            "SUBSCRIPTION_MANDATE_FAIL", 
            "B2B_RECEIVABLE_OVERDUE",
            "HARD_DECLINE"
        ])
        error_code = st.selectbox("Error Code", [
            "AUTH_STEP_ABANDONED", 
            "GATEWAY_TIMEOUT", 
            "UPI_NPCI_UNAVAILABLE", 
            "MANDATE_EXECUTION_FAILED",
            "INVOICE_OVERDUE_15D",
            "INSUFFICIENT_FUNDS",
            "CARD_BLOCKED"
        ])
        retries = st.slider("Previous Retry Count", 0, 4, 0)
        customer_tier = st.selectbox("Customer Tier", ["standard", "enterprise"])

    if st.button("⚡ Trigger Autonomous Recovery", type="primary"):
        payload = {
            "record_id": "REC_LIVE_SIM",
            "order_id": order_id,
            "customer_name": cust_name,
            "customer_email": cust_email,
            "failure_type": failure_type,
            "error_code": error_code,
            "amount_inr": amount,
            "retry_count": retries,
            "customer_tier": customer_tier
        }
        res = process_recovery_pipeline(payload)
        
        st.markdown(f"### Outcome Status: `{res['status']}`")
        st.write(f"**Action Note:** {res['reason']}")
        
        if res["payment_link"]:
            st.success(f"**Generated Dynamic Link:** [{res['payment_link']}]({res['payment_link']})")
            st.text_area("Generated Contextual Message (Hinglish/English):", res["message"], height=80)
        
        st.write("#### Agent Execution Trace:")
        st.json(res["audit_trail"])

# -------------------------------------------------------------
# TAB 3: IMMUTABLE AUDIT TRAIL
# -------------------------------------------------------------
with tabs[2]:
    st.subheader("Explainable Audit Trail & Compliance Matrix")
    if "batch_results" in st.session_state:
        all_logs = []
        for r in st.session_state["batch_results"]:
            for step in r["audit_trail"]:
                all_logs.append({
                    "Record ID": r["record_id"],
                    "Status": r["status"],
                    "Pipeline Step": step.get("step"),
                    "Step Status": step.get("status"),
                    "Details": str({k: v for k, v in step.items() if k not in ["step", "status"]})
                })
        st.dataframe(pd.DataFrame(all_logs), use_container_width=True)
    else:
        st.info("Run the batch benchmark in Tab 1 to populate the audit logs.")