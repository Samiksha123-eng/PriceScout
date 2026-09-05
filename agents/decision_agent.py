"""
decision_agent.py
------------------
Decision Agent.

Turns the Analysis Agent's facts into one of three verdicts. This is plain,
deterministic business logic — the same inputs always give the same
verdict. The LLM is never involved in the decision itself, only in
explaining it afterwards (see llm_reasoning.py).

Rules (checked in order):
    1. BUY_NOW    current_price <= target_price
    2. GOOD_DEAL  current_price is at least GOOD_DEAL_THRESHOLD below the
                  historical average (a real discount vs. what this product
                  usually costs, even if it hasn't hit the target yet)
    3. WAIT       everything else — price is at or above what's normal
"""

GOOD_DEAL_THRESHOLD_PCT = -5.0  # current must be >=5% below avg_price


class DecisionAgent:
    def decide(self, current_price: float, target_price: float, analysis: dict) -> dict:
        avg_price = analysis["avg_price"]
        vs_avg_pct = analysis["vs_avg_pct"]

        if current_price <= target_price:
            verdict = "BUY_NOW"
        elif vs_avg_pct <= GOOD_DEAL_THRESHOLD_PCT:
            verdict = "GOOD_DEAL"
        else:
            verdict = "WAIT"

        return {
            "verdict": verdict,
            "current_price": current_price,
            "target_price": target_price,
            "avg_price": avg_price,
            "vs_avg_pct": vs_avg_pct,
            "price_change": analysis["price_change"],
            "price_change_pct": analysis["price_change_pct"],
            "trend": analysis["trend"],
        }
