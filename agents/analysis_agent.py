"""
analysis_agent.py
------------------
Analysis Agent.

Pure, deterministic arithmetic over price history — no randomness, no LLM.
Given a list of past prices and the current price, it computes the facts
the Decision Agent needs to make a call.
"""

from statistics import mean


class AnalysisAgent:
    def analyze(self, history_prices: list, current_price: float) -> dict:
        """
        history_prices: chronological list of past observed prices,
                         NOT including current_price.
        Returns a dict of computed facts.
        """
        if history_prices:
            avg_price = round(mean(history_prices), 2)
            previous_price = history_prices[-1]
        else:
            avg_price = current_price
            previous_price = current_price

        price_change = round(current_price - previous_price, 2)
        price_change_pct = (
            round((price_change / previous_price) * 100, 2) if previous_price else 0.0
        )
        vs_avg_pct = (
            round(((current_price - avg_price) / avg_price) * 100, 2) if avg_price else 0.0
        )

        if price_change < 0:
            trend = "falling"
        elif price_change > 0:
            trend = "rising"
        else:
            trend = "flat"

        return {
            "avg_price": avg_price,
            "previous_price": previous_price,
            "price_change": price_change,
            "price_change_pct": price_change_pct,
            "vs_avg_pct": vs_avg_pct,
            "trend": trend,
            "lowest_price": round(min(history_prices + [current_price]), 2),
            "highest_price": round(max(history_prices + [current_price]), 2),
            "samples": len(history_prices) + 1,
        }
