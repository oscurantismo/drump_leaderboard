from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS
import json
import os
import datetime

app = Flask(__name__)
CORS(app)

DATA_FILE = "scores.json"
LOG_FILE = "logs.txt"

# === Utility Functions ===

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

# === API Routes ===

@app.route("/submit", methods=["POST"])
def submit():
    data = request.get_json()

    # Extract username and score safely
    username = (data.get("username") or "Anonymous").strip()
    score = data.get("score")

    # Validate values
    if not username:
        username = "Anonymous"
    try:
        score = int(score)
        if score < 0:
            score = 0
    except (TypeError, ValueError):
        log_event(f"❌ Invalid score submitted by {username}: {score}")
        return jsonify({"status": "error", "message": "Invalid score"}), 400

    log_event(f"🔄 Score submitted: {username} – {score}")

    scores = load_scores()
    updated = False

    for entry in scores:
        if entry.get("username", "").lower() == username.lower():
            if score > entry["score"]:
                entry["score"] = score
                log_event(f"✅ Updated score for {username} to {score}")
            updated = True
            break

    if not updated:
        scores.append({"username": username, "score": score})
        log_event(f"🆕 New user added: {username} with score {score}")

    save_scores(scores)
    return jsonify({"status": "ok"})

@app.route("/register", methods=["POST"])
def register():
    data = request.get_json()
    username = (data.get("username") or "Anonymous").strip()
    if not username:
        username = "Anonymous"

    scores = load_scores()
    for entry in scores:
        if entry.get("username", "").lower() == username.lower():
            log_event(f"🔁 Already registered: {username}")
            return jsonify({"status": "already_registered"})

    scores.append({"username": username, "score": 0})
    save_scores(scores)
    log_event(f"📝 Auto-registered new user: {username}")
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

    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Leaderboard</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                background: #fff;
                padding: 20px;
                color: #333;
                text-align: center;
            }
            h2 {
                color: #0077cc;
            }
            table {
                width: 100%;
                border-collapse: collapse;
                margin-top: 20px;
            }
            th, td {
                padding: 10px;
                border-bottom: 1px solid #ccc;
            }
            th {
                background: #f4f4f4;
            }
        </style>
    </head>
    <body>
        <h2>🏆 TrumpToss Leaderboard</h2>
        {% if scores %}
        <table>
            <tr><th>#</th><th>Username</th><th>Score</th></tr>
            {% for entry in scores %}
            <tr>
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
    return render_template_string(html, scores=sorted_scores)

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
        <h2>🪝 TrumpToss Server Logs</h2>
        <div>{log_content}</div>
    </body>
    </html>
    """

# === Entry Point ===
if __name__ == "__main__":
    app.run(debug=True, port=5000)
