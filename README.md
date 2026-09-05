# PriceScout — Autonomous Price Monitoring & Alert Agent

A small multi-agent system that watches product prices, decides whether
now is a good time to buy, explains its reasoning, and alerts you — on its
own, on a timer.

```
User → Add Product → Get Current Price → Store Price → Analyze Price
     → Make Decision → Alert User → Monitor Again (repeat)
```

## Why this counts as an "agent," not just a script

Each step above is owned by a small, independently testable module with
one job. The **Orchestrator** is the only thing that knows about all of
them, and it runs the loop continuously in a background thread:

| Step     | Module                       | Responsibility                                            |
|----------|-------------------------------|-------------------------------------------------------------|
| Observe  | `agents/price_agent.py`       | Get the current price (mock market data source)             |
| Store    | `database.py`                 | Persist every observation to SQLite                          |
| Analyze  | `agents/analysis_agent.py`    | Deterministic historical average / price-change math         |
| Decide   | `agents/decision_agent.py`    | Deterministic BUY_NOW / GOOD_DEAL / WAIT rules                |
| Explain  | `agents/llm_reasoning.py`     | **The only LLM call** — turns the decision into plain English |
| Act      | `agents/notification_agent.py`| Raises an alert for BUY_NOW / GOOD_DEAL                       |
| Monitor  | `agents/orchestrator.py`      | Repeats the whole cycle for every product, every 20s          |

The LLM never decides anything — it only explains a decision that
deterministic Python already made. If there's no `ANTHROPIC_API_KEY` set,
or the API call fails for any reason, a template-based fallback keeps the
agent fully functional offline.

## Decision rules (deterministic)

1. **BUY_NOW** — current price ≤ target price
2. **GOOD_DEAL** — current price is ≥5% below the historical average (a real
   discount, even before it hits your target)
3. **WAIT** — anything else (price at or above what's normal for this product)

## Project structure

```
pricescout/
├── app.py                    Flask server (routes only — no business logic)
├── database.py                SQLite schema + CRUD
├── requirements.txt
├── test_workflow.py            End-to-end test of the full pipeline
├── agents/
│   ├── price_agent.py          Product/Price Agent (mock data source)
│   ├── analysis_agent.py       Analysis Agent
│   ├── decision_agent.py       Decision Agent
│   ├── llm_reasoning.py        LLM explanation (+ offline fallback)
│   ├── notification_agent.py   Notification Agent
│   └── orchestrator.py         Orchestrator + background monitor loop
├── templates/index.html        Dashboard shell
└── static/
    ├── style.css                Dashboard styling
    └── dashboard.js              Dashboard logic (calls the REST API)
```

## Running it

```bash
cd pricescout
pip install -r requirements.txt

# optional — enables real LLM explanations instead of the template fallback
export ANTHROPIC_API_KEY=sk-ant-...

python app.py
```

Open **http://localhost:5000**.

- **Add product**: enter a name and target price. The agent immediately
  runs one full cycle (observe → analyze → decide → explain → act) so you
  see a result right away.
- **Check price now**: manually triggers another cycle for the selected
  product.
- **Automatic monitoring**: a background thread re-runs the cycle for
  every active product every 20 seconds — no user action needed. The
  dashboard polls the API every 6 seconds and reflects new prices,
  decisions, and alerts as they land.

Since there's no real marketplace behind this yet, prices come from a
**seeded random walk** (`ProductPriceAgent`): each product's starting price
is deterministically derived from its name (so re-adding "iPhone 16 Pro"
always starts near the same price), and it drifts/dips tick over tick like
a noisy real market — including occasional bigger dips so GOOD_DEAL and
BUY_NOW are actually reachable in a short demo session. Swapping in a real
price source later only means replacing `get_current_price()`.

## Testing

```bash
python test_workflow.py
```

Runs 15 full cycles against a throwaway database and asserts that price
history, decisions, and alerts are all persisted correctly, and that only
the three valid verdicts are ever produced.

## Data model (SQLite, `pricescout.db`)

- `products` — name, target price, seed price
- `price_history` — every price observation (the agent's memory)
- `decisions` — every verdict + the numbers and reasoning behind it
- `alerts` — every BUY_NOW / GOOD_DEAL notification raised
