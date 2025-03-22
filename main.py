from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import json

app = Flask(__name__)
CORS(app)

DATA_FILE = "scores.json"

def load_scores():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return []

def save_scores(scores):
    with open(DATA_FILE, "w") as f:
        json.dump(scores, f)

@app.route("/submit", methods=["POST"])
def submit_score():
    data = request.get_json()
    username = data.get("username", "Anonymous")
    score = int(data.get("score", 0))

    scores = load_scores()
    found = False
    for entry in scores:
        if entry["username"] == username:
            if score > entry["score"]:
                entry["score"] = score
            found = True
            break

    if not found:
        scores.append({"username": username, "score": score})

    scores.sort(key=lambda x: x["score"], reverse=True)
    save_scores(scores)
    return jsonify({"status": "success"}), 200

@app.route("/leaderboard-page")
def leaderboard_page():
    return """
    <html>
    <head>
        <title>TrumpToss Leaderboard</title>
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <style>
            body {
                font-family: 'Segoe UI', sans-serif;
                background: #f1f1f1;
                color: #333;
                padding: 2rem;
                text-align: center;
            }
            h1 {
                font-size: 2em;
                margin-bottom: 1rem;
                color: #222;
            }
            .entry {
                background: #fff;
                padding: 12px 20px;
                margin: 8px auto;
                width: 100%;
                max-width: 400px;
                border-radius: 8px;
                box-shadow: 0 2px 5px rgba(0,0,0,0.1);
                font-size: 1.1rem;
            }
        </style>
    </head>
    <body>
        <h1>🏆 TrumpToss Leaderboard</h1>
        <div id="board">Loading...</div>
        <script>
            fetch("/leaderboard")
                .then(res => res.json())
                .then(data => {
                    const board = document.getElementById("board");
                    if (!data.length) {
                        board.innerHTML = "<p>No scores yet!</p>";
                        return;
                    }
                    board.innerHTML = data.map((e, i) => (
                        `<div class='entry'>${i + 1}. @${e.username} – ${e.score} punches</div>`
                    )).join('');
                })
                .catch(() => {
                    document.getElementById("board").innerText = "Failed to load leaderboard.";
                });
        </script>
    </body>
    </html>
    """


if __name__ == "__main__":
    app.run(debug=True)
