# routes/tasks.py
"""
🪄  Social‑task rewards for Drump | Punch2Earn
------------------------------------------------
•  Exposes 2 endpoints:
   GET    /tasks           → list tasks + completion state for this user
   POST   /tasks/complete  → mark task done, add punches if not yet done
•  Verification: true follow / retweet checks need external APIs &
   OAuth scopes; for now we simply trust the front‑end click‑through.
"""

from flask import Blueprint, request, jsonify
from utils.storage import load_scores, save_scores
from utils.logging import log_event
from routes.rewards import log_reward_event  # NEW

tasks_routes = Blueprint("tasks_routes", __name__)

# --- master task list (must match earn_tab.js) -----------------------------
TASK_DEFINITIONS = {
    "follow_x":        {"title": "Follow us on X",                   "reward": 40},
    "like_pinned_v2": {"title": "Like our pinned tweet", "reward": 25},
    "retweet_pinned":  {"title": "Re‑post pinned tweet",             "reward": 35},
    "quote_tweet":     {"title": "Quote‑tweet with #Punch2Earn",     "reward": 60},
    "join_channel":    {"title": "Join our Telegram channel",        "reward": 25},
    "join_group":      {"title": "Join the community chat",          "reward": 30},
    "share_game_tg":   {"title": "Share the game with a friend",     "reward": 50},
    "invite_friend_tg":{"title": "Invite a friend to the chat",      "reward": 100},
    "twitter_space":   {"title": "Join our next Twitter Space",      "reward": 130},
}

# --------------------------------------------------------------------------
def _get_user_entry(user_id: str, scores: list[dict]) -> dict | None:
    for e in scores:
        if e.get("user_id") == user_id:
            e.setdefault("tasks_done", [])
            return e
    return None

# === GET /tasks ===========================================================
@tasks_routes.route("/tasks", methods=["GET"])
def list_tasks():
    """Return all tasks and whether current user completed them."""
    user_id = (request.args.get("user_id") or "").strip()
    if not user_id:
        return jsonify({"error": "user_id query param required"}), 400

    scores = load_scores()
    entry = _get_user_entry(user_id, scores)
    done = set(entry["tasks_done"]) if entry else set()

    return jsonify([
        {
            "id": tid,
            "title": meta["title"],
            "reward": meta["reward"],
            "done": tid in done,
        }
        for tid, meta in TASK_DEFINITIONS.items()
    ])

# === POST /tasks/complete ==================================================
@tasks_routes.route("/tasks/complete", methods=["POST"])
def complete_task():
    data = request.get_json(force=True)
    user_id = str(data.get("user_id", "")).strip()
    task_id = str(data.get("task_id", "")).strip()

    if not user_id or task_id not in TASK_DEFINITIONS:
        return jsonify({"error": "invalid user_id or task_id"}), 400

    scores = load_scores()
    user = _get_user_entry(user_id, scores)
    if not user:
        return jsonify({"error": "user not registered"}), 404

    if task_id in user["tasks_done"]:
        return jsonify({"status": "already_completed"})

    # --- apply reward ---------------------------------------------------- #
    reward = TASK_DEFINITIONS[task_id]["reward"]
    prev = user.get("score", 0)
    new = prev + reward

    user["tasks_done"].append(task_id)
    user["score"] = new
    save_scores(scores)

    # --- diagnostic log before reward logging ---------------------------- #
    log_event(f"📡 REACHED log_reward_event for user {user_id}, task {task_id}")
    print(f"📡 REACHED log_reward_event for user {user.get('username', 'Anonymous')} ({user_id}), task {task_id}")

    # --- log to central ledger ------------------------------------------ #
    log_reward_event(
        user_id=user_id,
        username=user.get("username", "Anonymous"),
        reward_type="task_complete",
        source_id=task_id,
        change=reward,
        prev_score=prev,
        new_score=new,
        meta={"task_title": TASK_DEFINITIONS[task_id]["title"]},
    )

    # Log to terminal and logs.txt
    print(f"📝 Logging reward for {user.get('username', 'Anonymous')} ({user_id}) – task_complete:{task_id}")
    log_event(f"🎁 Logged reward for {user.get('username', 'Anonymous')} ({user_id}) – task_complete:{task_id}")

    return jsonify({"status": "ok", "new_score": new, "reward": reward})
