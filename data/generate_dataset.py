"""
RazorRecover AI — Synthetic Recovery Dataset Generator
Track 03: AI Revenue Recovery — Razorpay AI Buildathon

Generates `data/synthetic_batch.json`: 50 realistic synthetic revenue-recovery
scenarios spanning payment degradation, checkout drop-off, subscription
mandate failures, B2B receivable overdue cases, and hard declines.

Run:
    python data/generate_dataset.py
"""

import json
import random
from pathlib import Path

# ----------------------------------------------------------------------------
# Deterministic-ish but varied output. Seed can be changed for new batches.
# ----------------------------------------------------------------------------
random.seed(42)

OUTPUT_PATH = Path(__file__).parent / "synthetic_batch.json"

# ----------------------------------------------------------------------------
# Reference data pools
# ----------------------------------------------------------------------------

FIRST_NAMES = [
    "Aarav", "Vivaan", "Aditya", "Vihaan", "Arjun", "Sai", "Reyansh", "Krishna",
    "Ishaan", "Rohan", "Ananya", "Diya", "Priya", "Saanvi", "Aadhya", "Kiara",
    "Meera", "Isha", "Neha", "Riya", "Karthik", "Suresh", "Rajesh", "Anil",
    "Sunita", "Deepa", "Pooja", "Nikhil", "Varun", "Sanjay", "Lakshmi", "Divya",
    "Manoj", "Ramesh", "Kavya", "Shreya", "Amit", "Vikram", "Nisha", "Tanvi",
]

LAST_NAMES = [
    "Sharma", "Verma", "Iyer", "Nair", "Reddy", "Gupta", "Mehta", "Patel",
    "Kumar", "Singh", "Rao", "Joshi", "Desai", "Kapoor", "Malhotra", "Chatterjee",
    "Bose", "Menon", "Pillai", "Agarwal", "Bhatt", "Chauhan", "Trivedi", "Nagar",
]

COMPANY_NAMES = [
    "Nimbus Retail Pvt Ltd", "Vertex Logistics", "BlueWave Textiles",
    "Orbit Manufacturing Co", "Zenith Traders", "Sundar Agro Exports",
    "Prakash Steel Industries", "Falcon Freight Solutions", "Meridian Foods",
    "Ashoka Building Materials", "Lotus Pharma Distributors", "Crescent Hardware",
]

EMAIL_DOMAINS = ["gmail.com", "outlook.com", "yahoo.in", "rediffmail.com", "business.co.in"]

CITIES = ["Bengaluru", "Mumbai", "Delhi", "Hyderabad", "Chennai", "Pune", "Kolkata",
          "Ahmedabad", "Jaipur", "Kochi", "Noida", "Gurugram"]

# ----------------------------------------------------------------------------
# Failure-type specific reference data
# ----------------------------------------------------------------------------

PAYMENT_DEGRADATION_ERRORS = [
    ("GATEWAY_TIMEOUT", "Payment gateway did not respond within the expected window during authorization."),
    ("UPI_NPCI_UNAVAILABLE", "NPCI switch was unreachable, causing the UPI collect request to fail silently."),
    ("BANK_SERVER_TIMEOUT", "Issuing bank's authorization server timed out mid-transaction."),
    ("ACQUIRER_LATENCY_BREACH", "Acquirer response exceeded SLA latency threshold, transaction auto-voided."),
    ("UPI_PSP_HANDSHAKE_FAILED", "UPI PSP handshake failed due to intermediary routing delay."),
]

CHECKOUT_DROPOFF_ERRORS = [
    ("OTP_ABANDONED", "Customer navigated away from the checkout page during OTP entry."),
    ("3DS_TIMEOUT", "3D Secure authentication page timed out before customer completed verification."),
    ("OTP_NOT_RECEIVED", "Customer exited checkout after reporting the OTP was not received."),
    ("3DS_ABANDONED", "Customer closed the 3DS challenge window without completing authentication."),
    ("SESSION_EXPIRED_AT_OTP", "Checkout session expired while awaiting OTP confirmation."),
]

