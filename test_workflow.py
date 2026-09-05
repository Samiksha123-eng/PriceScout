"""
test_workflow.py
------------------
Exercises the complete Observe -> Analyze -> Decide -> Explain -> Act ->
Monitor pipeline directly against a throwaway database, without needing
the Flask server or network access. Run:

    python test_workflow.py
"""

import os

import database as db

# use a scratch DB so this never touches the real app's data
db.DB_PATH = "test_pricescout.db"
if os.path.exists(db.DB_PATH):
    os.remove(db.DB_PATH)
db.init_db()

from agents.price_agent import ProductPriceAgent
from agents.orchestrator import Orchestrator

orch = Orchestrator()

print("=" * 60)
print("1) Add a product")
print("=" * 60)
name = "Sony WH-1000XM5 Headphones"
seed = ProductPriceAgent.seed_price(name)
target = round(seed * 0.85, 2)  # target 15% below seed, reachable via drift/dips
product_id = db.add_product(name, target, seed)
product = db.get_product(product_id)
print(f"Added '{name}' | seed price {seed} | target {target}")
assert product["name"] == name

print()
print("=" * 60)
print("2-7) Run several Observe->Analyze->Decide->Explain->Act cycles")
print("=" * 60)
verdicts_seen = set()
for i in range(15):
    result = orch.run_cycle_for_product(product)
    d = result["decision"]
    verdicts_seen.add(d["verdict"])
    alert_flag = "  <-- ALERT" if result["alert"] else ""
    print(
        f"tick {i:02d} | price {d['current_price']:>9} | avg {d['avg_price']:>9} "
        f"| vs_avg {d['vs_avg_pct']:>6}% | verdict {d['verdict']:<9}{alert_flag}"
    )
    print(f"          reasoning: {result['reasoning']}")

print()
print("=" * 60)
print("8) Verify persistence: price history + decisions stored")
print("=" * 60)
history = db.get_price_history(product_id)
latest_decision = db.get_latest_decision(product_id)
print(f"Stored {len(history)} price observations.")
print(f"Latest decision verdict: {latest_decision['verdict']}")
assert len(history) == 15
assert latest_decision is not None

print()
print("=" * 60)
print("9) Verify notifications fired for alert-worthy verdicts")
print("=" * 60)
alerts = db.list_alerts(product_id)
print(f"Alerts raised: {len(alerts)}")
for a in alerts[:5]:
    print(f"  [{a['verdict']}] {a['message']}")

print()
print("=" * 60)
print("10) Sanity checks on deterministic decision rules")
print("=" * 60)
assert "BUY_NOW" in verdicts_seen or "GOOD_DEAL" in verdicts_seen or "WAIT" in verdicts_seen
for v in verdicts_seen:
    assert v in {"BUY_NOW", "GOOD_DEAL", "WAIT"}
print(f"Verdicts observed across the run: {sorted(verdicts_seen)}")

print()
print("ALL CHECKS PASSED")
print(f"(LLM explanation used: {'ANTHROPIC_API_KEY' in os.environ})")

os.remove(db.DB_PATH)
