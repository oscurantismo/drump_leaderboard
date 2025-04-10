import os
import json
import fcntl
import time
from .logging import log_event

SCORES_FILE = "/app/data/scores.json"
BACKUP_FOLDER = "/app/data/backups"
_last_backup_time = 0

def ensure_file():
    if not os.path.exists(SCORES_FILE):
        os.makedirs(os.path.dirname(SCORES_FILE), exist_ok=True)
        with open(SCORES_FILE, "w") as f:
            json.dump([], f)
        log_event("✅ Created new scores.json")

def load_scores():
    ensure_file()
    with open(SCORES_FILE, "r") as f:
        try:
            fcntl.flock(f, fcntl.LOCK_SH)
            data = json.load(f)
            fcntl.flock(f, fcntl.LOCK_UN)
            return data
        except json.JSONDecodeError as e:
            log_event(f"❌ Failed to decode scores.json: {e} (Path: {SCORES_FILE})")

    # 🔁 Try auto-restore from latest good backup, including manual
    try:
        backups = sorted([
            f for f in os.listdir(BACKUP_FOLDER)
            if f.endswith(".json")
        ], reverse=True)

        for backup_file in backups:
            path = os.path.join(BACKUP_FOLDER, backup_file)
            try:
                with open(path, "r") as b:
                    data = json.load(b)
                with open(SCORES_FILE, "w") as w:
                    json.dump(data, w, indent=2)
                log_event(f"♻️ Restored scores.json from backup: {backup_file}")
                return data
            except Exception as inner:
                log_event(f"⚠️ Skipped invalid backup {backup_file}: {inner}")
    except Exception as outer:
        log_event(f"❌ Failed to restore from backup: {outer}")

    return []

def save_scores(scores):
    temp_path = SCORES_FILE + ".tmp"
    with open(temp_path, "w") as f:
        fcntl.flock(f, fcntl.LOCK_EX)
        json.dump(scores, f, indent=2)
        f.flush()
        os.fsync(f.fileno())
        fcntl.flock(f, fcntl.LOCK_UN)
    os.replace(temp_path, SCORES_FILE)

def backup_scores(tag=None):
    global _last_backup_time
    now = time.time()

    if now - _last_backup_time < 60 and tag is None:
        log_event("⏳ Skipping backup (too soon after last one)")
        return

    _last_backup_time = now
    os.makedirs(BACKUP_FOLDER, exist_ok=True)
    from datetime import datetime
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    suffix = f"_{tag}" if tag else ""
    backup_path = os.path.join(BACKUP_FOLDER, f"leaderboard_backup_{timestamp}{suffix}.json")
    scores = load_scores()
    with open(backup_path, "w") as f:
        json.dump(scores, f, indent=2)
    log_event(f"💾 Backup saved: {backup_path}")