SUBSCRIPTION_MANDATE_ERRORS = [
    ("MANDATE_AUTH_DECLINED", "Recurring e-mandate auto-debit was declined by the issuing bank at authorization."),
    ("MANDATE_INSUFFICIENT_BALANCE", "Scheduled auto-debit failed due to insufficient balance in linked account."),
    ("MANDATE_EXPIRED", "UPI Autopay / NACH mandate has expired and requires customer re-registration."),
    ("MANDATE_FREQUENCY_MISMATCH", "Auto-debit attempt fell outside the mandate's registered debit frequency window."),
    ("MANDATE_BANK_REJECTED", "Bank rejected the recurring mandate execution during the debit cycle."),
]

B2B_RECEIVABLE_ERRORS = [
    ("INVOICE_OVERDUE_15D", "Invoice has remained unpaid for more than 15 days past the due date."),
    ("INVOICE_OVERDUE_30D", "Invoice has remained unpaid for more than 30 days past the due date."),
    ("PO_MISMATCH_HOLD", "Payment held by client's AP team pending purchase-order reconciliation."),
    ("INVOICE_DISPUTE_PENDING", "Client has flagged a partial dispute on the invoice line items."),
    ("PAYMENT_TERMS_LAPSED", "Net-30 payment terms have lapsed without remittance from the client."),
]

HARD_DECLINE_ERRORS = [
    ("INSUFFICIENT_FUNDS", "Card issuer declined the transaction due to insufficient funds in the account."),
    ("CARD_BLOCKED", "Card has been blocked by the issuing bank and cannot authorize new transactions."),
    ("STOLEN_CARD", "Issuing bank flagged the card as reported lost or stolen; transaction hard-declined."),
    ("CUSTOMER_OPT_OUT", "Customer has explicitly opted out of further payment retry communications."),
]

FAILURE_TYPES = [
    "PAYMENT_DEGRADATION",
    "CHECKOUT_DROPOFF",
    "SUBSCRIPTION_MANDATE_FAIL",
    "B2B_RECEIVABLE_OVERDUE",
    "HARD_DECLINE",
]

# Exact distribution across the 5 required categories (sums to 50).
DISTRIBUTION = {
    "PAYMENT_DEGRADATION": 10,
    "CHECKOUT_DROPOFF": 10,
    "SUBSCRIPTION_MANDATE_FAIL": 10,
    "B2B_RECEIVABLE_OVERDUE": 10,
    "HARD_DECLINE": 10,
}

ERROR_MAP = {
    "PAYMENT_DEGRADATION": PAYMENT_DEGRADATION_ERRORS,
    "CHECKOUT_DROPOFF": CHECKOUT_DROPOFF_ERRORS,
    "SUBSCRIPTION_MANDATE_FAIL": SUBSCRIPTION_MANDATE_ERRORS,
    "B2B_RECEIVABLE_OVERDUE": B2B_RECEIVABLE_ERRORS,
    "HARD_DECLINE": HARD_DECLINE_ERRORS,
}

# Amount ranges per category (in INR), tuned to be realistic per scenario type.
AMOUNT_RANGES = {
    "PAYMENT_DEGRADATION": (499.0, 15000.0),
    "CHECKOUT_DROPOFF": (299.0, 9999.0),
    "SUBSCRIPTION_MANDATE_FAIL": (199.0, 4999.0),
    "B2B_RECEIVABLE_OVERDUE": (25001.0, 850000.0),   # must always exceed ₹25,000
    "HARD_DECLINE": (399.0, 25000.0),
}


def _random_phone() -> str:
    """Generate a realistic +91 Indian mobile number."""
    first_digit = random.choice(["6", "7", "8", "9"])
    rest = "".join(str(random.randint(0, 9)) for _ in range(9))
    return f"+91{first_digit}{rest}"


def _random_person_name() -> str:
    return f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"


