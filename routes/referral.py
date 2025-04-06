from flask import Blueprint, request, jsonify, render_template_string
from utils.storage import load_scores

referral_routes = Blueprint("referral_routes", __name__)

@referral_routes.route("/referral-history")
def referral_history():
    user_id = request.args.get("user_id", "")
    if not user_id:
        return jsonify({"error": "Missing user ID"}), 400

    scores = load_scores()
    user = next((e for e in scores if e["user_id"] == user_id), None)

    if not user:
        return jsonify({"error": "User not found"}), 404

    return jsonify(user.get("referrals", []))


@referral_routes.route("/referral-history-table")
def referral_history_table():
    scores = load_scores()
    all_referrals = []

    for user in scores:
        referrer = user.get("username", "Unknown")
        referrals = user.get("referrals", [])
        for ref in referrals:
            all_referrals.append({
                "referrer": referrer,
                "invitee": ref["ref_username"],
                "timestamp": ref["timestamp"],
                "reward": ref["reward"],
                "status": "Accepted" if ref["reward"] > 0 else "Pending"
            })

    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Referral History</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                background: #f7f7f7;
                padding: 20px;
                color: #333;
            }
            h2 {
                color: #0047ab;
            }
            table {
                width: 100%;
                border-collapse: collapse;
                background: #fff;
                margin-top: 20px;
            }
            th, td {
                border: 1px solid #ccc;
                padding: 10px;
                font-size: 14px;
                text-align: left;
            }
            th {
                background: #0047ab;
                color: #fff;
            }
            tr:nth-child(even) {
                background: #f2f2f2;
            }
        </style>
    </head>
    <body>
        <h2>📨 Referral History</h2>
        <table>
            <tr>
                <th>Referrer</th>
                <th>Invitee</th>
                <th>Time</th>
                <th>Status</th>
                <th>Reward</th>
            </tr>
            {% for entry in referrals %}
            <tr>
                <td>{{ entry.referrer }}</td>
                <td>{{ entry.invitee }}</td>
                <td>{{ entry.timestamp }}</td>
                <td>{{ entry.status }}</td>
                <td>{{ entry.reward }}</td>
            </tr>
            {% endfor %}
        </table>
    </body>
    </html>
    """

    return render_template_string(html, referrals=all_referrals)


@referral_routes.route("/user-logs")
def user_logs():
    scores = load_scores()
    logs = []

    for user in scores:
        logs.append({
            "username": user.get("username", "Anonymous"),
            "user_id": user.get("user_id", ""),
            "punches": user.get("score", 0),
            "referrals_sent": len([u for u in scores if u.get("referred_by") == user.get("user_id")]),
            "referrals_accepted": len(user.get("referrals", [])),
            "registered": user.get("referrals", [{}])[0].get("timestamp", "N/A")
        })

    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>User Logs</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                background: #f7f7f7;
                padding: 20px;
                color: #333;
            }
            h2 {
                color: #0047ab;
            }
            table {
                width: 100%;
                border-collapse: collapse;
                background: #fff;
                margin-top: 20px;
            }
            th, td {
                border: 1px solid #ccc;
                padding: 10px;
                font-size: 14px;
                text-align: left;
            }
            th {
                background: #0047ab;
                color: #fff;
            }
            tr:nth-child(even) {
                background: #f2f2f2;
            }
        </style>
    </head>
    <body>
        <h2>👥 User Logs</h2>
        <p>Total users: {{ total }}</p>
        <table>
            <tr>
                <th>Username</th>
                <th>User ID</th>
                <th>Punches</th>
                <th>Referrals Sent</th>
                <th>Referrals Accepted</th>
                <th>First Referral Reward Time</th>
            </tr>
            {% for entry in logs %}
            <tr>
                <td>{{ entry.username }}</td>
                <td>{{ entry.user_id }}</td>
                <td>{{ entry.punches }}</td>
                <td>{{ entry.referrals_sent }}</td>
                <td>{{ entry.referrals_accepted }}</td>
                <td>{{ entry.registered }}</td>
            </tr>
            {% endfor %}
        </table>
    </body>
    </html>
    """

    return render_template_string(html, logs=logs, total=len(scores))
