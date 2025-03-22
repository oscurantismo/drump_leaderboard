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

@app.route("/leaderboard", methods=["GET"])
def get_leaderboard():
    scores = load_scores()
    top_scores = sorted(scores, key=lambda x: x["score"], reverse=True)[:10]
    return jsonify(top_scores), 200

if __name__ == "__main__":
    app.run(debug=True)
