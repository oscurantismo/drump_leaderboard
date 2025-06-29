import os
import json
import fcntl
import time
import threading
import hashlib
from datetime import datetime
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

    # 🔁 Try auto-restore from latest good backup (based on modification time)
    try:
        backups = sorted([
            os.path.join(BACKUP_FOLDER, f)
            for f in os.listdir(BACKUP_FOLDER)
            if f.endswith(".json")
        ], key=os.path.getmtime, reverse=True)

        for backup_path in backups:
            try:
                with open(backup_path, "r") as b:
                    data = json.load(b)
                with open(SCORES_FILE, "w") as w:
                    json.dump(data, w, indent=2)
                log_event(f"♻️ Restored scores.json from backup: {os.path.basename(backup_path)}")
                return data
            except Exception as inner:
                log_event(f"⚠️ Skipped invalid backup {os.path.basename(backup_path)}: {inner}")
    except Exception as outer:
        log_event(f"❌ Failed to restore from backup: {outer}")

    return []

def save_scores(scores):
    if not validate_scores(scores):
        log_event("❌ Invalid scores format — skipping save.")
        return

    os.makedirs(os.path.dirname(SCORES_FILE), exist_ok=True)

    try:
        with open(SCORES_FILE, "w") as f:
            json.dump(scores, f, indent=2)
            f.flush()
            os.fsync(f.fileno())
        log_event("✅ Successfully saved scores.json")
    except Exception as e:
        log_event(f"❌ Failed to save scores.json: {e}")

def get_file_hash(path):
    try:
        with open(path, "rb") as f:
            return hashlib.md5(f.read()).hexdigest()
    except Exception:
        return None

def backup_scores(tag=None):
    global _last_backup_time
    now = time.time()

    if now - _last_backup_time < 60 and tag is None:
        log_event("⏳ Skipping backup (too soon after last one)")
        return

    _last_backup_time = now
    os.makedirs(BACKUP_FOLDER, exist_ok=True)
    scores = load_scores()

    current_hash = get_file_hash(SCORES_FILE)
    latest_backup = sorted([
        os.path.join(BACKUP_FOLDER, f)
        for f in os.listdir(BACKUP_FOLDER)
        if f.endswith(".json")
    ], key=os.path.getmtime, reverse=True)

    if latest_backup:
        latest_path = latest_backup[0]
        if get_file_hash(latest_path) == current_hash and tag is None:
            log_event("🟡 Skipping backup — no changes since last snapshot.")
            return

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    suffix = f"_{tag}" if tag else ""
    backup_path = os.path.join(BACKUP_FOLDER, f"leaderboard_backup_{timestamp}{suffix}.json")

    try:
        with open(backup_path, "w") as f:
            json.dump(scores, f, indent=2)
        log_event(f"💾 Backup saved: {backup_path}")
    except Exception as e:
        log_event(f"❌ Failed to write backup file: {e}")

# ------------------ Scheduled Backups ------------------
def periodic_backup(interval_hours=6):
    while True:
        try:
            backup_scores()
        except Exception as e:
            log_event(f"❌ Scheduled backup error: {e}")
        time.sleep(interval_hours * 3600)

# ✅ Launch background scheduler at runtime
threading.Thread(target=periodic_backup, daemon=True).start()
