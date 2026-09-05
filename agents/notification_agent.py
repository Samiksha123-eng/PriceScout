"""
notification_agent.py
-----------------------
Notification Agent.

Decides whether a decision is "alert-worthy" and, if so, writes an alert
record. In this project an alert is displayed on the dashboard; the same
function is the natural place to plug in email/SMS/webhook delivery later.
"""

import database as db

ALERT_WORTHY = {"BUY_NOW", "GOOD_DEAL"}


class NotificationAgent:
    def notify(self, product: dict, decision: dict, reasoning: str):
        """
        Raises an alert if the verdict is BUY_NOW or GOOD_DEAL.
        Returns the alert dict if one was created, else None.
        """
        verdict = decision["verdict"]
        if verdict not in ALERT_WORTHY:
            return None

        if verdict == "BUY_NOW":
            headline = f"Target reached! {product['name']} is at {decision['current_price']} (target {decision['target_price']})."
        else:
            headline = f"Good deal on {product['name']}: {decision['current_price']} is {abs(decision['vs_avg_pct'])}% below its average."

        message = f"{headline} {reasoning}"
        alert_id = db.add_alert(product["id"], message, verdict)
        return {"id": alert_id, "message": message, "verdict": verdict}
