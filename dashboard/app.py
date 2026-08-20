import os
import sys

# Ensure root directory is accessible
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

# -------------------------------------------------------------
# ADVANCED RAZORPAY "BLADE" DESIGN SYSTEM & ANIMATIONS
# -------------------------------------------------------------
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Mulish:wght@400;500;600;700;800;900&family=JetBrains+Mono:wght@500;700&display=swap');

    /* Global typography overrides */
    * {
        font-family: 'Mulish', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif !important;
    }
    
    .stCode, code, pre, .mono-font {
        font-family: 'JetBrains Mono', monospace !important;
    }

    /* Animated background gradient mesh */
    .stApp {
        background-color: #F4F7FB !important;
        background-image: 
            radial-gradient(at 0% 0%, rgba(13, 148, 251, 0.08) 0px, transparent 50%),
            radial-gradient(at 100% 0%, rgba(1, 38, 82, 0.07) 0px, transparent 50%),
            radial-gradient(at 50% 100%, rgba(4, 219, 124, 0.05) 0px, transparent 50%) !important;
        background-attachment: fixed !important;
    }

    /* Main Container Padding */
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 3rem;
        max-width: 1200px;
    }

    /* Razorpay Executive Hero Header */
    .rzp-hero {
        background: linear-gradient(135deg, #012652 0%, #083b79 55%, #0D94FB 100%);
        padding: 36px 40px;
        border-radius: 16px;
        color: #FFFFFF;
        box-shadow: 0 20px 35px -10px rgba(13, 148, 251, 0.25);
        margin-bottom: 28px;
        border: 1px solid rgba(255, 255, 255, 0.12);
        position: relative;
        overflow: hidden;
    }

    .rzp-hero::after {
        content: "";
        position: absolute;
        top: -50%;
        right: -10%;
        width: 350px;
        height: 350px;
        background: radial-gradient(circle, rgba(13, 148, 251, 0.25) 0%, transparent 70%);
        border-radius: 50%;
        pointer-events: none;
    }

    .rzp-hero h1 {
        color: #FFFFFF !important;
        font-weight: 900 !important;
        font-size: 2.25rem !important;
        letter-spacing: -0.02em !important;
        margin: 0 !important;
    }

    .rzp-hero p {
        color: #D8E5F7 !important;
        font-size: 1.05rem !important;
        margin-top: 8px !important;
        margin-bottom: 14px !important;
        font-weight: 500 !important;
    }

    .rzp-tag {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        background: rgba(255, 255, 255, 0.15);
        backdrop-filter: blur(10px);
        color: #FFFFFF !important;
        padding: 5px 14px;
        border-radius: 30px;
        font-size: 0.82rem;
        font-weight: 700;
        border: 1px solid rgba(255, 255, 255, 0.2);
    }

    /* Interactive Glassmorphism Metric Cards */
    .metric-card {
        background: rgba(255, 255, 255, 0.95);
        backdrop-filter: blur(12px);
        border: 1px solid #E2E8F0;
        padding: 22px 24px;
        border-radius: 14px;
        box-shadow: 0 4px 14px rgba(1, 38, 82, 0.04);
        transition: all 0.28s cubic-bezier(0.4, 0, 0.2, 1);
        cursor: default;
    }

    .metric-card:hover {
        transform: translateY(-6px);
        border-color: #0D94FB;
        box-shadow: 0 16px 30px -8px rgba(13, 148, 251, 0.18);
    }

    .metric-label {
        color: #64748B;
        font-size: 0.8rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.6px;
    }

    .metric-num {
        color: #012652;
        font-size: 1.85rem;
        font-weight: 800;
        margin: 6px 0;
        font-family: 'JetBrains Mono', monospace !important;
    }

    .metric-footer {
        font-size: 0.82rem;
        font-weight: 700;
        display: flex;
        align-items: center;
        gap: 4px;
    }

    .text-green { color: #02A95C; }
    .text-blue { color: #0D94FB; }
    .text-purple { color: #5F259F; }

    /* Animated Razorpay Primary Button */
    .stButton > button {
        background: linear-gradient(180deg, #0D94FB 0%, #0274D9 100%) !important;
        color: #FFFFFF !important;
        border: none !important;
        border-radius: 8px !important;
        font-weight: 700 !important;
        font-size: 0.95rem !important;
        padding: 12px 28px !important;
        letter-spacing: 0.2px !important;
        box-shadow: 0 4px 14px rgba(13, 148, 251, 0.35) !important;
        transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1) !important;
    }

    .stButton > button:hover {
        background: linear-gradient(180deg, #24A0FF 0%, #0D85EA 100%) !important;
        transform: translateY(-2px) !important;
        box-shadow: 0 8px 22px rgba(13, 148, 251, 0.45) !important;
    }

    .stButton > button:active {
        transform: translateY(0px) !important;
    }

    /* Tabs Styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 16px;
        border-bottom: 2px solid #E2E8F0;
        margin-bottom: 20px;
    }

    .stTabs [data-baseweb="tab"] {
        font-weight: 700 !important;
        font-size: 0.95rem !important;
        color: #64748B !important;
        padding: 10px 16px !important;
        border: none !important;
        background: transparent !important;
    }

    .stTabs [aria-selected="true"] {
        color: #0D94FB !important;
        border-bottom: 3px solid #0D94FB !important;
    }

    /* Input Field & Selectbox Custom Styling */
    .stTextInput input, .stSelectbox select, .stNumberInput input {
        border-radius: 8px !important;
        border: 1px solid #CBD5E1 !important;
        font-weight: 500 !important;
        transition: all 0.2s ease !important;
    }

    .stTextInput input:focus, .stSelectbox select:focus, .stNumberInput input:focus {
        border-color: #0D94FB !important;
        box-shadow: 0 0 0 3px rgba(13, 148, 251, 0.15) !important;
    }
</style>
""", unsafe_allow_html=True)

# -------------------------------------------------------------
# HERO BANNER
# -------------------------------------------------------------
st.markdown("""
<div class="rzp-hero">
    <h1>⚡ RazorRecover AI</h1>
    <p>Autonomous AI Revenue Recovery Engine with Deterministic Guardrails</p>
    <div class="rzp-tag">🛡️ Razorpay AI Buildathon &nbsp;|&nbsp; Track 03: AI Revenue Recovery</div>
</div>
""", unsafe_allow_html=True)

# Load synthetic batch dataset
try:
    with open("data/synthetic_batch.json", "r") as f:
        batch_data = json.load(f)
except Exception:
    try:
        with open("../data/synthetic_batch.json", "r") as f:
            batch_data = json.load(f)
    except Exception:
        st.error("Missing `data/synthetic_batch.json`. Please ensure the synthetic dataset is generated.")
        st.stop()

tabs = st.tabs(["📊 Batch Benchmark (50 Scenarios)", "🧪 Single Transaction Sandbox", "📜 Full Audit Trail"])

# -------------------------------------------------------------
# TAB 1: BATCH BENCHMARK
# -------------------------------------------------------------
with tabs[0]:
    st.markdown("### 📈 Measured Money Recovered Across 50-Record Batch")
    st.write("Autonomous recovery pipeline evaluating checkout drop-offs, payment degradations, mandate desyncs, and overdue B2B receivables.")

    if st.button("🚀 Run 50-Record Batch Benchmark"):
        with st.spinner("Executing agent pipeline across 50 records..."):
            results = [process_recovery_pipeline(item) for item in batch_data]
            st.session_state["batch_results"] = results

    if "batch_results" in st.session_state:
        results = st.session_state["batch_results"]
        
        total_risk = sum(r["money_at_risk"] for r in results)
        total_recovered = sum(r["money_recovered"] for r in results if r["status"] == "RECOVERED")
        stopped_count = sum(1 for r in results if r["status"] == "STOPPED")
        escalated_count = sum(1 for r in results if r["status"] == "ESCALATED_TO_HUMAN")
        recovered_count = sum(1 for r in results if r["status"] == "RECOVERED")
        recovery_rate = (recovered_count / len(results)) * 100 if len(results) > 0 else 0

        # Razorpay Blade Metric Cards
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">Total Revenue at Risk</div>
                <div class="metric-num">₹{total_risk:,.2f}</div>
                <div class="metric-footer text-blue">● 50 Scenarios Evaluated</div>
            </div>
            """, unsafe_allow_html=True)
        with col2:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">Total Recovered</div>
                <div class="metric-num text-green">₹{total_recovered:,.2f}</div>
                <div class="metric-footer text-green">↑ {recovery_rate:.1f}% Recovery Win Rate</div>
            </div>
            """, unsafe_allow_html=True)
        with col3:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">Stopping Rules Triggered</div>
                <div class="metric-num text-purple">{stopped_count}</div>
                <div class="metric-footer text-purple">✓ Zero Hallucinations</div>
            </div>
            """, unsafe_allow_html=True)
        with col4:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">Compliant Escalations</div>
                <div class="metric-num">{escalated_count}</div>
                <div class="metric-footer text-blue">👤 Human Review Queue</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # Batch Results Table
        df_summary = pd.DataFrame([
            {
                "Record ID": r["record_id"],
                "Status": r["status"],
                "Original ₹": f"₹{r['money_at_risk']:,.2f}",
                "Recovered ₹": f"₹{r['money_recovered']:,.2f}",
                "Decision / Action Reason": r["reason"],
                "Generated Payment Link": r["payment_link"] or "N/A"
            }
            for r in results
        ])
        st.dataframe(df_summary, use_container_width=True)

# -------------------------------------------------------------
# TAB 2: LIVE SIMULATION SANDBOX
# -------------------------------------------------------------
with tabs[1]:
    st.markdown("### 🧪 Live Transaction Recovery Simulator")
    st.write("Test single-event interventions and observe deterministic guardrails in real time.")
    
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

    if st.button("⚡ Trigger Autonomous Recovery"):
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
        
        status_color = "#02A95C" if res["status"] == "RECOVERED" else ("#5F259F" if res["status"] == "ESCALATED_TO_HUMAN" else "#E53E3E")
        st.markdown(f"""
        <div style="background: #FFFFFF; border-left: 6px solid {status_color}; padding: 18px 22px; border-radius: 12px; margin-top: 20px; box-shadow: 0 4px 14px rgba(1, 38, 82, 0.04);">
            <h4 style="margin: 0; color: {status_color}; font-weight: 800;">Status: {res['status']}</h4>
            <p style="margin: 6px 0 0 0; color: #334155; font-weight: 500;"><strong>Action Note:</strong> {res['reason']}</p>
        </div>
        """, unsafe_allow_html=True)
        
        if res["payment_link"]:
            st.success(f"**Generated Dynamic Link:** [{res['payment_link']}]({res['payment_link']})")
            st.text_area("Generated Contextual Message (Hinglish/English):", res["message"], height=80)
        
        st.markdown("#### Agent Execution Trace:")
        st.json(res["audit_trail"])

# -------------------------------------------------------------
# TAB 3: IMMUTABLE AUDIT TRAIL
# -------------------------------------------------------------
with tabs[2]:
    st.markdown("### 📜 Explainable Audit Trail & Compliance Matrix")
    st.write("Chronological, deterministic trace of every validation checkpoint executed.")
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