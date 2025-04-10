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

    # Search filter
    query = request.args.get("q", "").lower()
    if query:
        logs = [l for l in logs if query in l.get("username", "").lower() or query in l.get("user_id", "") or query in l.get("event", "").lower()]

    # Summary per user
    summary = {}
    for log in logs:
        uid = log["user_id"]
        if uid not in summary:
            summary[uid] = {
                "username": log["username"],
                "total": 0,
                "events": []
            }
        summary[uid]["total"] += log["change"]
        summary[uid]["events"].append(log["event"])

    return render_template_string("""
    <html>
    <head>
        <title>🎁 Reward Logs</title>
        <style>
            body { font-family: monospace; padding: 20px; }
            input[type="text"] {
                padding: 6px;
                font-size: 14px;
                margin-bottom: 12px;
                width: 300px;
            }
            table { border-collapse: collapse; width: 100%; margin-top: 10px; }
            th, td { border: 1px solid #ccc; padding: 6px; text-align: left; font-size: 13px; }
            th { background-color: #0047ab; color: white; }
            .summary-box {
                background: #f5f5f5;
                padding: 10px;
                border-radius: 6px;
                margin-bottom: 20px;
            }
            .summary-box h3 {
                margin-top: 0;
            }
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

        <form method="get" action="/reward-logs">
            <input type="text" name="q" placeholder="Search username, ID or event..." value="{{ request.args.get('q', '') }}">
            <button type="submit">Search</button>
        </form>

        <div class="summary-box">
            <h3>📊 User Reward Summary</h3>
            {% for uid, user in summary.items() %}
                <p><strong>{{ user.username }}</strong> ({{ uid }}) — {{ user.total }} punches — {{ user.events|length }} rewards</p>
            {% endfor %}
        </div>

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
    """, logs=logs, summary=summary)
