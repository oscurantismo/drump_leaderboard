from flask import Flask, request, jsonify, render_template_string
import json
import os

app = Flask(__name__)
DATA_FILE = "scores.json"

# Load scores from file
def load_scores():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
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
    score = data.get("score", 0)

    scores = load_scores()
    updated = False

    for entry in scores:
        if entry["username"] == username:
            if score > entry["score"]:
                entry["score"] = score
            updated = True
            break

    if not updated:
        scores.append({"username": username, "score": score})

    save_scores(scores)
    return jsonify({"status": "ok"})

# JSON API for leaderboard
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

# Run locally or with WSGI
if __name__ == "__main__":
    app.run(debug=True, port=5000)
