"""
price_agent.py
---------------
Product/Price Agent.

Responsible for ONE thing: "what does this product cost right now?"

Today that means a mock price source, so PriceScout works without depending
on Amazon / Flipkart / any real marketplace. The mock source is a seeded
random walk: each product gets a deterministic seed (from its name), so the
same product always starts at the same price and always moves the same way
tick-by-tick — this makes the agent's behaviour reproducible and testable,
while still looking like a real, noisy market.

Swapping this out for a real scraper/API later only means replacing
`get_current_price()` — nothing else in the system needs to change.
"""

import hashlib
import random


class ProductPriceAgent:
    """Observes the current price of a product from a data source."""

    # how much the price can move, as a fraction of itself, per tick
    VOLATILITY = 0.045
    # gentle downward drift so "GOOD DEAL" / "BUY NOW" states are reachable
    # in a short demo session, not just theoretically
    DRIFT = -0.004

    def __init__(self):
        # tick counters per product name, so repeated calls advance the walk
        self._ticks = {}

    @staticmethod
    def seed_price(product_name: str) -> float:
        """Deterministic starting price derived from the product's name."""
        digest = hashlib.sha256(product_name.strip().lower().encode()).hexdigest()
        # map the hash to a "realistic" price band: 500 - 50,000
        value = int(digest[:8], 16) / 0xFFFFFFFF
        return round(500 + value * 49500, 2)

    def get_current_price(self, product_name: str, previous_price: float) -> float:
        """
        Observe the next price for a product.

        Uses a per-product seeded RNG so results are reproducible across a
        run for the same product + tick number, while still behaving like a
        noisy, drifting market.
        """
        tick = self._ticks.get(product_name, 0)
        self._ticks[product_name] = tick + 1

        seed_material = f"{product_name.strip().lower()}::{tick}"
        rng = random.Random(seed_material)

        # occasional bigger dip to simulate a real "deal" event
        if rng.random() < 0.12:
            shock = -abs(rng.gauss(0, self.VOLATILITY * 2.2))
        else:
            shock = rng.gauss(self.DRIFT, self.VOLATILITY)

        new_price = previous_price * (1 + shock)
        new_price = max(new_price, previous_price * 0.5)  # floor: no free-fall
        return round(new_price, 2)
