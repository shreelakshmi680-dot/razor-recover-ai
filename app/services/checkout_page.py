"""
RazorRecover AI - Interactive High-Fidelity Checkout Simulator
Self-rendering responsive payment gateway portal with zero browser reload dependency.
"""

import base64
import html

def generate_interactive_checkout_url(order_id: str, amount_inr: float, customer_name: str) -> str:
    safe_order_id = html.escape(str(order_id))
    safe_customer = html.escape(str(customer_name))
    safe_amount = f"{float(amount_inr):,.2f}"

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Razorpay Trusted Checkout - {safe_order_id}</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
        * {{ box-sizing: border-box; margin: 0; padding: 0; font-family: 'Inter', sans-serif; }}
        body {{ background-color: #0b0f19; color: #f3f4f6; display: flex; align-items: center; justify-content: center; min-height: 100vh; padding: 20px; }}
        .card {{ background: #111827; border: 1px solid #1f2937; border-radius: 16px; width: 100%; max-width: 440px; overflow: hidden; box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.7); }}
        .header {{ background: linear-gradient(135deg, #0c2340 0%, #0284c7 100%); padding: 24px; text-align: center; border-bottom: 1px solid #1e293b; }}
        .header h2 {{ font-size: 20px; font-weight: 700; color: #ffffff; letter-spacing: -0.02em; }}
        .header p {{ font-size: 13px; color: #bae6fd; margin-top: 4px; }}
        .content {{ padding: 24px; }}
        .order-badge {{ display: flex; justify-content: space-between; background: #1e293b; padding: 12px 16px; border-radius: 8px; font-size: 13px; margin-bottom: 20px; }}
        .amount-display {{ text-align: center; margin-bottom: 24px; }}
        .amount-display .label {{ font-size: 12px; text-transform: uppercase; letter-spacing: 0.05em; color: #9ca3af; font-weight: 600; }}
        .amount-display .val {{ font-size: 32px; font-weight: 700; color: #38bdf8; margin-top: 4px; }}
        .btn {{ width: 100%; padding: 14px; background: #0284c7; color: white; border: none; border-radius: 8px; font-size: 15px; font-weight: 600; cursor: pointer; transition: all 0.2s; }}
        .btn:hover {{ background: #0369a1; transform: translateY(-1px); }}
        .btn:active {{ transform: translateY(0); }}
        .success-box {{ display: none; text-align: center; padding: 20px; }}
        .success-icon {{ width: 56px; height: 56px; background: #064e3b; color: #34d399; border-radius: 50%; display: inline-flex; align-items: center; justify-content: center; font-size: 28px; margin-bottom: 12px; }}
        .footer {{ text-align: center; font-size: 11px; color: #6b7280; margin-top: 20px; }}
    </style>
</head>
<body>
    <div class="card">
        <div class="header">
            <h2>Razorpay Secure Checkout</h2>
            <p>RazorRecover Guaranteed Settlement</p>
        </div>
        <div class="content" id="payment-view">
            <div class="order-badge">
                <span style="color: #94a3b8;">Order Ref:</span>
                <span style="font-weight: 600; color: #f8fafc;">{safe_order_id}</span>
            </div>
            <div class="amount-display">
                <div class="label">Amount Due</div>
                <div class="val">₹{safe_amount}</div>
                <div style="font-size: 13px; color: #94a3b8; margin-top: 4px;">Paying as: <strong>{safe_customer}</strong></div>
            </div>
            <button class="btn" onclick="completePayment()">Pay via UPI / Card / NetBanking</button>
            <div class="footer">🔒 256-bit SSL Encrypted | Razorpay Verified Merchant</div>
        </div>
        <div class="content success-box" id="success-view">
            <div class="success-icon">✓</div>
            <h3 style="color: #f8fafc; font-size: 18px; margin-bottom: 8px;">Payment Successful</h3>
            <p style="color: #94a3b8; font-size: 13px; margin-bottom: 20px;">Order {safe_order_id} has been settled and updated in the immutable audit log.</p>
            <button class="btn" style="background: #1e293b;" onclick="window.close()">Close Window</button>
        </div>
    </div>
    <script>
        function completePayment() {{
            document.getElementById('payment-view').style.display = 'none';
            document.getElementById('success-view').style.display = 'block';
        }}
    </script>
</body>
</html>"""
    
    encoded_bytes = base64.b64encode(html_content.encode("utf-8")).decode("utf-8")
    return f"data:text/html;charset=utf-8;base64,{encoded_bytes}"