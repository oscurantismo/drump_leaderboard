from flask import Blueprint, request, jsonify, render_template_string
from utils.storage import load_scores
from utils.logging import log_event

leaderboard_routes = Blueprint("leaderboard_routes", __name__)

MAINTENANCE_MODE = True

@leaderboard_routes.route("/leaderboard")
def get_leaderboard():
    scores = load_scores()
    sorted_scores = sorted(scores, key=lambda x: x.get("score", 0), reverse=True)
    for entry in sorted_scores:
        entry["display_name"] = (
            entry.get("first_name") or
            entry.get("last_name") or
            entry.get("username") or
            "Anonymous"
        )
    return jsonify(sorted_scores)

@leaderboard_routes.route("/leaderboard-page")
def leaderboard_page():
    if MAINTENANCE_MODE:
        return render_template_string("<h1>🚧 Leaderboard Under Maintenance</h1>")

    try:
        scores = load_scores()
        filtered_scores = [s for s in scores if s.get("score", 0) > 0]
        sorted_scores = sorted(filtered_scores, key=lambda x: x["score"], reverse=True)
        current_user_id = request.args.get("user_id", "")
        total_players = len(filtered_scores)

        for entry in sorted_scores:
            entry["display_name"] = (
                entry.get("first_name") or
                entry.get("last_name") or
                entry.get("username") or
                "Anonymous"
            )

        user_index = next((i for i, e in enumerate(sorted_scores) if e.get("user_id") == current_user_id), None)
        user_rank = user_index + 1 if user_index is not None else None
        user_score = sorted_scores[user_index]["score"] if user_index is not None else 0

        if user_rank:
            if user_rank > 25:
                threshold = sorted_scores[24]["score"]
                progress_text = f"{threshold - user_score + 1} punches left to enter top-25"
            elif user_rank > 1:
                threshold = sorted_scores[user_index - 1]["score"]
                progress_text = f"{threshold - user_score + 1} punches left to reach top-{user_rank - 1}"
            else:
                progress_text = "You're #1! 🏆"
        else:
            progress_text = "Punch more to enter the top-25!"

        movement_history = []
        if user_rank:
            if user_rank <= 25:
                movement_history.append("⬆️ Entered top-25: +250 punches")
            if user_rank <= 10:
                movement_history.append("⬆️ Entered top-10: +550 punches")
            if user_rank == 3:
                movement_history.append("⬆️ Entered top-3: +1000 punches")
            if user_rank == 2:
                movement_history.append("⬆️ Entered top-2: +2000 punches")
            if user_rank == 1:
                movement_history.append("⬆️ Entered top-1: +4000 punches")

        return render_template_string(modern_leaderboard_template,
                                      scores=sorted_scores[:25],
                                      current_user_id=current_user_id,
                                      total_players=total_players,
                                      user_rank=user_rank,
                                      progress_text=progress_text,
                                      movement_history=movement_history)
    except Exception as e:
        log_event(f"❌ Leaderboard crash: {e}")
        return render_template_string("<h1>🚧 Leaderboard Under Maintenance</h1>")
