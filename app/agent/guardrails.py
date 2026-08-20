"""
RazorRecover AI — Deterministic Guardrails & Stopping Rules
Track 03: AI Revenue Recovery — Razorpay AI Buildathon

This module contains ZERO LLM calls and ZERO hallucination surface area.
Every decision here is a pure, deterministic function of its inputs so that
the recovery agent's behaviour is fully auditable, reproducible, and safe
to run unattended in production. All thresholds are hard-coded constants —
no runtime configuration can silently loosen them.

These functions are the final authority on:
  1. Whether the agent must STOP attempting recovery on a record.
  2. Whether a record must be ESCALATED to a human operator.
  3. How much discount (if any) the agent is permitted to offer.
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Hard Constants
# ---------------------------------------------------------------------------
# These bounds are intentionally hard-coded (not env-configurable) so that no
# prompt, request payload, or misconfiguration can override safety limits.

MAX_ALLOWED_RETRIES: int = 2
HIGH_VALUE_THRESHOLD_INR: float = 25000.0
MAX_DISCOUNT_PERCENTAGE: float = 10.0
MAX_ABSOLUTE_DISCOUNT_INR: float = 500.0
MIN_ORDER_AMOUNT_FOR_DISCOUNT_INR: float = 500.0

HARD_STOP_ERROR_CODES: set[str] = {
    "INSUFFICIENT_FUNDS",
    "CARD_BLOCKED",
    "STOLEN_CARD",
    "CUSTOMER_OPT_OUT",
    "FRAUD_SUSPECTED",
}


# ---------------------------------------------------------------------------
# 1. Stopping Rules
# ---------------------------------------------------------------------------
def evaluate_stopping_rules(
    error_code: str,
    retry_count: int,
    opt_out: bool = False,
) -> tuple[bool, str]:
    """
    Determine whether the recovery agent must HALT further action on a record.

    A hard stop is triggered by any ONE of the following conditions:
      - The error code belongs to HARD_STOP_ERROR_CODES (non-recoverable /
        compliance-sensitive failures such as fraud, blocked or stolen
        cards, or a compliance-mandated opt-out signal).
      - The customer has explicitly opted out of further contact
        (opt_out=True), regardless of error code.
      - The record has already been retried MAX_ALLOWED_RETRIES times or
        more, to prevent unbounded retry loops.

    Args:
        error_code: The failure/error code associated with the transaction
            (e.g. "GATEWAY_TIMEOUT", "STOLEN_CARD").
        retry_count: Number of recovery attempts already made on this record.
        opt_out: Whether the customer has opted out of further contact.

    Returns:
        A tuple of (should_stop, reason):
            should_stop: True if the agent must halt recovery for this record.
            reason: Human-readable, audit-log-ready explanation of the
                decision — always populated, even when should_stop is False.
    """
    normalized_code = (error_code or "").strip().upper()

    if opt_out:
        return (
            True,
            "STOP: Customer has opted out of further recovery communications. "
            "Continuing would violate consent and compliance policy.",
        )

    if normalized_code in HARD_STOP_ERROR_CODES:
        return (
            True,
            f"STOP: Error code '{normalized_code}' is classified as a hard-stop "
            "condition (non-recoverable or compliance-sensitive). No further "
            "automated recovery attempts are permitted.",
        )

    if retry_count >= MAX_ALLOWED_RETRIES:
        return (
            True,
            f"STOP: Retry count ({retry_count}) has reached or exceeded the "
            f"maximum allowed retries ({MAX_ALLOWED_RETRIES}). Further automated "
            "attempts are blocked to prevent customer fatigue and abuse.",
        )

    return (
        False,
        f"CONTINUE: No stopping condition met (error_code='{normalized_code}', "
        f"retry_count={retry_count}, opt_out={opt_out}). Recovery may proceed.",
    )


# ---------------------------------------------------------------------------
# 2. Escalation Rules
# ---------------------------------------------------------------------------
def evaluate_escalation_rules(
    amount: float,
    retry_count: int,
    customer_tier: str,
) -> tuple[bool, str]:
    """
    Determine whether a record must be escalated to a human operator instead
    of (or in addition to) continuing automated recovery.

    Escalation is triggered by any ONE of the following conditions:
      - The transaction amount is at or above HIGH_VALUE_THRESHOLD_INR,
        since high-value recoveries carry outsized financial/relationship
        risk if mishandled by automation alone.
      - The customer is an "enterprise" tier customer AND has already
        failed at least once (retry_count >= 1) — enterprise relationships
        warrant human judgment after the very first failure.

    Args:
        amount: Transaction / invoice amount in INR.
        retry_count: Number of recovery attempts already made on this record.
        customer_tier: Customer segment, expected values "standard" or
            "enterprise" (case-insensitive).

    Returns:
        A tuple of (should_escalate, reason):
            should_escalate: True if the record must be flagged
                ESCALATED_TO_HUMAN.
            reason: Human-readable, audit-log-ready explanation of the
                decision — always populated, even when should_escalate is False.
    """
    normalized_tier = (customer_tier or "").strip().lower()

    if amount >= HIGH_VALUE_THRESHOLD_INR:
        return (
            True,
            f"ESCALATED_TO_HUMAN: Transaction amount (₹{amount:,.2f}) meets or "
            f"exceeds the high-value threshold (₹{HIGH_VALUE_THRESHOLD_INR:,.2f}). "
            "High-value recoveries require human oversight.",
        )

    if normalized_tier == "enterprise" and retry_count >= 1:
        return (
            True,
            f"ESCALATED_TO_HUMAN: Enterprise-tier customer has already failed "
            f"{retry_count} time(s). Enterprise accounts are escalated after "
            "the first failure to protect the relationship.",
        )

    return (
        False,
        f"NO_ESCALATION: Amount (₹{amount:,.2f}) is below the high-value "
        f"threshold and customer_tier='{normalized_tier}' with retry_count="
        f"{retry_count} does not meet enterprise escalation criteria. "
        "Automated recovery may continue.",
    )


# ---------------------------------------------------------------------------
# 3. Discount Guardrail
# ---------------------------------------------------------------------------
def apply_discount_guardrail(
    order_amount: float,
    proposed_discount_pct: float,
) -> tuple[float, float, str]:
    """
    Deterministically bound any discount the agent proposes to offer as a
    recovery incentive, then compute the resulting final payable amount.

    Rules enforced, in order:
      1. Orders below MIN_ORDER_AMOUNT_FOR_DISCOUNT_INR (₹500) are NOT
         eligible for any discount at all — the discount is rejected
         outright (bounded_pct = 0.0).
      2. The proposed percentage is clamped to the range
         [0.0, MAX_DISCOUNT_PERCENTAGE] (i.e. never negative, never above 10%).
      3. The resulting discount amount in INR is further capped at
         MAX_ABSOLUTE_DISCOUNT_INR (₹500). If the percentage-based discount
         would exceed this absolute cap, the effective percentage is
         reduced so the discount amount equals exactly the absolute cap.

    Args:
        order_amount: The original order amount in INR.
        proposed_discount_pct: The discount percentage the agent wants to
            offer (e.g. 15.0 for 15%). May be out of bounds; will be
            clamped, never trusted as-is.

    Returns:
        A tuple of (bounded_pct, final_amount, notes):
            bounded_pct: The final, guardrail-enforced discount percentage
                actually applied (0.0 if rejected).
            final_amount: The order_amount after the bounded discount has
                been subtracted (equals order_amount if no discount applies).
            notes: Human-readable, audit-log-ready explanation of every
                adjustment made.
    """
    notes: list[str] = []

    # Rule 1: minimum order value eligibility check.
    if order_amount < MIN_ORDER_AMOUNT_FOR_DISCOUNT_INR:
        notes.append(
            f"REJECTED: Order amount (₹{order_amount:,.2f}) is below the minimum "
            f"eligible amount for any discount (₹{MIN_ORDER_AMOUNT_FOR_DISCOUNT_INR:,.2f})."
        )
        return 0.0, round(order_amount, 2), " ".join(notes)

    # Rule 2: clamp percentage to [0, MAX_DISCOUNT_PERCENTAGE].
    original_pct = proposed_discount_pct
    clamped_pct = max(0.0, min(proposed_discount_pct, MAX_DISCOUNT_PERCENTAGE))
    if clamped_pct != original_pct:
        notes.append(
            f"Proposed discount of {original_pct:.2f}% was clamped to "
            f"{clamped_pct:.2f}% (allowed range: 0%–{MAX_DISCOUNT_PERCENTAGE:.0f}%)."
        )

    # Rule 3: cap the resulting absolute discount amount.
    discount_amount = round(order_amount * (clamped_pct / 100.0), 2)
    if discount_amount > MAX_ABSOLUTE_DISCOUNT_INR:
        capped_discount_amount = MAX_ABSOLUTE_DISCOUNT_INR
        # Recompute the effective percentage that yields exactly the cap.
        bounded_pct = round((capped_discount_amount / order_amount) * 100.0, 4)
        notes.append(
            f"Discount amount of ₹{discount_amount:,.2f} exceeded the absolute cap "
            f"of ₹{MAX_ABSOLUTE_DISCOUNT_INR:,.2f}; effective discount reduced to "
            f"{bounded_pct:.2f}% (₹{capped_discount_amount:,.2f})."
        )
        final_discount_amount = capped_discount_amount
        bounded_pct_final = bounded_pct
    else:
        final_discount_amount = discount_amount
        bounded_pct_final = clamped_pct

    final_amount = round(order_amount - final_discount_amount, 2)

    if not notes:
        notes.append(
            f"APPROVED: Discount of {bounded_pct_final:.2f}% "
            f"(₹{final_discount_amount:,.2f}) applied without adjustment."
        )
    else:
        notes.append(
            f"Final applied discount: {bounded_pct_final:.2f}% "
            f"(₹{final_discount_amount:,.2f})."
        )

    return bounded_pct_final, final_amount, " ".join(notes)


# ---------------------------------------------------------------------------
# Self-test / manual sanity check (safe to run standalone: `python guardrails.py`)
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    print("=== evaluate_stopping_rules ===")
    print(evaluate_stopping_rules("STOLEN_CARD", 0, False))
    print(evaluate_stopping_rules("GATEWAY_TIMEOUT", 2, False))
    print(evaluate_stopping_rules("GATEWAY_TIMEOUT", 0, True))
    print(evaluate_stopping_rules("GATEWAY_TIMEOUT", 1, False))

    print("\n=== evaluate_escalation_rules ===")
    print(evaluate_escalation_rules(30000.0, 0, "standard"))
    print(evaluate_escalation_rules(1000.0, 1, "enterprise"))
    print(evaluate_escalation_rules(1000.0, 0, "standard"))

    print("\n=== apply_discount_guardrail ===")
    print(apply_discount_guardrail(300.0, 10.0))     # below minimum -> rejected
    print(apply_discount_guardrail(1000.0, 15.0))    # pct clamped to 10%
    print(apply_discount_guardrail(10000.0, 10.0))   # pct would give ₹1000 -> capped to ₹500
    print(apply_discount_guardrail(2000.0, 5.0))     # within bounds -> approved as-is