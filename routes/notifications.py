# notifications.py
import json
from flask import Blueprint, request, jsonify

notifications_routes = Blueprint("notifications_routes", __name__)

@notifications_routes.route("/subscribe", methods=["POST"])
def toggle_subscription():
    data = request.get_json()
    user_id = str(data.get("user_id"))
    subscribe = bool(data.get("subscribe"))

    try:
        with open("subscriptions.json", "r") as f:
            subs = json.load(f)
    except:
        subs = {}

    subs[user_id] = {"subscribed": subscribe}

    with open("subscriptions.json", "w") as f:
        json.dump(subs, f, indent=2)

    return jsonify({"ok": True})
