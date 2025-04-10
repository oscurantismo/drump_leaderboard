from flask import Blueprint, session, redirect, url_for
import json
import os

clear_rewards_bp = Blueprint("clear_rewards", __name__)
REWARDS_FILE = "rewards.json"

@clear_rewards_bp.route("/admin/clear-rewards")
def clear_rewards():
    if not session.get("logged_in"):
        return redirect(url_for("auth_routes.login"))

    try:
        with open(REWARDS_FILE, "w") as f:
            json.dump([], f, indent=2)
        return """
        <h2>✅ All rewards have been cleared.</h2>
        <p><a href="/debug-logs">⬅️ Return to Debug Logs</a></p>
        """
    except Exception as e:
        return f"<h2>❌ Failed to clear rewards: {e}</h2>"
