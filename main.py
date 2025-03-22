from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import json

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "https://oscurantismo.github.io"}})


DATA_FILE = "scores.json"

def load_scores():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return []

def save_scores(scores):
    with open(DATA_FILE, "w") as f:
        json.dump(scores, f)

import json
import os

@app.route("/submit", methods=["POST"])
def submit_score():
    data = request.get_json()
    username = data.get("username", "Anonymous")
    score = int(data.get("score", 0))

    print("✅ Score submitted:", username, score)
    print("📦 Full scores list:", scores)


    # Read existing scores or start new list
    if os.path.exists("scores.json"):
        with open("scores.json", "r") as f:
            scores = json.load(f)
    else:
        scores = []

    # Update score if user exists or add new
    for entry in scores:
        if entry["username"] == username:
            if score > entry["score"]:
                entry["score"] = score
            break
    else:
        scores.append({"username": username, "score": score})

    with open("scores.json", "w") as f:
        json.dump(scores, f)

    return {"success": True}


@app.route("/leaderboard-page")
def leaderboard_page():
    try:
        with open("scores.json", "r") as f:
            scores = json.load(f)
    except:
        scores = []

    # Sort scores from highest to lowest
    scores = sorted(scores, key=lambda x: x["score"], reverse=True)

    # Limit to top 20 players
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


if __name__ == "__main__":
    app.run(debug=True)
