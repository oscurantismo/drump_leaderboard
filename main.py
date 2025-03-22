from flask import Flask, request, jsonify
from collections import defaultdict

app = Flask(__name__)
leaderboard = defaultdict(int)  # In-memory score storage: {username: score}

@app.route("/")
def home():
    return "🏆 TrumpToss Leaderboard API is live!"

@app.route("/submit", methods=["POST"])
def submit_score():
    data = request.json
    username = data.get("username")
    score = data.get("score")

    if not username or not isinstance(score, int):
        return jsonify({"error": "Invalid data"}), 400

    if score > leaderboard[username]:
        leaderboard[username] = score

    return jsonify({"message": "Score submitted successfully"})

@app.route("/leaderboard", methods=["GET"])
def get_leaderboard():
    top_scores = sorted(leaderboard.items(), key=lambda x: x[1], reverse=True)[:10]
    return jsonify([
        {"username": name, "score": score} for name, score in top_scores
    ])
