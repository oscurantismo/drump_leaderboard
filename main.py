from flask import Flask, request, jsonify, render_template_string, send_file
from flask_cors import CORS
import json
import os
import datetime

app = Flask(__name__)
CORS(app)

DATA_FILE = "/app/data/scores.json"
LOG_FILE = "/app/data/logs.txt"
BACKUP_FOLDER = "/app/data/backups"

def log_event(message):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_FILE, "a") as f:
        f.write(f"[{timestamp}] {message}\n")
    print(f"[{timestamp}] {message}")

def ensure_file():
    if not os.path.exists(DATA_FILE):
        os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
        with open(DATA_FILE, "w") as f:
            json.dump([], f)
        log_event("✅ Created new scores.json in /app/data")

def ensure_backup_folder():
    os.makedirs(BACKUP_FOLDER, exist_ok=True)
    log_event("📁 Backup folder ensured at /app/data/backups")

def load_scores():
    ensure_file()
    with open(DATA_FILE, "r") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            log_event("❌ Failed to decode JSON")
            return []

def save_scores(scores):
    with open(DATA_FILE, "w") as f:
        json.dump(scores, f, indent=2)

def backup_scores():
    ensure_backup_folder()
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = os.path.join(BACKUP_FOLDER, f"leaderboard_backup_{timestamp}.json")
    scores = load_scores()
    with open(backup_path, "w") as f:
        json.dump(scores, f, indent=2)
    log_event(f"💾 Backup saved: {backup_path}")

@app.route("/submit", methods=["POST"])
def submit():
    data = request.get_json()
    username = (data.get("username") or "Anonymous").strip()
    user_id = str(data.get("user_id", "")).strip()
    score = max(0, int(data.get("score", 0)))

    log_event(f"🔄 Score submitted: {username} (ID: {user_id}) – {score}")

    scores = load_scores()
    updated = False

    for entry in scores:
        if entry.get("user_id") == user_id:
            if score > entry["score"]:
                old_score = entry["score"]
                entry["score"] = score
                entry["username"] = username
                log_event(f"✅ Updated score for {username} (ID: {user_id}) from {old_score} to {score}")

                referrer_id = entry.get("referred_by")
                if old_score < 10 <= score and referrer_id:
                    referrer = next((e for e in scores if e["user_id"] == referrer_id), None)
                    if referrer:
                        reward = 100
                        old_ref_score = referrer["score"]
                        referrer["score"] += reward

                        if "referrals" not in referrer:
                            referrer["referrals"] = []

                        referrer["referrals"].append({
                            "ref_user_id": user_id,
                            "ref_username": username,
                            "timestamp": datetime.datetime.now().isoformat(),
                            "reward": reward,
                            "before_score": old_ref_score,
                            "after_score": referrer["score"]
                        })

                        log_event(f"🎉 Referral bonus: {referrer['username']} (ID: {referrer_id}) +{reward} punches for {username}")
            updated = True
            break

    if not updated:
        scores.append({"username": username, "user_id": user_id, "score": score})
        log_event(f"🆕 New user added: {username} (ID: {user_id}) with score {score}")

    save_scores(scores)
    backup_scores()
    return jsonify({"status": "ok"})

@app.route("/register", methods=["POST"])
def register():
    data = request.get_json()
    username = (data.get("username") or "Anonymous").strip()
    user_id = str(data.get("user_id", "")).strip()
    referrer_id = str(data.get("referrer_id", "")).strip()

    scores = load_scores()
    for entry in scores:
        if entry.get("user_id") == user_id:
            log_event(f"🔁 Already registered: {username} (ID: {user_id})")
            return jsonify({"status": "already_registered"})

    new_user = {
        "username": username,
        "user_id": user_id,
        "score": 0,
    }

    if referrer_id:
        new_user["referred_by"] = referrer_id

    scores.append(new_user)
    save_scores(scores)
    log_event(f"📝 Registered new user: {username} (ID: {user_id})")

    return jsonify({"status": "registered"})

@app.route("/profile")
def profile():
    user_id = request.args.get("user_id", "")
    if not user_id:
        return jsonify({"error": "Missing user ID"}), 400

    scores = load_scores()
    entry = next((e for e in scores if e["user_id"] == user_id), None)

    if not entry:
        return jsonify({"error": "User not found"}), 404

    return jsonify({
        "username": entry["username"],
        "punches": entry["score"]
    })

@app.route("/referral-history")
def referral_history():
    user_id = request.args.get("user_id", "")
    if not user_id:
        return jsonify({"error": "Missing user ID"}), 400

    scores = load_scores()
    user = next((e for e in scores if e["user_id"] == user_id), None)

    if not user:
        return jsonify({"error": "User not found"}), 404

    return jsonify(user.get("referrals", []))

