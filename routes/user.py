from flask import Blueprint, request, jsonify
from utils.storage import load_scores, save_scores, backup_scores
from utils.logging import log_event
import datetime
from routes.debug_tools.subscriptions import load_subscriptions, save_subscriptions

user_routes = Blueprint("user_routes", __name__)

@user_routes.route("/register", methods=["POST"])
def register():
    data = request.get_json()
    username = (data.get("username") or "Anonymous").strip()
    first_name = (data.get("first_name") or "").strip()
    last_name = (data.get("last_name") or "").strip()
    user_id = str(data.get("user_id", "")).strip()
    referrer_id = str(data.get("referrer_id", "")).strip()

    scores = load_scores()
    for entry in scores:
        if entry.get("user_id") == user_id:
            log_event(f"🔁 Already registered: {username} (ID: {user_id})")
            return jsonify({"status": "already_registered"})

    new_user = {
        "username": username,
        "first_name": first_name,
        "last_name": last_name,
        "user_id": user_id,
        "score": 0,
        "registered_at": datetime.datetime.now().isoformat()
    }

    if referrer_id:
        new_user["referred_by"] = referrer_id
        log_event(f"🧾 {username} was referred by {referrer_id}")

    scores.append(new_user)
    save_scores(scores)
    backup_scores()
    log_event(f"📝 Registered new user: {username} (ID: {user_id})")
    return jsonify({"status": "registered"})


from collections import defaultdict, deque
import time

submission_times = {}  # Tracks last submission time per user
user_activity = defaultdict(lambda: deque(maxlen=50))  # Store recent taps

@user_routes.route("/submit", methods=["POST"])
def submit():
    data = request.get_json()
    username = (data.get("username") or "Anonymous").strip()
    first_name = (data.get("first_name") or "").strip()
    last_name = (data.get("last_name") or "").strip()
    user_id = str(data.get("user_id", "")).strip()
    score = max(0, int(data.get("score", 0)))

    now = time.time()

    # === Bot Detection ===
    last_time = submission_times.get(user_id)
    submission_times[user_id] = now
    if last_time:
        interval = now - last_time
        if interval < 0.2:
            log_event(f"⚠️ Suspiciously fast tap: {username} (ID: {user_id}) – {interval:.3f}s")

    user_activity[user_id].append(now)
    recent_taps = [t for t in user_activity[user_id] if now - t <= 10]
    if len(recent_taps) > 30:
        log_event(f"🚨 High-frequency activity: {username} (ID: {user_id}) – {len(recent_taps)} taps in 10s")

    log_event(f"🔄 Score submitted: {username} (ID: {user_id}) – {score}")

    scores = load_scores()
    updated = False

    for entry in scores:
        if entry.get("user_id") == user_id:
            old_score = entry["score"]
            if score > old_score:
                entry["score"] = score
                entry["username"] = username
                entry["first_name"] = first_name
                entry["last_name"] = last_name

                # 🎯 Bonus for 100s milestone
                if score % 100 == 0:
                    entry["score"] += 25
                    log_event(f"🎯 Milestone reached: {score} → +25 bonus punches for {username}")

                # 🎁 Referral reward
                referrer_id = entry.get("referred_by")
                if old_score < 20 <= score and referrer_id and not entry.get("referral_reward_issued"):
                    referrer = next((e for e in scores if e["user_id"] == referrer_id), None)
                    if referrer:
                        reward = 1000
                        referrer_old = referrer["score"]
                        referred_old = entry["score"]

                        existing_referral = any(
                            r.get("ref_user_id") == user_id for r in referrer.get("referrals", [])
                        )

                        if not existing_referral:
                            referrer["score"] += reward
                            entry["score"] += reward
                            entry["referral_reward_issued"] = True
                            entry["referral_reward_time"] = datetime.datetime.now().isoformat()

                            if "referrals" not in referrer:
                                referrer["referrals"] = []

                            referrer["referrals"].append({
                                "ref_user_id": user_id,
                                "ref_username": username,
                                "ref_first_name": first_name,
                                "ref_last_name": last_name,
                                "timestamp": entry["referral_reward_time"],
                                "reward": reward,
                                "before_score": referrer_old,
                                "after_score": referrer["score"]
                            })

                            log_event(f"🎉 Referral bonus issued: {referrer['username']} and {username} +{reward} each at 20 punches")
                        else:
                            log_event(f"⛔ Duplicate referral ignored: {referrer['username']} already rewarded for referring {username}")

                log_event(f"✅ Updated score for {username} (ID: {user_id}) to {entry['score']}")
            updated = True
            break

    if not updated:
        scores.append({
            "username": username,
            "first_name": first_name,
            "last_name": last_name,
            "user_id": user_id,
            "score": score,
            "registered_at": datetime.datetime.now().isoformat()
        })
        log_event(f"🆕 New user added: {username} (ID: {user_id}) with score {score}")

    save_scores(scores)
    return jsonify({"status": "ok"})

@user_routes.route("/profile")
def profile():
    user_id = request.args.get("user_id", "")
    if not user_id:
        return jsonify({"error": "Missing user ID"}), 400

    scores = load_scores()
    entry = next((e for e in scores if e["user_id"] == user_id), None)

    if not entry:
        return jsonify({"error": "User not found"}), 404

    return jsonify({
        "username": entry["username"],
        "first_name": entry.get("first_name", ""),
        "last_name": entry.get("last_name", ""),
        "punches": entry["score"],
        "already_claimed_referral": bool(entry.get("referral_reward_issued", False)),
        "referrals": entry.get("referrals", [])
    })

@user_routes.route("/notifications/subscribe", methods=["POST"])
def subscribe_notifications():
    data = request.get_json(force=True)
    user_id = str(data.get("user_id", "")).strip()
    username = data.get("username", "Anonymous")

    scores = load_scores()
    user = next((e for e in scores if e["user_id"] == user_id), None)
    if not user:
        return jsonify({"error": "User not found"}), 404

    user["subscribed_notifications"] = True
    save_scores(scores)

    subs = load_subscriptions()
    subs[user_id] = {
        "username": username,
        "subscribed": True,
        "subscribed_at": datetime.datetime.now().isoformat(),
        "opted_out": False
    }
    save_subscriptions(subs)

    log_event(f"🔔 Subscribed to notifications: {username} ({user_id})")
    return jsonify({"status": "subscribed"})


@user_routes.route("/notifications/unsubscribe", methods=["POST"])
def unsubscribe_notifications():
    data = request.get_json(force=True)
    user_id = str(data.get("user_id", "")).strip()

    scores = load_scores()
    user = next((e for e in scores if e["user_id"] == user_id), None)
    if not user:
        return jsonify({"error": "User not found"}), 404

    user["subscribed_notifications"] = False
    save_scores(scores)

    subs = load_subscriptions()
    subs[user_id] = {
        **subs.get(user_id, {}),
        "subscribed": False,
        "opted_out": True
    }
    save_subscriptions(subs)

    log_event(f"🔕 Unsubscribed from notifications: {user.get('username')} ({user_id})")
    return jsonify({"status": "unsubscribed"})


@user_routes.route("/notifications/status", methods=["GET"])
def check_notification_status():
    user_id = request.args.get("user_id", "").strip()
    scores = load_scores()
    user = next((e for e in scores if e["user_id"] == user_id), None)

    if not user:
        return jsonify({"error": "User not found"}), 404

    return jsonify({
        "subscribed": bool(user.get("subscribed_notifications", False))
    })
