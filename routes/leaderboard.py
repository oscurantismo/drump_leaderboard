from flask import Blueprint, request, jsonify, render_template
from utils.storage import load_scores
from utils.logging import log_event
from routes.rewards import log_reward_event, _load as load_reward_ledger

leaderboard_routes = Blueprint("leaderboard_routes", __name__)

MAINTENANCE_MODE = False
ENABLE_REWARD_ISSUING = False

@leaderboard_routes.route("/leaderboard-page")
def leaderboard_page():
    try:
        scores = load_scores()
        filtered = [s for s in scores if s.get("score", 0) > 0]
        sorted_scores = sorted(filtered, key=lambda x: x["score"], reverse=True)
        current_uid = request.args.get("user_id", "")
        total_players = len(scores)

        for e in sorted_scores:
            e["display_name"] = e.get("first_name") or e.get("last_name") or e.get("username") or "Anonymous"

        user_index = next((i for i, e in enumerate(sorted_scores) if e.get("user_id") == current_uid), None)
        user_rank = user_index + 1 if user_index is not None else None
        user_score = sorted_scores[user_index]["score"] if user_index is not None else 0

        top_first = sorted_scores[0] if len(sorted_scores) > 0 else None
        top_second = sorted_scores[1] if len(sorted_scores) > 1 else None
        top_third = sorted_scores[2] if len(sorted_scores) > 2 else None

        return render_template(
            "leaderboard.html",
            scores=sorted_scores,
            current_user_id=current_uid,
            total_players=total_players,
            user_rank=user_rank,
            top_first=top_first,
            top_second=top_second,
            top_third=top_third,
        )

    except Exception as e:
        log_event(f"❌ Leaderboard crash: {e}")
        return "<h2>🚧 Leaderboard under maintenance</h2>", 500

@leaderboard_routes.route("/leaderboard-list")
def get_leaderboard_list():
    try:
        scores = load_scores()
        filtered = [s for s in scores if s.get("score", 0) > 0]
        sorted_scores = sorted(filtered, key=lambda x: x["score"], reverse=True)
        return jsonify(sorted_scores)
    except Exception as e:
        log_event(f"❌ Error in /leaderboard-list: {e}")
        return jsonify({"error": "Leaderboard list fetch failed"}), 500


@leaderboard_routes.route("/leaderboard")
def get_leaderboard_data():
    try:
        scores = load_scores()
        user_id = request.args.get("user_id", "")
        filtered = [s for s in scores if s.get("score", 0) > 0]
        sorted_scores = sorted(filtered, key=lambda x: x["score"], reverse=True)

        user_index = next((i for i, s in enumerate(sorted_scores) if s.get("user_id") == user_id), None)
        user_rank = user_index + 1 if user_index is not None else None
        user_score = sorted_scores[user_index]["score"] if user_index is not None else 0

        next_score = None
        punch_gap = 0

        if user_index is not None and user_index > 0:
            next_score = sorted_scores[user_index - 1]["score"]
            punch_gap = max(0, next_score - user_score)

        response = {
            "user_id": user_id,
            "rank": user_rank,
            "score": user_score,
            "punches_to_next_rank": punch_gap
        }

        return jsonify(response)

    except Exception as e:
        log_event(f"❌ Error in /leaderboard JSON: {e}")
        return jsonify({"error": "Leaderboard fetch failed"}), 500
