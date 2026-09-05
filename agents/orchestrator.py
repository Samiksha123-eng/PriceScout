"""
orchestrator.py
-----------------
The Orchestrator wires the five agents together into one workflow:

    Observe  -> ProductPriceAgent.get_current_price()
    Store    -> database.add_price()
    Analyze  -> AnalysisAgent.analyze()
    Decide   -> DecisionAgent.decide()
    Explain  -> llm_reasoning.explain_decision()   (LLM, explanation only)
    Act      -> NotificationAgent.notify()
    Store    -> database.add_decision()
    Monitor  -> repeat, on a timer, for every active product

This is the only module that knows about ALL the agents; each agent module
only knows about its own job. That separation is what makes this "agentic"
rather than one big function: every step is a small, independently testable
unit with one responsibility.
"""

import threading
import time

import database as db
from agents.price_agent import ProductPriceAgent
from agents.analysis_agent import AnalysisAgent
from agents.decision_agent import DecisionAgent
from agents.notification_agent import NotificationAgent
from agents.llm_reasoning import explain_decision

MONITOR_INTERVAL_SECONDS = 20


class Orchestrator:
    def __init__(self):
        self.price_agent = ProductPriceAgent()
        self.analysis_agent = AnalysisAgent()
        self.decision_agent = DecisionAgent()
        self.notification_agent = NotificationAgent()

        self._monitor_thread = None
        self._stop_event = threading.Event()
        self._lock = threading.Lock()

    # ---------------------------------------------------------- one product
    def run_cycle_for_product(self, product: dict) -> dict:
        """
        Runs one full Observe -> Analyze -> Decide -> Explain -> Act cycle
        for a single product and persists everything. Returns a summary
        dict the API/dashboard can render directly.
        """
        history = db.get_price_history(product["id"])
        history_prices = [h["price"] for h in history]
        previous_price = history_prices[-1] if history_prices else product["seed_price"]

        # OBSERVE
        current_price = self.price_agent.get_current_price(product["name"], previous_price)
        # STORE (raw observation)
        db.add_price(product["id"], current_price)

        # ANALYZE
        analysis = self.analysis_agent.analyze(history_prices, current_price)

        # DECIDE
        decision = self.decision_agent.decide(current_price, product["target_price"], analysis)

        # EXPLAIN (LLM, explanation-only — never changes the verdict)
        reasoning = explain_decision(product["name"], decision)

        # STORE (decision)
        db.add_decision(
            product["id"],
            current_price,
            analysis["avg_price"],
            analysis["price_change"],
            decision["verdict"],
            reasoning,
        )

        # ACT
        alert = self.notification_agent.notify(product, decision, reasoning)

        return {
            "product_id": product["id"],
            "product_name": product["name"],
            "current_price": current_price,
            "target_price": product["target_price"],
            "analysis": analysis,
            "decision": decision,
            "reasoning": reasoning,
            "alert": alert,
        }

    def run_cycle_by_id(self, product_id: int) -> dict:
        product = db.get_product(product_id)
        if not product:
            raise ValueError(f"No product with id {product_id}")
        return self.run_cycle_for_product(product)

    # --------------------------------------------------------- all products
    def run_cycle_all(self):
        results = []
        for product in db.list_products(active_only=True):
            with self._lock:
                results.append(self.run_cycle_for_product(product))
        return results

    # ------------------------------------------------------- auto-monitor
    def start_monitoring(self, interval_seconds: int = MONITOR_INTERVAL_SECONDS):
        """Starts a background thread that repeats the workflow for every
        active product on a fixed interval — the 'Monitor Again' step."""
        if self._monitor_thread and self._monitor_thread.is_alive():
            return  # already running

        self._stop_event.clear()

        def loop():
            while not self._stop_event.wait(interval_seconds):
                try:
                    self.run_cycle_all()
                except Exception as exc:  # keep the monitor alive on any error
                    print(f"[orchestrator] monitor cycle failed: {exc}")

        self._monitor_thread = threading.Thread(target=loop, daemon=True)
        self._monitor_thread.start()

    def stop_monitoring(self):
        self._stop_event.set()


# a single shared orchestrator instance for the whole app
orchestrator = Orchestrator()