@app.route("/leaderboard")
def leaderboard():
    scores = load_scores()
    sorted_scores = sorted(scores, key=lambda x: x["score"], reverse=True)[:25]
    return jsonify(sorted_scores)

@app.route("/leaderboard-page")
def leaderboard_page():
    scores = load_scores()
    filtered_scores = [s for s in scores if s.get("score", 0) > 0]
    sorted_scores = sorted(filtered_scores, key=lambda x: x["score"], reverse=True)[:25]
    current_user_id = request.args.get("user_id", "")
    total_players = len(filtered_scores)

    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Leaderboard</title>
        <style>
            body {
                font-family: 'Arial Black', sans-serif;
                background: #ffffff;
                padding: 20px;
                color: #002868;
                text-align: center;
            }
            h2 {
                color: #b22234;
                margin-bottom: 20px;
            }
            table {
                width: 100%;
                border-collapse: collapse;
                margin-top: 10px;
                margin-bottom: 60px;
            }
            th, td {
                padding: 12px;
                border-bottom: 2px solid #ddd;
                font-size: 16px;
            }
            th {
                background: #002868;
                color: white;
            }
            tr.highlight {
                background-color: #ffeeba !important;
                animation: flash 1s ease-in-out;
            }
            tr:hover {
                background-color: #f1f1f1;
            }
            @keyframes flash {
                from { background-color: #fff3cd; }
                to { background-color: #ffeeba; }
            }
        </style>
    </head>
    <body>
        <h2>🏆 Leaderboard</h2>
        {% if scores %}
        <table>
            <tr><th>#</th><th>Username</th><th>Score</th></tr>
            {% for entry in scores %}
            <tr class="{% if entry.user_id == current_user_id %}highlight{% endif %}">
                <td>{{ loop.index }}</td>
                <td>{{ entry.username }}</td>
                <td>{{ entry.score }}</td>
            </tr>
            {% endfor %}
        </table>
        <div class="footer">showing {{ scores|length }}/{{ total }} players</div>
        {% else %}
        <p>No scores submitted yet.</p>
        {% endif %}
    </body>
    </html>
    """
    return render_template_string(html, scores=sorted_scores, current_user_id=current_user_id)

@app.route("/referral-history-table")
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

@app.route("/user-logs")
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


@app.route("/download-backup")
def download_backup():
    filename = request.args.get("file")
    if not filename or not filename.endswith(".json"):
        return "Invalid filename", 400
    filepath = os.path.join(BACKUP_FOLDER, filename)
    if not os.path.exists(filepath):
        return "File not found", 404
    return send_file(filepath, as_attachment=True)

@app.route("/backups")
def view_backups():
    files = sorted(os.listdir(BACKUP_FOLDER), reverse=True)
    json_files = [f for f in files if f.endswith(".json")]

    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>📦 Backups</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                background: #f4f4f4;
                padding: 20px;
                color: #333;
            }
            h2 {
                color: #0047ab;
            }
            ul {
                list-style: none;
                padding: 0;
            }
            li {
                background: #fff;
                margin-bottom: 10px;
                padding: 10px 15px;
                border-radius: 8px;
                box-shadow: 0 2px 5px rgba(0,0,0,0.1);
                display: flex;
                justify-content: space-between;
                align-items: center;
            }
            a.download-btn {
                background: #007bff;
                color: #fff;
                padding: 6px 12px;
                text-decoration: none;
                border-radius: 6px;
                font-weight: bold;
                transition: background 0.3s;
            }
            a.download-btn:hover {
                background: #0056b3;
            }
        </style>
    </head>
    <body>
        <h2>📦 Leaderboard & Referral Backups</h2>
        <ul>
    """

    for filename in json_files:
        html += f"""
        <li>
            {filename}
            <a class="download-btn" href="/download-backup?file={filename}">Download</a>
        </li>
        """

    html += """
        </ul>
    </body>
    </html>
    """

    return html

@app.route("/debug-logs")
def view_logs():
    if not os.path.exists(LOG_FILE):
        return "<h3>No logs yet.</h3>"

    with open(LOG_FILE, "r") as f:
        log_content = f.read().replace("\n", "<br>")

    return f"""
    <html>
    <head><title>Debug Logs</title></head>
    <body style="font-family: monospace; padding: 20px;">
        <h2>🪵 Server Logs</h2>
        <div>{log_content}</div>
    </body>
    </html>
    """

if __name__ == "__main__":
    app.run(debug=True, port=5000)
