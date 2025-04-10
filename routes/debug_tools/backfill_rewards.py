from utils.storage import load_scores, save_scores
from routes.rewards import load_rewards, log_reward_event

# Define reward tiers
reward_tiers = [
    ("Entered top-1", 1, 4000),
    ("Entered top-2", 2, 2000),
    ("Entered top-3", 3, 1000),
    ("Entered top-10", 10, 550),
    ("Entered top-25", 25, 250),
]

# Load leaderboard scores
scores = load_scores()
sorted_scores = sorted(scores, key=lambda x: x.get("score", 0), reverse=True)

# Load already issued rewards
existing_rewards = load_rewards()
issued = {(r["user_id"], r["event"]) for r in existing_rewards}

# Track changes for saving
score_updated = False

for rank, player in enumerate(sorted_scores, start=1):
    user_id = player.get("user_id")
    if not user_id:
        continue  # skip incomplete records

    username = (
        player.get("first_name") or
        player.get("last_name") or
        player.get("username") or
        "Anonymous"
    )

    for label, threshold, bonus in reward_tiers:
        if rank <= threshold and (user_id, label) not in issued:
            # Add reward to user's score
            current_score = player.get("score", 0)
            player["score"] = current_score + bonus
            score_updated = True

            # Log the reward
            log_reward_event(user_id, username, label, bonus)
            print(f"✅ Issued {label} to {username} (Rank {rank}) — +{bonus} punches")

# Save modified scores only if updated
if score_updated:
    save_scores(sorted_scores)
    print("💾 Updated scores saved.")
else:
    print("✅ No new rewards were issued.")
