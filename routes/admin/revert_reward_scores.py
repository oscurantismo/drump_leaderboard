from flask import Blueprint, session, redirect, url_for
import json
import os
from utils.storage import load_scores, save_scores
from routes.rewards import load_rewards

revert_bp = Blueprint("revert_rewards", __name__)

@revert_bp.route("/admin/revert-reward-scores")
def revert_reward_scores():
    if not session.get("logged_in"):
        return redirect(url_for("auth_routes.login"))

    scores = load_scores()
    rewards = load_rewards()
    updated = 0

    user_map = {entry["user_id"]: entry for entry in scores}

    for reward in rewards:
        user_id = reward.get("user_id")
        change = reward.get("change", 0)
        if user_id in user_map:
            user_map[user_id]["score"] = max(0, user_map[user_id]["score"] - change)
            updated += 1

    save_scores(list(user_map.values()))

    return f"<h2>✅ Reverted scores for {updated} reward entries.</h2><p><a href='/debug-logs'>Back to debug logs</a></p>"
