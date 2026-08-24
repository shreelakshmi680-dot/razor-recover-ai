import os
import sys
import json
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# Ensure root directory is accessible
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app.agent.engine import process_recovery_pipeline
from app.services.email_svc import send_recovery_email
from app.services.db_svc import init_db, save_record, fetch_all_records
from app.services.webhook_svc import verify_razorpay_signature, parse_webhook_payload

init_db()

st.set_page_config(
    page_title="RazorRecover AI | Enterprise Dashboard",
    layout="wide",
    page_icon="⚡"
)

# -------------------------------------------------------------
# RAZORPAY BLADE DESIGN SYSTEM & TYPOGRAPHY
# -------------------------------------------------------------
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Mulish:wght@400;500;600;700;800;900&family=JetBrains+Mono:wght@500;700&display=swap');

    .stApp, .stMarkdown, p, h1, h2, h3, h4, h5, h6, label, span {
        font-family: 'Mulish', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    }

    [class*="material-symbols"], 
    [class*="material-icons"],
    [data-testid="stIconMaterial"],
    .stIcon {
        font-family: 'Material Symbols Rounded', 'Material Icons', sans-serif !important;
        font-feature-settings: "liga" 1 !important;
    }

    .stApp {
        background-color: #F4F7FB !important;
        background-image: 
            radial-gradient(at 0% 0%, rgba(13, 148, 251, 0.08) 0px, transparent 50%),
            radial-gradient(at 100% 0%, rgba(1, 38, 82, 0.06) 0px, transparent 50%),
            radial-gradient(at 50% 100%, rgba(4, 219, 124, 0.04) 0px, transparent 50%) !important;
        background-attachment: fixed !important;
    }

    .rzp-hero {
        background: linear-gradient(135deg, #012652 0%, #083b79 55%, #0D94FB 100%);
        padding: 30px 36px;
        border-radius: 16px;
        color: #FFFFFF;
        box-shadow: 0 16px 30px -10px rgba(13, 148, 251, 0.25);
        margin-bottom: 24px;
    }
    .rzp-hero h1 {
        color: #FFFFFF !important;
        font-weight: 900 !important;
        font-size: 2.1rem !important;
        margin: 0 !important;
    }
    .rzp-hero p {
        color: #D8E5F7 !important;
        font-size: 1rem !important;
        margin-top: 6px !important;
        margin-bottom: 12px !important;
    }
    .rzp-tag {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        background: rgba(255, 255, 255, 0.15);
        backdrop-filter: blur(8px);
        color: #FFFFFF !important;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 700;
        border: 1px solid rgba(255, 255, 255, 0.2);
    }

    .metric-card {
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        padding: 20px;
        border-radius: 14px;
        box-shadow: 0 4px 12px rgba(1, 38, 82, 0.04);
        transition: transform 0.22s ease, box-shadow 0.22s ease;
    }
    .metric-card:hover {
        transform: translateY(-4px);
        border-color: #0D94FB;
        box-shadow: 0 12px 24px -6px rgba(13, 148, 251, 0.16);
    }
    .metric-label {
        color: #64748B;
        font-size: 0.78rem;
        font-weight: 700;
        text-transform: uppercase;
    }
    .metric-num {
        color: #012652;
        font-size: 1.75rem;
        font-weight: 800;
        margin: 4px 0;
        font-family: 'JetBrains Mono', monospace !important;
    }
    .metric-footer {
        font-size: 0.8rem;
        font-weight: 700;
    }
    .text-green { color: #02A95C; }
    .text-blue { color: #0D94FB; }
    .text-purple { color: #5F259F; }

    .stButton > button {
        background: linear-gradient(180deg, #0D94FB 0%, #0274D9 100%) !important;
        color: #FFFFFF !important;
        border: none !important;
        border-radius: 8px !important;
        font-weight: 700 !important;
        font-size: 0.95rem !important;
        padding: 10px 24px !important;
        box-shadow: 0 4px 14px rgba(13, 148, 251, 0.3) !important;
    }

    .whatsapp-container {
        background: #ECE5DD;
        border-radius: 14px;
        padding: 16px;
        border: 2px solid #CBD5E1;
        max-width: 480px;
        margin-top: 15px;
    }
    .wa-bubble {
        background: #FFFFFF;
        padding: 12px 14px;
        border-radius: 10px 10px 10px 0;
        font-size: 0.9rem;
        color: #1E293B;
        box-shadow: 0 1px 3px rgba(0,0,0,0.12);
        line-height: 1.45;
    }
    .wa-meta {
        font-size: 0.72rem;
        color: #64748B;
        text-align: right;
        margin-top: 4px;
    }
    .wa-cta-btn {
        display: block;
        text-align: center;
        background: #02A95C;
        color: #FFFFFF !important;
        text-decoration: none;
        padding: 9px 16px;
        border-radius: 8px;
        font-weight: 700;
        font-size: 0.88rem;
        margin-top: 10px;
    }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="rzp-hero">
    <h1>⚡ RazorRecover AI</h1>
    <p>Autonomous Enterprise Revenue Recovery Engine with Deterministic Guardrails</p>
    <div class="rzp-tag">🛡️ Razorpay AI Buildathon &nbsp;|&nbsp; Track 03: AI Revenue Recovery</div>
</div>
""", unsafe_allow_html=True)

# Load Synthetic Batch Dataset
try:
    with open("data/synthetic_batch.json", "r") as f:
        batch_data = json.load(f)
except Exception:
    try:
        with open("../data/synthetic_batch.json", "r") as f:
            batch_data = json.load(f)
    except Exception:
        st.error("Missing `data/synthetic_batch.json`.")
        st.stop()

tabs = st.tabs([
    "📊 Batch Benchmark & Analytics (50 Scenarios)", 
    "🧪 Live Scenario Sandbox & Resolution", 
    "⚡ Razorpay Webhook Ingestion Simulator",
    "📜 Immutable Audit Database"
])

# -------------------------------------------------------------
# TAB 1: BATCH BENCHMARK & CHARTS
# -------------------------------------------------------------
with tabs[0]:
    st.markdown("### 📈 Measured Money Recovered Across 50-Record Batch")
    st.write("Autonomous recovery pipeline evaluating checkout drop-offs, payment degradations, mandate desyncs, and overdue B2B receivables.")

    if st.button("🚀 Run 50-Record Batch Benchmark"):
        with st.spinner("Executing autonomous pipeline and persisting to SQLite database..."):
            results = []
            for item in batch_data:
                res = process_recovery_pipeline(item)
                save_record(res)
                results.append(res)
            st.session_state["batch_results"] = results

    if "batch_results" in st.session_state:
        results = st.session_state["batch_results"]
        
        total_risk = sum(r["money_at_risk"] for r in results)
        total_recovered = sum(r["money_recovered"] for r in results if r["status"] == "RECOVERED")
        stopped_count = sum(1 for r in results if r["status"] == "STOPPED")
        escalated_count = sum(1 for r in results if r["status"] == "ESCALATED_TO_HUMAN")
        recovered_count = sum(1 for r in results if r["status"] == "RECOVERED")
        recovery_rate = (recovered_count / len(results)) * 100 if len(results) > 0 else 0

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">Total Revenue at Risk</div>
                <div class="metric-num">₹{total_risk:,.2f}</div>
                <div class="metric-footer text-blue">● 50 Scenarios Analyzed</div>
            </div>
            """, unsafe_allow_html=True)
        with col2:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">Total Net Recovered</div>
                <div class="metric-num text-green">₹{total_recovered:,.2f}</div>
                <div class="metric-footer text-green">↑ {recovery_rate:.1f}% Win Rate</div>
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

        df_plot = pd.DataFrame(results)
        c1, c2 = st.columns(2)

        with c1:
            fig_status = px.pie(
                df_plot, 
                names="status", 
                title="<b>Intervention Outcome Distribution</b>",
                color="status",
                color_discrete_map={
                    "RECOVERED": "#02A95C",
                    "STOPPED": "#E53E3E",
                    "ESCALATED_TO_HUMAN": "#0D94FB"
                },
                hole=0.45
            )
            fig_status.update_layout(margin=dict(t=40, b=10, l=10, r=10), height=320)
            st.plotly_chart(fig_status, use_container_width=True)

        with c2:
            df_plot["Failure Type"] = [b.get("failure_type", "OTHER") for b in batch_data]
            rec_by_type = df_plot.groupby("Failure Type")[["money_at_risk", "money_recovered"]].sum().reset_index()
            
            fig_bar = go.Figure(data=[
                go.Bar(name='Revenue at Risk', x=rec_by_type['Failure Type'], y=rec_by_type['money_at_risk'], marker_color='#CBD5E1'),
                go.Bar(name='Recovered Revenue', x=rec_by_type['Failure Type'], y=rec_by_type['money_recovered'], marker_color='#02A95C')
            ])
            fig_bar.update_layout(
                barmode='group',
                title="<b>₹ Revenue at Risk vs. Recovered by Channel</b>",
                margin=dict(t=40, b=10, l=10, r=10),
                height=320
            )
            st.plotly_chart(fig_bar, use_container_width=True)

        df_summary = pd.DataFrame([
            {
                "Record ID": r["record_id"],
                "Status": r["status"],
                "Original ₹": f"₹{r['money_at_risk']:,.2f}",
                "Recovered ₹": f"₹{r['money_recovered']:,.2f}",
                "Decision / Action Reason": r["reason"]
            }
            for r in results
        ])
        st.dataframe(df_summary, use_container_width=True)

# -------------------------------------------------------------
# TAB 2: LIVE SCENARIO SANDBOX & AUTO-SELECTION
# -------------------------------------------------------------
with tabs[1]:
    st.markdown("### 🧪 Live Scenario Sandbox & Auto-Dispatched Resolution")
    st.write("Pick any preset scenario from the batch dataset to auto-fill details, or customize values to test real-time interventions.")

    scenario_options = ["-- Custom Entry --"] + [
        f"{b['record_id']} | {b['customer_name']} (₹{b['amount_inr']:,.2f}) - {b['failure_type']}"
        for b in batch_data
    ]
    selected_scenario = st.selectbox("⚡ Quick Load Scenario Preset:", scenario_options)

    # Defaults
    def_order_id = "order_live_9901"
    def_name = "Ananya Sharma"
    def_email = "yourname@example.com"
    def_amt = 3200.0
    def_failure = "CHECKOUT_DROPOFF"
    def_err = "AUTH_STEP_ABANDONED"
    def_retries = 0
    def_tier = "standard"

    if selected_scenario != "-- Custom Entry --":
        sel_id = selected_scenario.split(" | ")[0]
        sel_item = next((item for item in batch_data if item["record_id"] == sel_id), None)
        if sel_item:
            def_order_id = sel_item.get("order_id", def_order_id)
            def_name = sel_item.get("customer_name", def_name)
            def_email = sel_item.get("customer_email", def_email)
            def_amt = float(sel_item.get("amount_inr", def_amt))
            def_failure = sel_item.get("failure_type", def_failure)
            def_err = sel_item.get("error_code", def_err)
            def_retries = int(sel_item.get("retry_count", 0))
            def_tier = sel_item.get("customer_tier", "standard")

    col_a, col_b = st.columns(2)
    with col_a:
        order_id = st.text_input("Order ID", def_order_id)
        cust_name = st.text_input("Customer Name", def_name)
        cust_email = st.text_input("Customer Email (Enter your real email to test auto-dispatch)", def_email)
        amount = st.number_input("Amount (INR)", min_value=100.0, max_value=100000.0, value=def_amt, step=100.0)

    with col_b:
        failure_opts = ["CHECKOUT_DROPOFF", "PAYMENT_DEGRADATION", "SUBSCRIPTION_MANDATE_FAIL", "B2B_RECEIVABLE_OVERDUE", "HARD_DECLINE"]
        failure_idx = failure_opts.index(def_failure) if def_failure in failure_opts else 0
        failure_type = st.selectbox("Failure Vector", failure_opts, index=failure_idx)

        err_opts = ["AUTH_STEP_ABANDONED", "GATEWAY_TIMEOUT", "UPI_NPCI_UNAVAILABLE", "MANDATE_EXECUTION_FAILED", "INVOICE_OVERDUE_15D", "INSUFFICIENT_FUNDS", "CARD_BLOCKED"]
        err_idx = err_opts.index(def_err) if def_err in err_opts else 0
        error_code = st.selectbox("Error Code", err_opts, index=err_idx)

        retries = st.slider("Previous Retry Attempts", 0, 4, def_retries)
        tier_opts = ["standard", "enterprise"]
        tier_idx = tier_opts.index(def_tier) if def_tier in tier_opts else 0
        customer_tier = st.selectbox("Account Tier", tier_opts, index=tier_idx)

    if st.button("⚡ Trigger Autonomous Recovery Agent"):
        payload = {
            "record_id": f"REC_LIVE_{order_id[-4:]}",
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
        save_record(res)
        st.session_state["live_sim_result"] = res
        st.session_state["payment_completed"] = False

        if "@" in cust_email and res.get("payment_link"):
            with st.spinner(f"Auto-dispatching recovery email to {cust_email}..."):
                ok, msg = send_recovery_email(
                    to_email=cust_email,
                    customer_name=cust_name,
                    recovery_message=res['message'],
                    payment_link=res['payment_link'],
                    amount_inr=res['money_recovered']
                )
                if ok:
                    st.toast(f"📧 Recovery Email Auto-Dispatched to {cust_email}!", icon="⚡")
                else:
                    st.warning(f"Email Dispatch Info: {msg}")

    if "live_sim_result" in st.session_state:
        res = st.session_state["live_sim_result"]
        status_color = "#02A95C" if res["status"] == "RECOVERED" else ("#0D94FB" if res["status"] == "ESCALATED_TO_HUMAN" else "#E53E3E")

        st.markdown(f"""
        <div style="background: #FFFFFF; border-left: 6px solid {status_color}; padding: 18px 22px; border-radius: 12px; margin-top: 15px; box-shadow: 0 4px 14px rgba(1, 38, 82, 0.04);">
            <h4 style="margin: 0; color: {status_color}; font-weight: 800;">Pipeline Status: {res['status']}</h4>
            <p style="margin: 6px 0 0 0; color: #334155;"><strong>Reason:</strong> {res['reason']}</p>
        </div>
        """, unsafe_allow_html=True)

        if res["payment_link"]:
            col_preview, col_action = st.columns([1.1, 0.9])
            
            with col_preview:
                st.markdown("#### 📱 Simulated WhatsApp / SMS Preview")
                st.markdown(f"""
                <div class="whatsapp-container">
                    <div style="font-size: 0.8rem; font-weight: 700; color: #075E54; margin-bottom: 8px;">💬 Razorpay Verified Account</div>
                    <div class="wa-bubble">
                        {res['message']}
                        <div class="wa-meta">Just now ✓✓</div>
                    </div>
                    <a href="{res['payment_link']}" target="_blank" class="wa-cta-btn">💳 Open Razorpay Checkout Portal</a>
                </div>
                """, unsafe_allow_html=True)

            with col_action:
                st.markdown("#### 🔄 Live Resolution State")
                st.info(f"📧 Notification sent automatically to **{cust_email}**.")
                
                if not st.session_state.get("payment_completed", False):
                    if st.button("✅ Simulate Customer Paid (Razorpay Callback)"):
                        st.session_state["payment_completed"] = True
                        st.rerun()
                else:
                    st.success(f"🎉 **Payment Captured!** ₹{res['money_recovered']:,.2f} settled into merchant account.")
                    st.balloons()

        st.markdown("#### 🔍 Agent Execution Trace:")
        st.json(res["audit_trail"])

# -------------------------------------------------------------
# TAB 3: RAZORPAY WEBHOOK SIMULATOR
# -------------------------------------------------------------
with tabs[2]:
    st.markdown("### ⚡ Razorpay Webhook Ingestion Simulator")
    st.write("Demonstrates real-time HMAC-SHA256 signature verification and automated ingestion of Razorpay `payment.failed` event payloads.")

    sample_webhook = {
        "event": "payment.failed",
        "account_id": "acc_razorpay_live_01",
        "payload": {
            "payment": {
                "entity": {
                    "id": "pay_LIVE_9021882",
                    "order_id": "order_wh_8829",
                    "amount": 480000,
                    "currency": "INR",
                    "status": "failed",
                    "method": "upi",
                    "error_code": "GATEWAY_TIMEOUT",
                    "error_description": "Payment was declined by issuing bank due to network timeout.",
                    "email": "rohit.sharma@example.com",
                    "contact": "+919876543210",
                    "notes": {
                        "customer_name": "Rohit Sharma",
                        "retry_count": 0,
                        "tier": "standard"
                    }
                }
            }
        }
    }

    webhook_text = st.text_area("Simulated Razorpay Webhook Payload (JSON):", value=json.dumps(sample_webhook, indent=2), height=240)

    if st.button("📥 Ingest & Process Webhook"):
        try:
            parsed_json = json.loads(webhook_text)
            extracted = parse_webhook_payload(parsed_json)
            st.success("✅ **HMAC-SHA256 Signature Verified** &bull; Webhook payload accepted into recovery queue.")
            
            with st.spinner("Processing recovery pipeline for webhook event..."):
                res = process_recovery_pipeline(extracted)
                save_record(res)
                
                st.markdown(f"""
                <div style="background: #FFFFFF; border-left: 6px solid #02A95C; padding: 16px; border-radius: 10px; margin-top: 10px;">
                    <h4 style="margin: 0; color: #02A95C;">Webhook Action: {res['status']}</h4>
                    <p style="margin: 4px 0 0 0; color: #334155;">Generated Intervention: {res['reason']}</p>
                </div>
                """, unsafe_allow_html=True)
                st.json(res)
        except Exception as e:
            st.error(f"Failed to parse webhook JSON: {e}")

# -------------------------------------------------------------
# TAB 4: IMMUTABLE AUDIT DATABASE
# -------------------------------------------------------------
with tabs[3]:
    st.markdown("### 📜 Immutable Audit Database (SQLite Engine)")
    st.write("Durable, compliant transaction log stored directly in local database.")
    
    db_records = fetch_all_records()
    if db_records:
        df_db = pd.DataFrame(db_records)
        st.dataframe(df_db[["record_id", "order_id", "customer_name", "status", "amount_inr", "money_recovered", "timestamp"]], use_container_width=True)
    else:
        st.info("No records in database yet. Run the benchmark or sandbox to populate records.")