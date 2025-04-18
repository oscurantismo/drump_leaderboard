# routes/rewards.py
"""
Central reward ledger for Drump | Punch2Earn

Every reward‑granting feature (currently social‑tasks) should call
log_reward_event() so we have a canonical audit trail.
"""

import os, json
from datetime import datetime
from flask import Blueprint, request, jsonify, session
from utils.logging import log_event  # ✅ Logging to logs.txt

rewards_bp = Blueprint("rewards", __name__)
REWARDS_FILE = "rewards.json"

# ---------- Ensure rewards.json exists ----------------------------------- #
def ensure_rewards_file():
    if not os.path.exists(REWARDS_FILE):
        with open(REWARDS_FILE, "w") as f:
            json.dump([], f)
        print("✅ Created rewards.json")
        log_event("✅ Created rewards.json")

# ---------- helpers ------------------------------------------------------- #
def _load() -> list[dict]:
    ensure_rewards_file()
    try:
        with open(REWARDS_FILE, "r") as f:
            return json.load(f)
    except json.JSONDecodeError:
        log_event("❌ Failed to decode rewards.json")
        return []

def _save(data: list[dict]) -> None:
    with open(REWARDS_FILE, "w") as f:
        json.dump(data, f, indent=2)

# ---------- public function ---------------------------------------------- #
def log_reward_event(
    *,
    user_id: str,
    username: str,
    reward_type: str,          # e.g. "task_complete"
    source_id: str,            # e.g. task_id
    change: int,
    prev_score: int,
    new_score: int,
    meta: dict | None = None,
) -> None:
    """Append a reward entry unless an identical one already exists."""
    ledger = _load()

    # TEMP: comment this out to test
    duplicate = any(
        e["user_id"] == user_id and
        e["reward_type"] == reward_type and
        e["source_id"] == source_id
        for e in ledger
    )
    if duplicate:
        print(f"⚠️ Skipped duplicate reward for {username} ({user_id}) – {reward_type}:{source_id}")
        log_event(f"⚠️ Duplicate reward not logged for {username} ({user_id}) – {reward_type}:{source_id}")
        return

    reward_entry = {
        "timestamp": datetime.utcnow().isoformat(timespec="seconds") + "Z",
        "user_id": user_id,
        "username": username,
        "reward_type": reward_type,
        "source_id": source_id,
        "change": change,
        "prev_score": prev_score,
        "new_score": new_score,
        "meta": meta or {},
    }

    ledger.append(reward_entry)
    _save(ledger)

    print(f"💾 Logged reward for {username} ({user_id}) – {reward_type}:{source_id}")
    log_event(f"💾 Logged reward: {reward_type}:{source_id} for {username} ({user_id}) | Δ {change} → {new_score}")

# ---------- API endpoints (debug / backup) ------------------------------- #
@rewards_bp.route("/rewards", methods=["GET"])
def list_rewards():
    return jsonify(_load())

@rewards_bp.route("/rewards/backup", methods=["GET"])
def download_backup():
    if not os.path.exists(REWARDS_FILE):
        return "No rewards log found.", 404
    return (
        open(REWARDS_FILE).read(),
        200,
        {
            "Content-Disposition": "attachment; filename=rewards_backup.json",
            "Content-Type": "application/json",
        },
    )

@rewards_bp.route("/rewards/replace", methods=["POST"])
def replace_backup():
    if not session.get("logged_in"):
        return jsonify({"error": "unauthorized"}), 401
    try:
        data = request.get_json(force=True)
        _save(data)
        return jsonify({"status": "replaced", "entries": len(data)})
    except Exception as e:
        return jsonify({"error": str(e)}), 400

# ---------- Manual init endpoint (Railway friendly) ---------------------- #
@rewards_bp.route("/rewards/init", methods=["POST"])
def init_rewards_file():
    try:
        if not os.path.exists(REWARDS_FILE):
            with open(REWARDS_FILE, "w") as f:
                json.dump([], f)
            log_event("✅ rewards.json created via /rewards/init")
            return jsonify({"status": "created"})
        return jsonify({"status": "already_exists"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
