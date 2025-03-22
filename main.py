from flask import Flask, request
from flask_cors import CORS
import json
import os

app = Flask(__name__)
CORS(app)

SCORES_PATH = "/tmp/scores.json"

@app.after_request
def allow_iframe(response):
    response.headers['X-Frame-Options'] = 'ALLOWALL'
    return response

@app.route("/")
def home():
    return "✅ TrumpToss Leaderboard Backend is running!"

@app.route("/submit", methods=["POST"])
def submit_score():
    data = request.get_json()
    username = data.get("username", "Anonymous")
    score = int(data.get("score", 0))

    print(f"📩 Received score from {username}: {score}")

    scores = []

    if os.path.exists(SCORES_PATH):
        try:
            with open(SCORES_PATH, "r") as f:
                scores = json.load(f)
        except Exception as e:
            print("⚠️ Failed to load scores.json:", e)
            scores = []
    else:
        print("🆕 Creating new scores.json at /tmp")

    updated = False
    for entry in scores:
        if entry["username"] == username:
            if score > entry["score"]:
                entry["score"] = score
            updated = True
            break

    if not updated:
        scores.append({"username": username, "score": score})

    try:
        with open(SCORES_PATH, "w") as f:
            json.dump(scores, f)
        print("✅ scores.json written to /tmp")
    except Exception as e:
        print("❌ Failed to write /tmp/scores.json:", e)

    return {"success": True}

@app.route("/leaderboard-page")
def leaderboard_page():
    try:
        with open(SCORES_PATH, "r") as f:
            scores = json.load(f)
    except:
        scores = []

    scores = sorted(scores, key=lambda x: x["score"], reverse=True)
    scores = scores[:20]

    html = """
    <html>
    <head>
        <title>TrumpToss Leaderboard</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                text-align: center;
                padding: 40px;
                background-color: #f2f2f2;
            }
            h1 {
                font-size: 28px;
                color: #333;
            }
            table {
                margin: 20px auto;
                border-collapse: collapse;
                width: 90%%;
                max-width: 500px;
                background-color: #fff;
                box-shadow: 0 0 10px rgba(0,0,0,0.1);
            }
            th, td {
                padding: 12px;
                border-bottom: 1px solid #ddd;
            }
            th {
                background-color: #0077cc;
                color: white;
            }
            tr:nth-child(even) {
                background-color: #f9f9f9;
            }
            tr:hover {
                background-color: #e1f5fe;
            }
        </style>
    </head>
    <body>
        <h1>TrumpToss Leaderboard</h1>
        <table>
            <tr><th>Rank</th><th>Player</th><th>Punches</th></tr>
    """

    for i, entry in enumerate(scores):
        username = entry.get("username", "Anonymous")
        score = entry.get("score", 0)
        html += f"<tr><td>{i + 1}</td><td>{username}</td><td>{score}</td></tr>"

    html += """
        </table>
    </body>
    </html>
    """
    return html

@app.route("/debug-scores")
def debug_scores():
    try:
        with open(SCORES_PATH, "r") as f:
            scores = json.load(f)
        return {"scores": scores}
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    app.run(debug=True)
