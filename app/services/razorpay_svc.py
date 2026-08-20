import os
import razorpay
from dotenv import load_dotenv

load_dotenv()

RAZORPAY_KEY_ID = os.getenv("RAZORPAY_KEY_ID", "")
RAZORPAY_KEY_SECRET = os.getenv("RAZORPAY_KEY_SECRET", "")

client = None
if RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET and "placeholder" not in RAZORPAY_KEY_ID:
    try:
        client = razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET))
    except Exception:
        client = None

def create_recovery_payment_link(order_id: str, amount_inr: float, customer_email: str, customer_phone: str = None, description: str = "Recovery Link") -> str:
    """
    Creates a real Razorpay Test Payment Link or falls back gracefully to a mock test link.
    """
    if client:
        try:
            payload = {
                "amount": int(amount_inr * 100),
                "currency": "INR",
                "accept_partial": False,
                "description": description,
                "customer": {
                    "name": customer_email.split("@")[0],
                    "email": customer_email,
                    "contact": customer_phone or "+919999999999"
                },
                "notify": {"sms": False, "email": False},
                "reminder_enable": True,
                "notes": {
                    "recovery_order_id": order_id,
                    "engine": "RazorRecover_AI"
                }
            }
            res = client.payment_link.create(payload)
            return res.get("short_url") or res.get("url")
        except Exception as e:
            print(f"[Razorpay SDK Error] {e}")

    # Safe deterministic fallback link for local development
    return f"https://rzp.io/i/test_recovery_{order_id.replace('order_', '')}"