import os
import json
from flask import Blueprint, request, render_template_string, send_file

reward_logs_bp = Blueprint("reward_logs", __name__)
REWARDS_FILE = "rewards.json"

@reward_logs_bp.route("/reward-logs")
def reward_logs_page():
    if not os.path.exists(REWARDS_FILE):
        return "<h3>No rewards have been logged yet.</h3>"

    with open(REWARDS_FILE, "r") as f:
        try:
            logs = json.load(f)
        except json.JSONDecodeError:
            return "<h3>Corrupt rewards log.</h3>"

    return render_template_string("""
    <html>
    <head>
        <title>🎁 Reward Logs</title>
        <style>
            body { font-family: monospace; padding: 20px; }
            table { border-collapse: collapse; width: 100%; margin-top: 10px; }
            th, td { border: 1px solid #ccc; padding: 6px; text-align: left; }
            th { background-color: #0047ab; color: white; }
            button {
                margin-top: 12px;
                padding: 8px 14px;
                border: none;
                background: #0047ab;
                color: white;
                border-radius: 6px;
                cursor: pointer;
            }
        </style>
    </head>
    <body>
        <h2>🎁 Leaderboard Reward Logs</h2>
        <table>
            <tr><th>User</th><th>Event</th><th>Change</th><th>Time (UTC)</th></tr>
            {% for entry in logs %}
            <tr>
                <td>{{ entry.username }} ({{ entry.user_id }})</td>
                <td>{{ entry.event }}</td>
                <td>{{ entry.change }}</td>
                <td>{{ entry.timestamp }}</td>
            </tr>
            {% endfor %}
        </table>

        <form method="get" action="/rewards/backup">
            <button type="submit">📥 Download Backup</button>
        </form>

        <form method="post" action="/rewards/replace" enctype="application/json">
            <p>To replace the log, send a POST to <code>/rewards/replace</code> with JSON data.</p>
        </form>
    </body>
    </html>
    """, logs=logs)
