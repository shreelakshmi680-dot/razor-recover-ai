# ⚡ RazorRecover AI
**Autonomous Revenue Recovery Engine with Deterministic Financial Guardrails**

I built **RazorRecover AI** to solve a real fintech dilemma: how to recover lost revenue from failed Razorpay transactions without letting an autonomous agent hallucinate discounts or spam customers.

---

### 💡 The Core Idea

When a customer's payment fails (cart abandonment, network timeout, or expired mandate), sending generic automated retries can backfire. Unrestricted agents might hand out massive discounts or repeatedly message blocked cards. 

This project enforces **hard deterministic rules** before any outreach or link generation happens:

* **Margin Safety:** Discounts are strictly capped at **10% (max ₹500)** to protect merchant profits.
* **Anti-Spam Threshold:** Maximum of **2 automated retries**. If it still fails, the system halts.
* **Instant Cutoff:** Hard failures like `CARD_BLOCKED` or `INSUFFICIENT_FUNDS` stop immediately (zero outreach).
* **Human-in-the-Loop Desk:** High-value transactions (**≥ ₹25,000**) and Enterprise tiers are escalated directly to account managers.

---

### 🛠️ How the System Works

1. **Event Ingestion:** Captures failed payments through manual inputs or Razorpay Webhooks (verified with HMAC-SHA256 signatures).
2. **Guardrail Engine:** Evaluates the failure vector, retry history, and amount against the safety matrix.
3. **Action Dispatch:** Generates official Razorpay payment links (or interactive test sandbox links) and triggers notification alerts.
4. **Audit Logging:** Every single decision and stopping rule is recorded in an immutable SQLite database for complete traceability.

---

### 🖥️ Dashboard Features

* **Batch Benchmark:** Tests high-throughput processing across 50 concurrent payment failure scenarios with interactive Plotly analytics.
* **Live Sandbox & Checkout:** Real-time testing of single recovery scenarios with instant checkout previews.
* **Webhook Simulator:** Tests cryptographic signature verification for inbound payment events.
* **Audit Database:** Live transaction log with real-time search and filter capabilities.

---

### 🧪 Running Tests & Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Run the test suite
python -m pytest

# Run the dashboard
python -m streamlit run dashboard/app.py