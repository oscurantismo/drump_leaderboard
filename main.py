from flask import Flask, request, jsonify, render_template_string
import json
import os
import datetime

app = Flask(__name__)
DATA_FILE = "scores.json"

LOG_FILE = "logs.txt"

def log_event(message):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_FILE, "a") as f:
        f.write(f"[{timestamp}] {message}\n")

# Ensure scores.json exists
def ensure_file():
    if not os.path.exists(DATA_FILE):
        with open(DATA_FILE, "w") as f:
            json.dump([], f)

# Load scores from file
def load_scores():
    ensure_file()
    with open(DATA_FILE, "r") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return []

# Save scores to file
def save_scores(scores):
    with open(DATA_FILE, "w") as f:
        json.dump(scores, f)

# Endpoint to submit scores
@app.route("/submit", methods=["POST"])
def submit():
    data = request.get_json()
    username = data.get("username", "Anonymous")
    score = int(data.get("score", 0))

    log_event(f"Score submitted – {username}: {score}")

    scores = load_scores()
    updated = False

    for entry in scores:
        if entry["username"] == username:
            if score > entry["score"]:
                entry["score"] = score
                log_event(f"Updated score for {username} to {score}")
            updated = True
            break

    if not updated:
        scores.append({"username": username, "score": score})
        log_event(f"New user added: {username} with score {score}")

    save_scores(scores)
    return jsonify({"status": "ok"})


# API for raw JSON leaderboard
@app.route("/leaderboard")
def leaderboard():
    scores = load_scores()
    sorted_scores = sorted(scores, key=lambda x: x["score"], reverse=True)[:10]
    return jsonify(sorted_scores)

# HTML Leaderboard Page
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
        <h2>🪵 TrumpToss Server Logs</h2>
        <div>{log_content}</div>
    </body>
    </html>
    """


# Run locally or with WSGI
if __name__ == "__main__":
    app.run(debug=True, port=5000)
