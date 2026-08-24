"""
RazorRecover AI - Production Control Dashboard & Analytics Cockpit
Enterprise revenue recovery cockpit with deterministic guardrails and interactive Plotly visuals.
"""

import sys
import os

# Ensure root directory is in module search path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import streamlit as st
import pandas as pd
import json
import concurrent.futures
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go

from app.agent.engine import process_recovery_pipeline
from app.services.db_svc import init_db, save_recovery_record, get_all_records
from app.services.webhook_svc import simulate_incoming_webhook
from app.services.email_svc import send_recovery_email

st.set_page_config(
    page_title="RazorRecover AI - Enterprise Cockpit",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom Razorpay Enterprise Theme, Fonts & Card Micro-Interactions
st.markdown("""
<style>
    /* Hide Streamlit default chrome */
    #MainMenu, footer, header, .stDeployButton, div[data-testid="stDecoration"] {
        display: none !important;
    }

    /* Modern Fintech Mesh Background */
    .stApp {
        background-color: #f8fafc;
        background-image: radial-gradient(#e2e8f0 1px, transparent 1px);
        background-size: 24px 24px;
    }

    /* Hero Header Container */
    .hero-container {
        background: linear-gradient(135deg, #0c2340 0%, #0369a1 100%);
        padding: 24px 32px;
        border-radius: 16px;
        color: #ffffff;
        margin-bottom: 20px;
        box-shadow: 0 10px 25px -5px rgba(12, 35, 64, 0.25);
        display: flex;
        align-items: center;
        justify-content: space-between;
    }
    .hero-title {
        font-size: 32px !important;
        font-weight: 800 !important;
        letter-spacing: -0.03em;
        margin: 0;
        display: flex;
        align-items: center;
        gap: 12px;
        color: #ffffff;
    }
    .hero-subtitle {
        font-size: 14px;
        color: #bae6fd;
        margin-top: 6px;
        font-weight: 400;
    }

    /* Executive Status Pill */
    .status-pill {
        background: rgba(255, 255, 255, 0.15);
        border: 1px solid rgba(255, 255, 255, 0.3);
        backdrop-filter: blur(8px);
        padding: 8px 16px;
        border-radius: 9999px;
        font-size: 13px;
        font-weight: 600;
        color: #ffffff;
        display: flex;
        align-items: center;
        gap: 8px;
    }
    .pulse-dot {
        width: 8px;
        height: 8px;
        background: #38bdf8;
        border-radius: 50%;
        box-shadow: 0 0 10px #38bdf8;
    }

    /* Interactive Metric Cards */
    div[data-testid="stMetric"] {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        padding: 20px 24px;
        border-radius: 14px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.03);
        transition: all 0.25s ease-in-out;
    }
    div[data-testid="stMetric"]:hover {
        transform: translateY(-4px);
        box-shadow: 0 12px 24px -4px rgba(2, 132, 199, 0.18);
        border-color: #0284c7;
    }
    div[data-testid="stMetricLabel"] p {
        font-size: 13px !important;
        font-weight: 700 !important;
        color: #64748b !important;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    div[data-testid="stMetricValue"] div {
        color: #0284c7 !important;
        font-weight: 900 !important;
        font-size: 32px !important;
        letter-spacing: -0.02em;
    }

    /* Guardrail Banner */
    .guardrail-strip {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-left: 5px solid #0284c7;
        padding: 12px 20px;
        border-radius: 10px;
        margin-bottom: 24px;
        font-size: 13px;
        color: #334155;
        box-shadow: 0 2px 6px rgba(0,0,0,0.02);
    }

    /* Razorpay Primary Buttons */
    div.stButton > button:first-child {
        background: linear-gradient(135deg, #0284c7 0%, #0369a1 100%) !important;
        color: #ffffff !important;
        border: none !important;
        border-radius: 10px !important;
        padding: 14px 28px !important;
        font-size: 15px !important;
        font-weight: 700 !important;
        box-shadow: 0 4px 14px rgba(2, 132, 199, 0.3) !important;
        transition: all 0.2s ease-in-out !important;
    }
    div.stButton > button:first-child:hover {
        background: linear-gradient(135deg, #0369a1 0%, #0c4a6e 100%) !important;
        box-shadow: 0 8px 20px rgba(2, 132, 199, 0.45) !important;
        transform: translateY(-2px);
    }

    /* Clean Tabs */
    button[data-baseweb="tab"] {
        font-size: 15px !important;
        font-weight: 700 !important;
        padding: 14px 22px !important;
        color: #64748b !important;
    }
    button[aria-selected="true"] {
        color: #0284c7 !important;
        border-bottom: 3px solid #0284c7 !important;
    }
</style>
""", unsafe_allow_html=True)

# Initialize database schema
init_db()

# Premium Hero Banner
st.markdown("""
<div class="hero-container">
    <div>
        <div class="hero-title">⚡ RazorRecover AI</div>
        <div class="hero-subtitle">Enterprise Autonomous Revenue Recovery Engine for Razorpay Checkouts</div>
    </div>
    <div class="status-pill">
        <span class="pulse-dot"></span> System Live & Guardrails Armed
    </div>
</div>
""", unsafe_allow_html=True)

# Active Guardrail Enforcement Strip
st.markdown("""
<div class="guardrail-strip">
    🛡️ <strong>Active Financial Constraints:</strong> Max Margin Discount <code>10.0% (Cap: ₹500)</code> | Max Automated Retries <code>≤ 2</code> | Escalation Floor <code>≥ ₹25,000</code> | Hard Declines Blocked
</div>
""", unsafe_allow_html=True)

# Preset Scenarios
PRESETS = {
    "Select a Scenario Preset...": None,
    "1. Cart Drop-off (Eligible for 5% Margin Incentive)": {
        "record_id": "PRESET_DROPOFF_01",
        "order_id": "order_cart_9921",
        "customer_name": "Aditi Rao",
        "customer_email": "aditi.rao@example.com",
        "customer_tier": "standard",
        "amount_inr": 3499.0,
        "failure_type": "CHECKOUT_DROPOFF",
        "error_code": "CUSTOMER_EXITED",
        "retry_count": 0,
        "opted_out": False
    },
    "2. High-Value Desk Escalation (Amount >= ₹25,000)": {
        "record_id": "PRESET_ESC_02",
        "order_id": "order_hival_4410",
        "customer_name": "Rohan Enterprise Solutions",
        "customer_email": "finance@rohanent.com",
        "customer_tier": "standard",
        "amount_inr": 48500.0,
        "failure_type": "CHECKOUT_DROPOFF",
        "error_code": "GATEWAY_TIMEOUT",
        "retry_count": 0,
        "opted_out": False
    },
    "3. Hard Decline (Card Blocked - Zero Outreach Rule)": {
        "record_id": "PRESET_STOP_03",
        "order_id": "order_decline_7712",
        "customer_name": "Karthik Verma",
        "customer_email": "karthik.v@example.com",
        "customer_tier": "standard",
        "amount_inr": 1800.0,
        "failure_type": "PAYMENT_DEGRADATION",
        "error_code": "CARD_BLOCKED",
        "retry_count": 1,
        "opted_out": False
    },
    "4. B2B Receivable Overdue (Enterprise Multi-Failure)": {
        "record_id": "PRESET_B2B_04",
        "order_id": "order_b2b_1088",
        "customer_name": "Nexus Dynamics LLP",
        "customer_email": "accounts@nexusdyn.com",
        "customer_tier": "enterprise",
        "amount_inr": 16500.0,
        "failure_type": "OVERDUE_RECEIVABLES",
        "error_code": "INVOICE_PAST_DUE",
        "retry_count": 1,
        "opted_out": False
    }
}

tab1, tab2, tab3, tab4 = st.tabs([
    "📊 Batch Recovery Benchmark & Visual Analytics",
    "🎯 Live Scenario & Sandbox Resolution",
    "⚡ Webhook Ingestion Simulator",
    "🗄️ Immutable Audit Database"
])

# ---------------- TAB 1: BATCH BENCHMARK & CHARTS ----------------
with tab1:
    st.markdown("### High-Throughput Batch Processing Simulation")
    st.write("Concurrently diagnoses and recovers 50 heterogeneous payment failures using deterministic algorithmic routing.")

    if st.button("🚀 Run Batch Recovery Benchmark (50 Records)", type="primary", use_container_width=True):
        batch_records = []
        failure_categories = [
            ("CHECKOUT_DROPOFF", "CUSTOMER_ABANDONED", 2400.0, 0, "standard"),
            ("PAYMENT_DEGRADATION", "GATEWAY_TIMEOUT", 1850.0, 1, "standard"),
            ("PAYMENT_DEGRADATION", "CARD_BLOCKED", 4200.0, 0, "standard"),
            ("SUBSCRIPTION_MANDATE_FAIL", "INSUFFICIENT_FUNDS", 999.0, 2, "standard"),
            ("OVERDUE_RECEIVABLES", "PAYMENT_PENDING", 32000.0, 0, "enterprise"),
        ]

        for i in range(50):
            cat = failure_categories[i % len(failure_categories)]
            batch_records.append({
                "record_id": f"BATCH_{i+1:03d}",
                "order_id": f"order_batch_{1000 + i}",
                "customer_name": f"Merchant Customer #{i+1}",
                "customer_email": f"customer_{i+1}@example.com",
                "customer_tier": cat[4],
                "amount_inr": cat[2] + (i * 50.0),
                "failure_type": cat[0],
                "error_code": cat[1],
                "retry_count": cat[3],
                "opted_out": (i == 48)
            })

        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
            results = list(executor.map(process_recovery_pipeline, batch_records))

        for r in results:
            save_recovery_record(r)

        df = pd.DataFrame(results)
        recovered_df = df[df["status"] == "RECOVERED"]
        escalated_df = df[df["status"] == "ESCALATED_TO_HUMAN"]
        stopped_df = df[df["status"] == "STOPPED"]

        total_risk = df["money_at_risk"].sum()
        total_rec = df["money_recovered"].sum()

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Money at Risk", f"₹{total_risk:,.2f}")
        col2.metric("Money Recovered", f"₹{total_rec:,.2f}", delta=f"{(total_rec/total_risk)*100:.1f}% Salvaged")
        col3.metric("Auto-Recovered", f"{len(recovered_df)} records")
        col4.metric("Escalated / Stopped", f"{len(escalated_df)} / {len(stopped_df)} records")

        st.markdown("<br>", unsafe_allow_html=True)

        chart_col1, chart_col2 = st.columns(2)

        with chart_col1:
            st.markdown("#### 🍩 Pipeline Resolution Breakdown")
            status_counts = df["status"].value_counts().reset_index()
            status_counts.columns = ["Status", "Count"]
            
            fig_donut = px.pie(
                status_counts,
                values="Count",
                names="Status",
                hole=0.6,
                color="Status",
                color_discrete_map={
                    "RECOVERED": "#0284c7",
                    "ESCALATED_TO_HUMAN": "#f59e0b",
                    "STOPPED": "#ef4444"
                }
            )
            fig_donut.update_traces(
                textposition="inside",
                textinfo="percent+label",
                marker=dict(line=dict(color="#ffffff", width=2))
            )
            fig_donut.update_layout(
                margin=dict(t=10, b=10, l=10, r=10),
                height=320,
                showlegend=False,
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)"
            )
            st.plotly_chart(fig_donut, use_container_width=True)

        with chart_col2:
            st.markdown("#### 📊 Value at Risk vs. Recovered by Vector")
            vector_agg = df.groupby("failure_type")[["money_at_risk", "money_recovered"]].sum().reset_index()
            
            fig_bar = go.Figure()
            fig_bar.add_trace(go.Bar(
                x=vector_agg["failure_type"],
                y=vector_agg["money_at_risk"],
                name="At Risk",
                marker_color="#94a3b8"
            ))
            fig_bar.add_trace(go.Bar(
                x=vector_agg["failure_type"],
                y=vector_agg["money_recovered"],
                name="Recovered",
                marker_color="#0284c7"
            ))
            fig_bar.update_layout(
                barmode="group",
                margin=dict(t=10, b=10, l=10, r=10),
                height=320,
                hovermode="x unified",
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                yaxis=dict(showgrid=True, gridcolor="#e2e8f0")
            )
            st.plotly_chart(fig_bar, use_container_width=True)

        st.markdown("#### 📋 Batch Transaction Ledger")
        st.dataframe(
            df[["record_id", "order_id", "failure_type", "money_at_risk", "money_recovered", "status", "reason"]],
            use_container_width=True
        )

