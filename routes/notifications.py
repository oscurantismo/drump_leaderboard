# notifications.py
import json
import datetime
from flask import Blueprint, request, jsonify

notifications_routes = Blueprint("notifications_routes", __name__)
SUBSCRIPTION_FILE = "subscriptions.json"

def load_subscriptions():
    try:
        with open(SUBSCRIPTION_FILE, "r") as f:
            return json.load(f)
    except:
        return {}

def save_subscriptions(data):
    with open(SUBSCRIPTION_FILE, "w") as f:
        json.dump(data, f, indent=2)

@notifications_routes.route("/status", methods=["GET"])
def get_subscription_status():
    user_id = request.args.get("user_id")
    if not user_id:
        return jsonify({"error": "Missing user_id"}), 400

    subs = load_subscriptions()
    subscribed = subs.get(user_id, {}).get("subscribed", False)
    return jsonify({"subscribed": subscribed})

@notifications_routes.route("/subscribe", methods=["POST"])
def subscribe():
    data = request.get_json()
    user_id = str(data.get("user_id"))
    username = data.get("username", "unknown")

    if not user_id:
        return jsonify({"error": "Missing user_id"}), 400

    subs = load_subscriptions()

    subs[user_id] = {
        **subs.get(user_id, {}),
        "subscribed": True,
        "username": username,
        "subscribed_at": datetime.datetime.utcnow().isoformat(),
        "opted_out": False
    }

    save_subscriptions(subs)
    return jsonify({"ok": True})

@notifications_routes.route("/unsubscribe", methods=["POST"])
def unsubscribe():
    data = request.get_json()
    user_id = str(data.get("user_id"))
    if not user_id:
        return jsonify({"error": "Missing user_id"}), 400

    subs = load_subscriptions()

    if user_id in subs:
        subs[user_id]["subscribed"] = False
        subs[user_id]["opted_out"] = True

    save_subscriptions(subs)
    return jsonify({"ok": True})
