from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS
import json
import os
import datetime

app = Flask(__name__)
CORS(app)

DATA_FILE = "/app/data/scores.json"
LOG_FILE = "/app/data/logs.txt"

def log_event(message):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_FILE, "a") as f:
        f.write(f"[{timestamp}] {message}\n")
    print(f"[{timestamp}] {message}")

def ensure_file():
    if not os.path.exists(DATA_FILE):
        os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
        with open(DATA_FILE, "w") as f:
            json.dump([], f)
        log_event("✅ Created new scores.json in /app/data")

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

@app.route("/submit", methods=["POST"])
def submit():
    data = request.get_json()
    username = (data.get("username") or "Anonymous").strip()
    user_id = str(data.get("user_id", "")).strip()
    score = max(0, int(data.get("score", 0)))

    log_event(f"🔄 Score submitted: {username} (ID: {user_id}) – {score}")

    scores = load_scores()
    updated = False

    for entry in scores:
        if entry.get("user_id") == user_id:
            if score > entry["score"]:
                old_score = entry["score"]
                entry["score"] = score
                entry["username"] = username
                log_event(f"✅ Updated score for {username} (ID: {user_id}) from {old_score} to {score}")

                # Check if this user was referred by someone and just reached 10 punches
                referrer_id = entry.get("referred_by")
                if old_score < 10 <= score and referrer_id:
                    referrer = next((e for e in scores if e["user_id"] == referrer_id), None)
                    if referrer:
                        reward = 100
                        old_ref_score = referrer["score"]
                        referrer["score"] += reward

                        if "referrals" not in referrer:
                            referrer["referrals"] = []

                        referrer["referrals"].append({
                            "ref_user_id": user_id,
                            "ref_username": username,
                            "timestamp": datetime.datetime.now().isoformat(),
                            "reward": reward,
                            "before_score": old_ref_score,
                            "after_score": referrer["score"]
                        })

                        log_event(f"🎉 Referral bonus: {referrer['username']} (ID: {referrer_id}) +{reward} punches for {username}")

            updated = True
            break

    if not updated:
        scores.append({"username": username, "user_id": user_id, "score": score})
        log_event(f"🆕 New user added: {username} (ID: {user_id}) with score {score}")

    save_scores(scores)
    return jsonify({"status": "ok"})

@app.route("/register", methods=["POST"])
def register():
    data = request.get_json()
    username = (data.get("username") or "Anonymous").strip()
    user_id = str(data.get("user_id", "")).strip()
    referrer_id = str(data.get("referrer_id", "")).strip()

    scores = load_scores()
    for entry in scores:
        if entry.get("user_id") == user_id:
            log_event(f"🔁 Already registered: {username} (ID: {user_id})")
            return jsonify({"status": "already_registered"})

    new_user = {
        "username": username,
        "user_id": user_id,
        "score": 0,
    }

    if referrer_id:
        new_user["referred_by"] = referrer_id

    scores.append(new_user)
    save_scores(scores)
    log_event(f"📝 Registered new user: {username} (ID: {user_id})")

    return jsonify({"status": "registered"})

@app.route("/profile")
def profile():
    user_id = request.args.get("user_id", "")
    if not user_id:
        return jsonify({"error": "Missing user ID"}), 400

    scores = load_scores()
    entry = next((e for e in scores if e["user_id"] == user_id), None)

    if not entry:
        return jsonify({"error": "User not found"}), 404

    return jsonify({
        "username": entry["username"],
        "coins": entry["score"]
    })

@app.route("/referral-history")
def referral_history():
    user_id = request.args.get("user_id", "")
    if not user_id:
        return jsonify({"error": "Missing user ID"}), 400

    scores = load_scores()
    user = next((e for e in scores if e["user_id"] == user_id), None)

    if not user:
        return jsonify({"error": "User not found"}), 404

    return jsonify(user.get("referrals", []))

@app.route("/leaderboard")
def leaderboard():
    scores = load_scores()
    sorted_scores = sorted(scores, key=lambda x: x["score"], reverse=True)[:10]
    return jsonify(sorted_scores)

@app.route("/leaderboard-page")
def leaderboard_page():
    scores = load_scores()
    sorted_scores = sorted(scores, key=lambda x: x["score"], reverse=True)[:10]
    current_user_id = request.args.get("user_id", "")

    html = """..."""  # unchanged HTML leaderboard template
    return render_template_string(html, scores=sorted_scores, current_user_id=current_user_id)

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
        <h2>🪵 Server Logs</h2>
        <div>{log_content}</div>
    </body>
    </html>
    """

if __name__ == "__main__":
    app.run(debug=True, port=5000)
