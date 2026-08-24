import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import os
from dotenv import load_dotenv

load_dotenv()

SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "465"))
SMTP_EMAIL = os.getenv("SMTP_EMAIL", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")

def send_recovery_email(to_email: str, customer_name: str, recovery_message: str, payment_link: str, amount_inr: float) -> tuple[bool, str]:
    if not SMTP_EMAIL or not SMTP_PASSWORD:
        return False, "SMTP credentials missing in .env"

    try:
        # If the payment link is a base64 data-URI, route the email button to a safe checkout URL
        # because Gmail/Apple Mail block base64 URIs for security.
        clickable_link = "https://rzp.io/l/demo-recover-pay" if payment_link.startswith("data:") else payment_link

        msg = MIMEMultipart("alternative")
        msg["Subject"] = "⚡ Action Required: Complete your payment — RazorRecover AI"
        msg["From"] = f"RazorRecover AI <{SMTP_EMAIL}>"
        msg["To"] = to_email

        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: #F4F7FB; margin: 0; padding: 20px; }}
                .container {{ background-color: #FFFFFF; max-width: 520px; margin: 0 auto; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 15px rgba(0,0,0,0.06); border-top: 4px solid #0D94FB; }}
                .header {{ padding: 22px; background: #012652; color: #FFFFFF; text-align: center; }}
                .content {{ padding: 26px; color: #334155; font-size: 15px; line-height: 1.6; }}
                .box {{ background-color: #F8FAFC; border-left: 4px solid #0D94FB; padding: 14px 16px; border-radius: 6px; margin: 18px 0; color: #1E293B; font-size: 14.5px; }}
                .amount-tag {{ text-align: center; font-size: 20px; font-weight: 800; color: #012652; margin: 18px 0 10px 0; }}
                .btn-box {{ text-align: center; margin: 24px 0; }}
                .btn {{ background-color: #02A95C; color: #FFFFFF !important; text-decoration: none; padding: 13px 28px; border-radius: 8px; font-weight: 700; font-size: 15px; display: inline-block; }}
                .footer {{ background-color: #F8FAFC; padding: 14px; text-align: center; font-size: 12px; color: #94A3B8; border-top: 1px solid #E2E8F0; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h2 style="margin: 0; font-size: 20px; color: #FFFFFF;">⚡ RazorRecover AI Interventions</h2>
                </div>
                <div class="content">
                    <p style="margin-top: 0;">Hi <strong>{customer_name}</strong>,</p>
                    <div class="box">
                        {recovery_message}
                    </div>
                    <div class="amount-tag">
                        Payable Amount: ₹{amount_inr:,.2f}
                    </div>
                    <div class="btn-box">
                        <a href="{clickable_link}" class="btn">💳 Complete Recovery Payment</a>
                    </div>
                </div>
                <div class="footer">
                    🔒 Secured by RazorRecover AI &bull; Track 03 Buildathon Engine
                </div>
            </div>
        </body>
        </html>
        """

        msg.attach(MIMEText(html_content, "html"))

        with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT) as server:
            server.login(SMTP_EMAIL, SMTP_PASSWORD)
            server.sendmail(SMTP_EMAIL, to_email, msg.as_string())

        return True, "Email sent successfully"

    except Exception as e:
        return False, str(e)