# ---------------- TAB 2: LIVE SCENARIO TRIGGER & MODAL ----------------
with tab2:
    st.markdown("### Manual Event Trigger & Sandbox Resolution")
    st.write("Test individual payment failures against the deterministic guardrail matrix.")

    selected_preset_name = st.selectbox("⚡ Quick Load Scenario Preset", list(PRESETS.keys()))
    preset = PRESETS.get(selected_preset_name)

    with st.form("manual_recovery_form"):
        col1, col2 = st.columns(2)
        with col1:
            order_id = st.text_input("Order ID", value=preset.get("order_id", "order_live_101") if preset else "order_live_101")
            customer_name = st.text_input("Customer Name", value=preset.get("customer_name", "Sri Lakshmi") if preset else "Sri Lakshmi")
            customer_email = st.text_input("Customer Email", value=preset.get("customer_email", "customer@example.com") if preset else "customer@example.com")
            customer_tier = st.selectbox("Customer Tier", ["standard", "enterprise"], index=1 if preset and preset.get("customer_tier") == "enterprise" else 0)

        with col2:
            amount_inr = st.number_input("Amount (₹)", min_value=0.0, value=float(preset.get("amount_inr", 2500.0)) if preset else 2500.0, step=100.0)
            failure_type = st.selectbox("Failure Vector", ["CHECKOUT_DROPOFF", "PAYMENT_DEGRADATION", "SUBSCRIPTION_MANDATE_FAIL", "OVERDUE_RECEIVABLES"], index=0)
            error_code = st.text_input("Error Code", value=preset.get("error_code", "PAYMENT_TIMEOUT") if preset else "PAYMENT_TIMEOUT")
            retry_count = st.number_input("Retry Count", min_value=0, max_value=10, value=int(preset.get("retry_count", 0)) if preset else 0)

        send_real_email = st.checkbox("📧 Dispatch Real Recovery Email via SMTP")
        submit_btn = st.form_submit_button("⚡ Trigger Autonomous Recovery Agent", type="primary", use_container_width=True)

    @st.dialog("⚡ RazorRecover Action Report")
    def show_resolution_modal(res, email_dispatched):
        st.markdown(f"### Status: **{res['status']}**")
        st.write(f"**Reason:** {res['reason']}")
        
        if res["status"] == "RECOVERED":
            st.success("Recovery Strategy Approved & Official Payment Link Generated.")
            st.info(f"**Dispatched Outreach:**\n\n{res['message']}")
            if res.get("payment_link"):
                st.link_button("💳 Open Secure Razorpay Checkout", res["payment_link"], use_container_width=True)
            if email_dispatched:
                st.caption("✅ Live SMTP notification dispatched to customer.")
        elif res["status"] == "ESCALATED_TO_HUMAN":
            st.warning("⚠️ Margin / Enterprise Floor Exceeded. Escalated to Account Desk.")
        else:
            st.error("🛑 Stopping Rule Enforced (Hard Decline / Retry Limit Hit).")

        st.markdown("**Deterministic Audit Trail:**")
        st.json(res["audit_trail"])

    if submit_btn:
        payload = {
            "record_id": f"MANUAL_{datetime.now().strftime('%H%M%S')}",
            "order_id": order_id,
            "customer_name": customer_name,
            "customer_email": customer_email,
            "customer_tier": customer_tier,
            "amount_inr": amount_inr,
            "failure_type": failure_type,
            "error_code": error_code,
            "retry_count": retry_count,
            "opted_out": False
        }

        result = process_recovery_pipeline(payload)
        save_recovery_record(result)

        email_ok = False
        if send_real_email and customer_email and result["status"] == "RECOVERED":
            email_ok = send_recovery_email(customer_email, customer_name, order_id, result.get("payment_link", ""), result["message"])

        show_resolution_modal(result, email_ok)

