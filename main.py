from flask import Flask, request, jsonify, render_template_string
import json
import os
import datetime

app = Flask(__name__)

# Use /tmp for Railway compatibility
DATA_FILE = "/tmp/scores.json"
LOG_FILE = "/tmp/logs.txt"

# Create log entry
def log_event(message):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_FILE, "a") as f:
        f.write(f"[{timestamp}] {message}\n")

# Ensure data file exists
def ensure_file():
    if not os.path.exists(DATA_FILE):
        with open(DATA_FILE, "w") as f:
            json.dump([], f)
        log_event("✅ Created new scores.json")

# Load scores
def load_scores():
    ensure_file()
    try:
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    except Exception as e:
        log_event(f"❌ Error loading scores: {e}")
        return []

# Save scores
def save_scores(scores):
    try:
        with open(DATA_FILE, "w") as f:
            json.dump(scores, f)
        log_event("✅ Scores saved")
    except Exception as e:
        log_event(f"❌ Error saving scores: {e}")

# Submit score
@app.route("/submit", methods=["POST"])
def submit():
    data = request.get_json()
    username = data.get("username", "Anonymous")
    score = int(data.get("score", 0))

    log_event(f"📩 Score submitted – {username}: {score}")

    scores = load_scores()
    updated = False

    for entry in scores:
        if entry["username"] == username:
            if score > entry["score"]:
                entry["score"] = score
                log_event(f"🔁 Updated score for {username} to {score}")
            updated = True
            break

    if not updated:
        scores.append({"username": username, "score": score})
        log_event(f"➕ New user: {username} with score {score}")

    save_scores(scores)
    return jsonify({"status": "ok"})

# JSON leaderboard
@app.route("/leaderboard")
def leaderboard():
    scores = load_scores()
    sorted_scores = sorted(scores, key=lambda x: x["score"], reverse=True)[:10]
    log_event("📊 Leaderboard accessed (JSON)")
    return jsonify(sorted_scores)

# HTML leaderboard
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
            {% for i, entry in enumerate(scores) %}
            <tr>
                <td>{{ i + 1 }}</td>
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

# Debug logs
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
        <h2>🪵 TrumpToss Server Logs</h2>
        <div>{log_content}</div>
    </body>
    </html>
    """

# Run the app
if __name__ == "__main__":
    app.run(debug=True, port=5000)
