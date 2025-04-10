from flask import Blueprint, session, redirect, url_for
from utils.storage import load_scores, save_scores
from routes.rewards import load_rewards
import json

revert_bp = Blueprint("revert_rewards", __name__)

@revert_bp.route("/admin/revert-reward-scores")
def revert_reward_scores():
    if not session.get("logged_in"):
        return redirect(url_for("auth_routes.login"))

    scores = load_scores()
    rewards = load_rewards()

    updated = 0
    user_map = {str(entry["user_id"]): entry for entry in scores if "user_id" in entry}

    for reward in rewards:
        user_id = str(reward.get("user_id", "")).strip()
        change = int(reward.get("change", 0))

        if user_id in user_map:
            entry = user_map[user_id]
            original_score = int(entry.get("score", 0))
            new_score = max(0, original_score - change)

            if new_score != original_score:
                entry["score"] = new_score
                updated += 1

    save_scores(list(user_map.values()))

    return f"""
    <h2>✅ Reverted rewards for {updated} users.</h2>
    <p><a href='/debug-logs'>⬅ Back to Debug Logs</a></p>
    """