# ---------------- TAB 3: WEBHOOK SIMULATOR ----------------
with tab3:
    st.markdown("### Razorpay Webhook Ingestion & HMAC Verification")
    st.write("Validates incoming `payment.failed` payloads using SHA-256 HMAC signature validation.")

    sample_webhook_payload = {
        "event": "payment.failed",
        "account_id": "acc_razorrecover_live",
        "contains": ["payment"],
        "payload": {
            "payment": {
                "entity": {
                    "id": "pay_test_998124",
                    "order_id": "order_hook_7721",
                    "amount": 450000,
                    "currency": "INR",
                    "status": "failed",
                    "error_code": "BAD_REQUEST_ERROR",
                    "error_description": "Payment failed due to bank timeout",
                    "notes": {
                        "customer_name": "Vikram Malhotra",
                        "customer_email": "vikram@example.com"
                    }
                }
            }
        }
    }

    st.json(sample_webhook_payload)

    if st.button("📥 Ingest & Process Webhook (HMAC-SHA256)", type="primary"):
        sim_res = simulate_incoming_webhook(sample_webhook_payload)
        
        if sim_res.get("signature_verified"):
            st.success(f"HMAC Signature Verified: `{sim_res.get('signature_sample')}`")
            rec_result = sim_res.get("recovery_result", {})
            save_recovery_record(rec_result)

            st.write(f"**Pipeline Action:** {rec_result.get('status')} ({rec_result.get('reason')})")
            if rec_result.get("payment_link"):
                st.link_button("🔗 Open Webhook-Generated Payment Link", rec_result.get("payment_link"))
        else:
            st.error("HMAC Signature Verification Failed!")

