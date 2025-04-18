# routes/reward_logs.py
import os, json
from flask import Blueprint, request, render_template_string
from routes.rewards import ensure_rewards_file  # ✅ (optional)

reward_logs_bp = Blueprint("reward_logs", __name__)
REWARDS_FILE = "rewards.json"

@reward_logs_bp.route("/reward-logs")
def reward_logs_page():
    ensure_rewards_file()  # ✅ Ensure file exists

    # --- load ledger (silently fall back to empty) -----------------------
    logs = []
    if os.path.exists(REWARDS_FILE):
        try:
            with open(REWARDS_FILE) as f:
                logs = json.load(f)
        except json.JSONDecodeError as e:
            print(f"❌ Failed to read rewards.json: {e}")

    # --- optional search filter -----------------------------------------
    q = request.args.get("q", "").lower()
    if q:
        logs = [
            e for e in logs
            if q in e.get("username", "").lower()
               or q in e.get("user_id", "").lower()
               or q in e.get("reward_type", "").lower()
               or q in e.get("source_id", "").lower()
        ]

    # --- render ----------------------------------------------------------
    return render_template_string(
        """
<!DOCTYPE html>
<html>
<head>
  <title>🎁 Reward Ledger</title>
  <style>
    body{font-family:monospace;padding:20px;}
    table{border-collapse:collapse;width:100%;}
    th,td{border:1px solid #ccc;padding:6px;font-size:13px;}
    th{background:#0047ab;color:#fff;}
    input[type=text]{padding:6px;width:260px;margin-bottom:10px;}
    .empty{color:#888;font-style:italic;text-align:center;padding:18px;}
    tr.highlight td { background-color: #ffeeba; font-weight: bold; }
  </style>
</head>
<body>
  <h2>🎁 Reward Ledger</h2>

  <form method="get">
    <input name="q" type="text" placeholder="Search..." value="{{ request.args.get('q','') }}">
    <button type="submit">Search</button>
  </form>

  <table>
    <tr>
      <th>User</th><th>Type</th><th>Source ID</th>
      <th>Δ Punches</th><th>Prev → New</th><th>Time (UTC)</th>
    </tr>
    {% if logs %}
      {% for e in logs %}
      <tr class="{{ 'highlight' if e.change >= 100 else '' }}">
        <td>{{ e.username }} ({{ e.user_id }})</td>
        <td>{{ e.reward_type }}</td>
        <td>{{ e.source_id }}</td>
        <td>{{ e.change }}</td>
        <td>{{ e.prev_score }} → {{ e.new_score }}</td>
        <td>{{ e.timestamp }}</td>
      </tr>
      {% endfor %}
    {% else %}
      <tr><td colspan="6" class="empty">— No rewards logged yet —</td></tr>
    {% endif %}
  </table>
</body>
</html>
""",
        logs=logs,
    )
