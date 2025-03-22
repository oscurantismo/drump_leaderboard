from flask import Flask, request, jsonify, render_template_string
import json
import os

app = Flask(__name__)
DATA_FILE = "scores.json"

# Ensure file exists
if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, "w") as f:
        json.dump([], f)

def load_scores():
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def save_scores(scores):
    with open(DATA_FILE, "w") as f:
        json.dump(scores, f)

@app.route("/submit", methods=["POST"])
def submit():
    data = request.get_json()
    username = data.get("username", "Anonymous")
    score = int(data.get("score", 0))

    print(f"🔥 Received score from {username}: {score}")

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

@app.route("/leaderboard")
def leaderboard():
    scores = load_scores()
    sorted_scores = sorted(scores, key=lambda x: x["score"], reverse=True)[:10]
    return jsonify(sorted_scores)

@app.route("/leaderboard-page")
def leaderboard_page():
    scores = load_scores()
    sorted_scores = sorted(scores, key=lambda x: x["score"], reverse=True)[:10]

    html = """ ... """  # Your same HTML template
    return render_template_string(html, scores=sorted_scores)

if __name__ == "__main__":
    app.run(debug=True, port=5000)