# ---------------- TAB 4: IMMUTABLE AUDIT DATABASE ----------------
with tab4:
    st.markdown("### Immutable Transaction Audit Log")
    st.write("Regulatory compliance view with real-time text query filtering.")

    col1, col2 = st.columns([3, 1])
    with col1:
        search_query = st.text_input("🔍 Search Database (Order ID, Customer Name, or Status):", placeholder="e.g. order_live_101, RECOVERED, ESCALATED")
    with col2:
        st.write("")
        st.write("")
        refresh_btn = st.button("🔄 Refresh Database", use_container_width=True)

    records = get_all_records()
    if records:
        db_df = pd.DataFrame(records)
        
        if search_query.strip():
            q = search_query.strip().lower()
            db_df = db_df[
                db_df["order_id"].astype(str).str.lower().str.contains(q) |
                db_df["customer_name"].astype(str).str.lower().str.contains(q) |
                db_df["status"].astype(str).str.lower().str.contains(q) |
                db_df["failure_type"].astype(str).str.lower().str.contains(q)
            ]

        st.dataframe(
            db_df[["id", "order_id", "customer_name", "failure_type", "amount_inr", "money_recovered", "status", "created_at"]],
            use_container_width=True
        )

        with st.expander("🔍 View Raw JSON Audit Trails"):
            for rec in records[:10]:
                st.markdown(f"**Order:** `{rec.get('order_id')}` | **Customer:** `{rec.get('customer_name')}` | **Status:** `{rec.get('status')}`")
                try:
                    trail = json.loads(rec.get("audit_trail", "[]"))
                    st.json(trail)
                except Exception:
                    st.write(rec.get("audit_trail"))
                st.divider()
    else:
        st.info("No records in audit store. Trigger a batch benchmark or live scenario to generate logs.")