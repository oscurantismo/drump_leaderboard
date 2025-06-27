import os
import json
import fcntl
import time
from .logging import log_event

SCORES_FILE = "/app/data/scores.json"
BACKUP_FOLDER = "/app/data/backups"
_last_backup_time = 0

# --------------------- Validators ---------------------
def validate_scores(scores):
    if not isinstance(scores, list):
        return False
    for entry in scores:
        if not isinstance(entry, dict):
            return False
        if "user_id" not in entry or not isinstance(entry["user_id"], str):
            return False
        if "score" in entry and not isinstance(entry["score"], int):
            return False
        if "tasks_done" in entry and not isinstance(entry["tasks_done"], list):
            return False
    return True

# --------------------- File I/O ------------------------
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
            content = f.read()
            fcntl.flock(f, fcntl.LOCK_UN)

            if not content.strip():
                raise json.JSONDecodeError("File is empty", content, 0)

            return json.loads(content)
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
    if not validate_scores(scores):
        log_event("❌ Invalid scores format — skipping save.")
        return

    temp_path = SCORES_FILE + ".tmp"
    try:
        with open(temp_path, "w") as f:
            fcntl.flock(f, fcntl.LOCK_EX)
            json.dump(scores, f, indent=2)
            f.flush()
            os.fsync(f.fileno())
            fcntl.flock(f, fcntl.LOCK_UN)
        os.replace(temp_path, SCORES_FILE)
        time.sleep(0.1)  # allow disk IO to settle
    except Exception as e:
        log_event(f"❌ Failed to save scores.json safely: {e}")

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
