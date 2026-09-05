"""
app.py
-------
Flask web server for PriceScout.

PriceScout supports TWO ways of adding products:

1. Web Dashboard
2. VS Code Terminal

Both use the same database and autonomous agent workflow.

Run:
    pip install -r requirements.txt
    python app.py

Then open:
    http://localhost:5000
"""

from flask import Flask, jsonify, request, render_template
import threading
import logging


import database as db
from agents.price_agent import ProductPriceAgent
from agents.orchestrator import orchestrator


app = Flask(__name__)


# ===============================================================
# TERMINAL PREDICTION DISPLAY
# ===============================================================

def print_prediction(result, product_name=None, target_price=None):
    """
    Print the AI prediction in the VS Code terminal.
    """

    print("\n")
    print("=" * 60)
    print("                    AI PREDICTION")
    print("=" * 60)

    # Product name
    if product_name:
        print(f"PRODUCT       : {product_name}")

    # Target price
    if target_price is not None:
        print(f"TARGET PRICE  : ₹{target_price:,.2f}")

    # Print result values safely
    if isinstance(result, dict):

        if "current_price" in result:
            try:
                print(
                    f"CURRENT PRICE : ₹{float(result['current_price']):,.2f}"
                )
            except (TypeError, ValueError):
                print(f"CURRENT PRICE : {result['current_price']}")

        if "avg_price" in result:
            try:
                print(
                    f"AVERAGE PRICE : ₹{float(result['avg_price']):,.2f}"
                )
            except (TypeError, ValueError):
                print(f"AVERAGE PRICE : {result['avg_price']}")

        if "price_change" in result:
            print(f"PRICE CHANGE  : {result['price_change']}")

        if "verdict" in result:
            print(f"PREDICTION    : {result['verdict']}")

        if "reasoning" in result:
            print(f"REASONING     : {result['reasoning']}")

    print("=" * 60)


# ===============================================================
# TERMINAL INPUT
# ===============================================================

def terminal_input():
    """
    Continuously accept product name and target price
    from the VS Code terminal.
    """

    print("\n")
    print("=" * 60)
    print("                 PRICESCOUT TERMINAL")
    print("=" * 60)
    print("Terminal mode is ready!")
    print("You can add products directly from VS Code.")
    print("Type 'exit' anytime to stop terminal input.")
    print("=" * 60)

    while True:

        try:
            # ---------------------------------------------------
            # PRODUCT NAME
            # ---------------------------------------------------

            name = input("\nEnter product name (or 'exit'): ").strip()

            if name.lower() in ["exit", "quit"]:
                print("\nPriceScout terminal input stopped.")
                break

            if not name:
                print("❌ Product name cannot be empty.")
                continue

            # ---------------------------------------------------
            # TARGET PRICE
            # ---------------------------------------------------

            target_input = input("Enter target price: ").strip()

            try:
                target_price = float(target_input)

                if target_price <= 0:
                    raise ValueError

            except ValueError:
                print("❌ Please enter a valid positive price.")
                continue

            # ---------------------------------------------------
            # RUN PRICE AGENT
            # ---------------------------------------------------

            print("\n" + "-" * 60)
            print("                 RUNNING AGENTS")
            print("-" * 60)

            print("🔎 Getting initial product price...")

            seed_price = ProductPriceAgent.seed_price(name)

            print(f"✓ Initial price: ₹{seed_price:,.2f}")

            # ---------------------------------------------------
            # ADD PRODUCT TO DATABASE
            # ---------------------------------------------------

            product_id = db.add_product(
                name,
                target_price,
                seed_price
            )

            print(f"✓ Product added with ID: {product_id}")

            # ---------------------------------------------------
            # RUN AUTONOMOUS WORKFLOW
            # ---------------------------------------------------

            print("\n🤖 Running autonomous agent workflow...")

            result = orchestrator.run_cycle_by_id(product_id)

            print("✓ Price Agent completed")
            print("✓ Analysis Agent completed")
            print("✓ Decision Agent completed")
            print("✓ Notification Agent completed")

            # ---------------------------------------------------
            # DISPLAY PREDICTION
            # ---------------------------------------------------

            print_prediction(
                result,
                product_name=name,
                target_price=target_price
            )

        except KeyboardInterrupt:
            print("\n\nPriceScout terminal stopped.")
            break

        except EOFError:
            print("\n\nTerminal input closed.")
            break

        except Exception as e:
            print(f"\n❌ Error: {e}")


# ===============================================================
# WEB DASHBOARD
# ===============================================================

@app.route("/")
def dashboard():
    return render_template("index.html")


# ===============================================================
# PRODUCTS
# ===============================================================