def _random_email(name: str, is_company: bool) -> str:
    handle = name.lower().replace(" ", ".").replace(",", "")
    handle = "".join(ch for ch in handle if ch.isalnum() or ch == ".")
    if is_company:
        return f"accounts.{handle}@{random.choice(EMAIL_DOMAINS)}"
    suffix = random.randint(1, 999)
    return f"{handle}{suffix}@{random.choice(EMAIL_DOMAINS)}"


def _random_amount(failure_type: str) -> float:
    lo, hi = AMOUNT_RANGES[failure_type]
    value = random.uniform(lo, hi)
    return round(value, 2)


def _customer_tier_for(failure_type: str) -> str:
    # B2B receivables are inherently enterprise-side scenarios.
    if failure_type == "B2B_RECEIVABLE_OVERDUE":
        return "enterprise"
    # Otherwise, skew mostly standard with some enterprise mixed in.
    return random.choices(["standard", "enterprise"], weights=[0.75, 0.25], k=1)[0]


def _retry_count_for(failure_type: str, error_code: str) -> int:
    if failure_type == "HARD_DECLINE" and error_code in ("STOLEN_CARD", "CARD_BLOCKED", "CUSTOMER_OPT_OUT"):
        # Hard, non-retryable failures should not show high retry counts.
        return random.randint(0, 1)
    if failure_type == "B2B_RECEIVABLE_OVERDUE":
        return random.randint(1, 4)
    return random.randint(0, 4)


def _opt_out_for(failure_type: str, error_code: str) -> bool:
    if error_code == "CUSTOMER_OPT_OUT":
        return True
    # Small chance of opt-out unrelated to the primary error, to add realism.
    return random.random() < 0.05


def _build_record(index: int, failure_type: str) -> dict:
    record_id = f"REC_{index:03d}"
    order_id = f"order_test_{1000 + index}"

    is_b2b = failure_type == "B2B_RECEIVABLE_OVERDUE"
    if is_b2b:
        display_name = random.choice(COMPANY_NAMES)
        contact_person = _random_person_name()
        customer_name = f"{contact_person} ({display_name})"
        customer_email = _random_email(display_name, is_company=True)
    else:
        customer_name = _random_person_name()
        customer_email = _random_email(customer_name, is_company=False)

    customer_phone = _random_phone()
    amount_inr = _random_amount(failure_type)

    error_code, error_description = random.choice(ERROR_MAP[failure_type])
    retry_count = _retry_count_for(failure_type, error_code)
    customer_tier = _customer_tier_for(failure_type)
    opt_out = _opt_out_for(failure_type, error_code)

    return {
        "record_id": record_id,
        "order_id": order_id,
        "customer_name": customer_name,
        "customer_email": customer_email,
        "customer_phone": customer_phone,
        "amount_inr": amount_inr,
        "failure_type": failure_type,
        "error_code": error_code,
        "error_description": error_description,
        "retry_count": retry_count,
        "customer_tier": customer_tier,
        "opt_out": opt_out,
    }


def generate_dataset() -> list:
    records = []
    index = 1

    # Expand distribution into a flat list of failure types, then shuffle
    # so the final JSON isn't grouped block-by-block.
    failure_type_sequence = []
    for failure_type in FAILURE_TYPES:
        failure_type_sequence.extend([failure_type] * DISTRIBUTION[failure_type])

    assert len(failure_type_sequence) == 50, "Distribution must sum to exactly 50 records."

    random.shuffle(failure_type_sequence)

    for failure_type in failure_type_sequence:
        records.append(_build_record(index, failure_type))
        index += 1

    return records


def main():
    dataset = generate_dataset()

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(dataset, f, indent=2, ensure_ascii=False)

    # Summary printout for sanity-checking the generated batch.
    counts = {ft: 0 for ft in FAILURE_TYPES}
    for rec in dataset:
        counts[rec["failure_type"]] += 1

    print(f"Generated {len(dataset)} records -> {OUTPUT_PATH}")
    for ft, count in counts.items():
        print(f"  {ft}: {count}")


if __name__ == "__main__":
    main()