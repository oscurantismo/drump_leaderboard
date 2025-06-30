# notifications.py
import json
from flask import Blueprint, request, jsonify
from utils import utc_timestamp

notifications_routes = Blueprint("notifications_routes", __name__)
SUBSCRIPTION_PATH = "subscriptions.json"

def load_subs():
    try:
        with open(SUBSCRIPTION_PATH, "r") as f:
            return json.load(f)
    except:
        return {}

def save_subs(data):
    with open(SUBSCRIPTION_PATH, "w") as f:
        json.dump(data, f, indent=2)

@notifications_routes.route("/status", methods=["GET"])
def get_subscription_status():
    user_id = request.args.get("user_id")
    if not user_id:
        return jsonify({"error": "Missing user_id"}), 400

    subs = load_subs()
    subscribed = subs.get(user_id, {}).get("subscribed", False)
    return jsonify({"subscribed": subscribed})

@notifications_routes.route("/subscribe", methods=["POST"])
def subscribe():
    data = request.get_json()
    user_id = str(data.get("user_id"))
    username = data.get("username", "unknown")

    if not user_id:
        return jsonify({"error": "Missing user_id"}), 400

    try:
        with open("subscriptions.json", "r") as f:
            subs = json.load(f)
    except:
        subs = {}

    subs[user_id] = {
        **subs.get(user_id, {}),
        "subscribed": True,
        "username": username,
        "subscribed_at": utc_timestamp()
    }

    with open("subscriptions.json", "w") as f:
        json.dump(subs, f, indent=2)

    return jsonify({"ok": True})


@notifications_routes.route("/unsubscribe", methods=["POST"])
def unsubscribe():
    data = request.get_json()
    user_id = str(data.get("user_id"))
    username = data.get("username", "Anonymous")
    if not user_id:
        return jsonify({"error": "Missing user_id"}), 400

    subs = load_subs()
    subs[user_id] = {
        **subs.get(user_id, {}),
        "subscribed": False,
        "username": username,
        "opted_out": True
    }
    save_subs(subs)
    return jsonify({"ok": True})
