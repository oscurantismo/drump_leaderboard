# notifications.py
import json
from flask import Blueprint, request, jsonify

notifications_routes = Blueprint("notifications_routes", __name__)

@notifications_routes.route("/status", methods=["GET"])
def get_subscription_status():
    user_id = request.args.get("user_id")
    if not user_id:
        return jsonify({"error": "Missing user_id"}), 400

    try:
        with open("subscriptions.json", "r") as f:
            subs = json.load(f)
    except:
        subs = {}

    subscribed = subs.get(user_id, {}).get("subscribed", False)
    return jsonify({"subscribed": subscribed})


@notifications_routes.route("/subscribe", methods=["POST"])
def subscribe():
    data = request.get_json()
    user_id = str(data.get("user_id"))
    if not user_id:
        return jsonify({"error": "Missing user_id"}), 400

    try:
        with open("subscriptions.json", "r") as f:
            subs = json.load(f)
    except:
        subs = {}

    subs[user_id] = {**subs.get(user_id, {}), "subscribed": True}
    with open("subscriptions.json", "w") as f:
        json.dump(subs, f, indent=2)

    return jsonify({"ok": True})


@notifications_routes.route("/unsubscribe", methods=["POST"])
def unsubscribe():
    data = request.get_json()
    user_id = str(data.get("user_id"))
    if not user_id:
        return jsonify({"error": "Missing user_id"}), 400

    try:
        with open("subscriptions.json", "r") as f:
            subs = json.load(f)
    except:
        subs = {}

    subs[user_id] = {**subs.get(user_id, {}), "subscribed": False}
    with open("subscriptions.json", "w") as f:
        json.dump(subs, f, indent=2)

    return jsonify({"ok": True})

