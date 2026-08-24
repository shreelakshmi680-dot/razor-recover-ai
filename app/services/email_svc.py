"""
RazorRecover AI - SMTP Email Outreach Service
Dispatches recovery links and customer nudges via secure SMTP.
"""

import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path
from dotenv import load_dotenv

# Force load .env from project root
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
env_path = ROOT_DIR / ".env"
load_dotenv(dotenv_path=env_path, override=True)


def send_recovery_email(to_email: str, customer_name: str, order_id: str, payment_link: str, message: str) -> bool:
    """
    Sends an automated recovery email that links directly to the in-app payment confirmation flow.
    """
    smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com").strip()
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    smtp_user = (os.getenv("SMTP_USERNAME") or "shreelakshmi680@gmail.com").strip()
    smtp_pass = (os.getenv("SMTP_PASSWORD") or "fsqdtmldirihwtvc").strip().replace(" ", "")

    # Deep link to Tab 2 with query parameters for in-app checkout
    checkout_url = f"http://localhost:8502/?order_id={order_id}&mode=checkout"

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"⚡ Action Required: Complete your order #{order_id}"
        msg["From"] = f"RazorRecover <{smtp_user}>"
        msg["To"] = to_email

        html_body = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>RazorRecover Payment</title>
</head>
<body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: #f8fafc; margin: 0; padding: 20px;">
    <div style="max-width: 560px; margin: 0 auto; background: #ffffff; border: 1px solid #e2e8f0; border-radius: 12px; padding: 32px; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);">
        
        <div style="display: flex; align-items: center; margin-bottom: 20px;">
            <h2 style="color: #0284c7; margin: 0; font-size: 22px; font-weight: 700;">⚡ RazorRecover Alert</h2>
        </div>
        
        <p style="font-size: 16px; color: #334155; line-height: 1.6; margin: 0 0 24px 0;">
            {message}
        </p>
        
        <div style="text-align: center; margin: 32px 0;">
            <a href="{checkout_url}" target="_blank" rel="noopener noreferrer" style="background-color: #0284c7; color: #ffffff; padding: 14px 32px; text-decoration: none; border-radius: 8px; font-weight: 600; font-size: 16px; display: inline-block; box-shadow: 0 4px 6px -1px rgba(2, 132, 199, 0.3);">
                💳 Complete Secure Payment
            </a>
        </div>
        
        <hr style="border: none; border-top: 1px solid #f1f5f9; margin: 24px 0;">
        
        <p style="font-size: 12px; color: #94a3b8; margin: 0; line-height: 1.5;">
            Order Reference: <strong>#{order_id}</strong><br>
            Protected by <strong>RazorRecover Autonomous Guardrail Engine</strong>.
        </p>
    </div>
</body>
</html>
"""

        msg.attach(MIMEText(html_body, "html"))

        with smtplib.SMTP(smtp_server, smtp_port, timeout=10) as server:
            server.starttls()
            server.login(smtp_user, smtp_pass)
            server.sendmail(smtp_user, to_email, msg.as_string())

        print(f"[SMTP Success] Email dispatched to {to_email} pointing to: {checkout_url}")
        return True

    except Exception as e:
        print(f"[SMTP Error] Failed to send email: {e}")
        return False