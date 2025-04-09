import os
import json
from datetime import datetime
from flask import Blueprint, request, jsonify

rewards_bp = Blueprint("rewards", __name__)

REWARDS_FILE = "rewards.json"

def log_reward_event(user_id, username, event, change):
    data = load_rewards()
    entry = {
        "user_id": user_id,
        "username": username,
        "event": event,
        "change": change,
        "timestamp": datetime.utcnow().isoformat()
    }
    data.append(entry)
    with open(REWARDS_FILE, "w") as f:
        json.dump(data, f, indent=2)

def load_rewards():
    if not os.path.exists(REWARDS_FILE):
        return []
    with open(REWARDS_FILE, "r") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return []

@rewards_bp.route("/rewards", methods=["GET"])
def get_all_rewards():
    return jsonify(load_rewards())

@rewards_bp.route("/rewards/backup", methods=["GET"])
def download_rewards_backup():
    if not os.path.exists(REWARDS_FILE):
        return "No rewards log found.", 404
    with open(REWARDS_FILE, "r") as f:
        return f.read(), 200, {
            "Content-Disposition": "attachment; filename=rewards_backup.json",
            "Content-Type": "application/json"
        }

@rewards_bp.route("/rewards/replace", methods=["POST"])
def replace_rewards_backup():
    try:
        data = request.get_json()
        with open(REWARDS_FILE, "w") as f:
            json.dump(data, f, indent=2)
        return jsonify({"status": "replaced", "entries": len(data)})
    except Exception as e:
        return jsonify({"error": str(e)}), 400
