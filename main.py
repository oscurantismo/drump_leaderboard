from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS
import json
import os
import datetime

app = Flask(__name__)
CORS(app)

DATA_FILE = "scores.json"
LOG_FILE = "logs.txt"

def log_event(message):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_FILE, "a") as f:
        f.write(f"[{timestamp}] {message}\n")

def ensure_file():
    if not os.path.exists(DATA_FILE):
        with open(DATA_FILE, "w") as f:
            json.dump([], f)
        log_event("✅ Created new scores.json")

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

@app.route("/submit", methods=["POST"])
def submit():
    data = request.get_json()
    username = (data.get("username") or "Anonymous").strip()
    user_id = str(data.get("user_id", "")).strip()
    score = int(data.get("score", 0))
    score = max(0, score)

    log_event(f"🔄 Score submitted: {username} (ID: {user_id}) – {score}")

    scores = load_scores()
    updated = False

    for entry in scores:
        if entry.get("user_id") == user_id:
            if score > entry["score"]:
                entry["score"] = score
                entry["username"] = username
                log_event(f"✅ Updated score for {username} (ID: {user_id}) to {score}")
            updated = True
            break

    if not updated:
        scores.append({"username": username, "user_id": user_id, "score": score})
        log_event(f"🆕 New user added: {username} (ID: {user_id}) with score {score}")

    save_scores(scores)
    return jsonify({"status": "ok"})

@app.route("/register", methods=["POST"])
def register():
    data = request.get_json()
    username = (data.get("username") or "Anonymous").strip()
    user_id = str(data.get("user_id", "")).strip()

    scores = load_scores()
    for entry in scores:
        if entry.get("user_id") == user_id:
            log_event(f"🔁 Already registered: {username} (ID: {user_id})")
            return jsonify({"status": "already_registered"})

    scores.append({"username": username, "user_id": user_id, "score": 0})
    save_scores(scores)
    log_event(f"📝 Auto-registered new user: {username} (ID: {user_id})")
    return jsonify({"status": "registered"})

@app.route("/leaderboard")
def leaderboard():
    scores = load_scores()
    sorted_scores = sorted(scores, key=lambda x: x["score"], reverse=True)[:10]
    log_event(f"📊 Leaderboard requested (JSON): {sorted_scores}")
    return jsonify(sorted_scores)

@app.route("/leaderboard-page")
def leaderboard_page():
    scores = load_scores()
    sorted_scores = sorted(scores, key=lambda x: x["score"], reverse=True)[:10]
    current_user_id = request.args.get("user_id", "")

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
        {% else %}
        <p>No scores submitted yet.</p>
        {% endif %}
    </body>
    </html>
    """
    log_event("🧾 Leaderboard page viewed (HTML)")
    return render_template_string(html, scores=sorted_scores, current_user_id=current_user_id)

@app.route("/profile", methods=["GET"])
def profile():
    user_id = request.args.get("user_id")
    if not user_id:
        log_event("❗ Missing user ID in profile request.")
        return jsonify({"error": "User ID is required"}), 400

    scores = load_scores()
    user_data = next((entry for entry in scores if entry.get("user_id") == user_id), None)

    if not user_data:
        log_event(f"❗ User not found: {user_id}")
        return jsonify({"error": "User not found"}), 404

    return jsonify({
        "username": user_data.get("username", "Anonymous"),
        "coins": user_data.get("score", 0)
    })

@app.route("/referral", methods=["POST"])
def referral():
    data = request.get_json()
    referrer_id = str(data.get("referrer_id", "")).strip()
    referred_user_id = str(data.get("user_id", "")).strip()

    if not referrer_id or not referred_user_id or referrer_id == referred_user_id:
        log_event("❗ Invalid referral data.")
        return jsonify({"error": "Invalid referral data"}), 400

    scores = load_scores()
    referrer = next((entry for entry in scores if entry.get("user_id") == referrer_id), None)
    referred_user = next((entry for entry in scores if entry.get("user_id") == referred_user_id), None)

    if not referrer:
        log_event(f"❗ Referrer not found: {referrer_id}")
        return jsonify({"error": "Referrer not found"}), 404

    if not referred_user:
        log_event(f"❗ Referred user not found: {referred_user_id}")
        return jsonify({"error": "Referred user not found"}), 404

    # Reward referrer with 10 coins
    referrer["score"] += 10
    save_scores(scores)
    log_event(f"🎉 Referral completed: {referrer['username']} earned +10 coins.")

    return jsonify({"status": "success", "new_coins": referrer["score"]})

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

    # Register the new user
    scores.append({"username": username, "user_id": user_id, "score": 0})
    save_scores(scores)
    log_event(f"📝 Registered new user: {username} (ID: {user_id})")

    # Handle referral if referrer_id exists
    if referrer_id:
        try:
            referral_response = referral()
            log_event(f"🎁 Referral bonus granted to {referrer_id}")
        except Exception as e:
            log_event(f"❗ Referral failed: {str(e)}")

    return jsonify({"status": "registered"})

def log_event(message):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_FILE, "a") as f:
        f.write(f"[{timestamp}] {message}\n")
    print(f"[{timestamp}] {message}")  # Print to console for easy debugging


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
        <h2>🪝 Drump Server Logs</h2>
        <div>{log_content}</div>
    </body>
    </html>
    """

if __name__ == "__main__":
    app.run(debug=True, port=5000)
