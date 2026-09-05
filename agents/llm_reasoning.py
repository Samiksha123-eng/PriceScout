"""
llm_reasoning.py
------------------
The ONLY place an LLM is used in this project.

Every number and the verdict itself (BUY_NOW / GOOD_DEAL / WAIT) already
came from deterministic Python code (analysis_agent.py + decision_agent.py).
This module's job is narrow: turn those facts into a short, plain-English
explanation a human can read at a glance. It never changes the verdict —
if the LLM call fails or no API key is configured, a template-based
fallback produces an equally accurate (if less fluent) explanation, so the
agent keeps working offline.
"""

import os

SYSTEM_PROMPT = (
    "You are the explanation module of PriceScout, a price-monitoring agent. "
    "You are given a decision that has ALREADY been made by deterministic code. "
    "Write a 1-2 sentence, plain-English explanation of why that decision makes "
    "sense, using only the numbers provided. Do not contradict or change the "
    "verdict. Do not invent numbers. No markdown, no preamble."
)


def _facts_prompt(product_name: str, decision: dict) -> str:
    return (
        f"Product: {product_name}\n"
        f"Verdict: {decision['verdict']}\n"
        f"Current price: {decision['current_price']}\n"
        f"Target price: {decision['target_price']}\n"
        f"Historical average price: {decision['avg_price']}\n"
        f"Current vs. average: {decision['vs_avg_pct']}%\n"
        f"Change since last check: {decision['price_change']} "
        f"({decision['price_change_pct']}%), trend is {decision['trend']}.\n\n"
        "Explain this verdict in 1-2 short sentences for a shopper looking at a dashboard."
    )


def _fallback_reasoning(product_name: str, decision: dict) -> str:
    """Deterministic, template-based explanation — used when no LLM is available."""
    v = decision["verdict"]
    if v == "BUY_NOW":
        return (
            f"{product_name} is at {decision['current_price']}, at or below your target of "
            f"{decision['target_price']}. That's the price you said you wanted — this is the moment to buy."
        )
    if v == "GOOD_DEAL":
        return (
            f"{product_name} is at {decision['current_price']}, which is "
            f"{abs(decision['vs_avg_pct'])}% below its historical average of {decision['avg_price']}. "
            f"It hasn't hit your target of {decision['target_price']} yet, but this is a real discount."
        )
    return (
        f"{product_name} is at {decision['current_price']}, close to or above its historical average of "
        f"{decision['avg_price']} and still above your target of {decision['target_price']}. "
        f"Worth waiting for a better window."
    )


def explain_decision(product_name: str, decision: dict) -> str:
    """
    Returns a short natural-language explanation of `decision`.
    Tries the Anthropic API first; falls back to a deterministic template
    if no API key is set or the call fails for any reason.
    """
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return _fallback_reasoning(product_name, decision)

    try:
        import anthropic

        client = anthropic.Anthropic(api_key=api_key)
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=120,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": _facts_prompt(product_name, decision)}],
        )
        text_blocks = [b.text for b in response.content if getattr(b, "type", None) == "text"]
        text = " ".join(text_blocks).strip()
        return text or _fallback_reasoning(product_name, decision)
    except Exception:
        # Any failure (network, auth, quota, bad response) — never break the
        # agent's workflow just because the explanation layer is unavailable.
        return _fallback_reasoning(product_name, decision)