@app.route("/api/products", methods=["GET"])
def api_list_products():

    products = db.list_products()

    out = []

    for p in products:

        history = db.get_price_history(p["id"])

        latest_decision = db.get_latest_decision(p["id"])

        out.append({
            **p,
            "price_history": history,
            "latest_decision": latest_decision,
        })

    return jsonify(out)


@app.route("/api/products", methods=["POST"])
def api_add_product():

    body = request.get_json(force=True)

    name = (body.get("name") or "").strip()

    target_price = body.get("target_price")

    # -----------------------------------------------------------
    # VALIDATE PRODUCT NAME
    # -----------------------------------------------------------

    if not name:
        return jsonify({
            "error": "Product name is required."
        }), 400

    # -----------------------------------------------------------
    # VALIDATE TARGET PRICE
    # -----------------------------------------------------------

    try:

        target_price = float(target_price)

        if target_price <= 0:
            raise ValueError

    except (TypeError, ValueError):

        return jsonify({
            "error": "Target price must be a positive number."
        }), 400

    # -----------------------------------------------------------
    # GET INITIAL PRICE
    # -----------------------------------------------------------

    seed_price = ProductPriceAgent.seed_price(name)

    # -----------------------------------------------------------
    # ADD PRODUCT
    # -----------------------------------------------------------

    product_id = db.add_product(
        name,
        target_price,
        seed_price
    )

    # -----------------------------------------------------------
    # RUN FIRST AGENT CYCLE
    # -----------------------------------------------------------

    result = orchestrator.run_cycle_by_id(product_id)

    # -----------------------------------------------------------
    # PRINT WEB PREDICTION IN TERMINAL TOO
    # -----------------------------------------------------------

    print("\n🌐 Product added from WEB dashboard.")

    print_prediction(
        result,
        product_name=name,
        target_price=target_price
    )

    return jsonify(result), 201


# ===============================================================
# DELETE PRODUCT
# ===============================================================

@app.route("/api/products/<int:product_id>", methods=["DELETE"])
def api_remove_product(product_id):

    db.deactivate_product(product_id)

    return jsonify({
        "ok": True
    })


# ===============================================================
# RUN AGENT CYCLE FOR ONE PRODUCT
# ===============================================================

@app.route("/api/products/<int:product_id>/check", methods=["POST"])
def api_check_price(product_id):

    try:

        result = orchestrator.run_cycle_by_id(product_id)

    except ValueError as exc:

        return jsonify({
            "error": str(exc)
        }), 404

    # -----------------------------------------------------------
    # PRINT PREDICTION IN TERMINAL
    # -----------------------------------------------------------

    print("\n🔄 Manual price check from WEB dashboard.")

    print_prediction(result)

    return jsonify(result)


# ===============================================================
# CHECK ALL PRODUCTS
# ===============================================================

@app.route("/api/check-all", methods=["POST"])
def api_check_all():

    results = orchestrator.run_cycle_all()

    print("\n")
    print("=" * 60)
    print("              CHECKING ALL PRODUCTS")
    print("=" * 60)

    if isinstance(results, list):

        for result in results:

            print_prediction(result)

    else:

        print_prediction(results)

    return jsonify(results)


# ===============================================================
# ALERTS
# ===============================================================

@app.route("/api/alerts", methods=["GET"])
def api_alerts():

    return jsonify(
        db.list_alerts()
    )


# ===============================================================
# START APPLICATION
# ===============================================================

if __name__ == "__main__":

    # -----------------------------------------------------------
    # INITIALIZE DATABASE
    # -----------------------------------------------------------

    db.init_db()

    print("\n" + "=" * 60)
    print("                 PRICESCOUT")
    print("=" * 60)
    print("✓ Database initialized")

    # -----------------------------------------------------------
    # START AUTONOMOUS MONITORING
    # -----------------------------------------------------------

    orchestrator.start_monitoring()

    print("✓ Autonomous monitoring started")

    # -----------------------------------------------------------
    # START TERMINAL INPUT THREAD
    # -----------------------------------------------------------

    terminal_thread = threading.Thread(
        target=terminal_input,
        daemon=True
    )

    terminal_thread.start()

    print("✓ Terminal input enabled")

    print("=" * 60)
    print("🌐 Web Dashboard : http://localhost:5000")
    print("💻 Terminal      : Ready for product input")
    print("=" * 60)
    print()

     # Hide Flask request logs from terminal
    logging.getLogger("werkzeug").setLevel(logging.ERROR)

    # -----------------------------------------------------------
    # START FLASK SERVER
    # -----------------------------------------------------------

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=False
    )