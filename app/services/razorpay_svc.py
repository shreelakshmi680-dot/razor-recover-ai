"""
RazorRecover AI - Razorpay Payment Service
Integrates directly with official Razorpay API for live link creation.
"""

import os
from dotenv import load_dotenv
from app.services.checkout_page import generate_interactive_checkout_url

load_dotenv()

RAZORPAY_KEY_ID = os.getenv("RAZORPAY_KEY_ID", "")
RAZORPAY_KEY_SECRET = os.getenv("RAZORPAY_KEY_SECRET", "")

def create_recovery_payment_link(order_id: str, amount_inr: float, customer_name: str, customer_email: str = "") -> dict:
    """
    Creates an authentic Razorpay Payment Link using the official SDK.
    Falls back to the interactive sandbox if API keys are not provided.
    """
    amount_inr = max(0.0, float(amount_inr))
    
    if RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET and not RAZORPAY_KEY_ID.startswith("rzp_test_placeholder"):
        try:
            import razorpay
            client = razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET))
            link_data = {
                "amount": int(round(amount_inr * 100)), # Amount in paise
                "currency": "INR",
                "accept_partial": False,
                "reference_id": order_id,
                "description": f"RazorRecover settlement for Order #{order_id}",
                "customer": {
                    "name": customer_name,
                    "email": customer_email or "customer@example.com"
                },
                "notify": {"sms": False, "email": False},
                "reminder_enable": True,
                "notes": {
                    "recovery_engine": "RazorRecover_AI",
                    "guardrail_status": "APPROVED"
                }
            }
            response = client.payment_link.create(data=link_data)
            return {
                "source": "RAZORPAY_OFFICIAL_API",
                "payment_url": response.get("short_url"),
                "plink_id": response.get("id"),
                "status": "CREATED"
            }
        except Exception:
            pass

    # Offline Interactive Sandbox Fallback
    fallback_url = generate_interactive_checkout_url(order_id, amount_inr, customer_name)
    return {
        "source": "RAZORRECOVER_SANDBOX",
        "payment_url": fallback_url,
        "plink_id": f"plink_sim_{order_id}",
        "status": "SIMULATED"
    }