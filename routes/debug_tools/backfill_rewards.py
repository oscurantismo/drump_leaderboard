from flask import Blueprint
from utils.storage import load_scores, save_scores
from routes.rewards import load_rewards, log_reward_event

backfill_bp = Blueprint("backfill_rewards", __name__)

@backfill_bp.route("/admin/backfill-rewards")
def backfill_rewards():
    reward_tiers = [
        ("Entered top-1", 1, 4000),
        ("Entered top-2", 2, 2000),
        ("Entered top-3", 3, 1000),
        ("Entered top-10", 10, 550),
        ("Entered top-25", 25, 250),
    ]

    scores = load_scores()
    sorted_scores = sorted(scores, key=lambda x: x.get("score", 0), reverse=True)
    existing = load_rewards()
    issued = {(r["user_id"], r["event"]) for r in existing}

    changes = []
    updated = False

    for rank, player in enumerate(sorted_scores, start=1):
        user_id = player.get("user_id")
        if not user_id:
            continue

        username = (
            player.get("first_name") or
            player.get("last_name") or
            player.get("username") or
            "Anonymous"
        )

        for label, threshold, bonus in reward_tiers:
            if rank <= threshold and (user_id, label) not in issued:
                player["score"] = player.get("score", 0) + bonus
                log_reward_event(user_id, username, label, bonus)
                issued.add((user_id, label))
                updated = True
                changes.append(f"✅ {username} (Rank {rank}): {label} +{bonus} punches")

    if updated:
        save_scores(sorted_scores)

    if not changes:
        return "<h3>✅ All rewards already issued. No changes made.</h3>"

    return f"""
    <h2>🎁 Reward Backfill Complete</h2>
    <ul>{"".join(f"<li>{c}</li>" for c in changes)}</ul>
    <p><b>{len(changes)}</b> rewards issued and scores updated.</p>
    """
