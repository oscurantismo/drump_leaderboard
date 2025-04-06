import os
import json
import fcntl
from .logging import log_event

DATA_FILE = "/app/data/scores.json"
BACKUP_FOLDER = "/app/data/backups"

def ensure_file():
    if not os.path.exists(DATA_FILE):
        os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
        with open(DATA_FILE, "w") as f:
            json.dump([], f)
        log_event("✅ Created new scores.json")

def load_scores():
    ensure_file()
    with open(DATA_FILE, "r") as f:
        try:
            # Obtain a shared lock for reading
            fcntl.flock(f, fcntl.LOCK_SH)
            data = json.load(f)
            # Release the lock
            fcntl.flock(f, fcntl.LOCK_UN)
            return data
        except json.JSONDecodeError as e:
            log_event(f"❌ Failed to decode JSON: {e}")
            return []

def save_scores(scores):
    temp_path = DATA_FILE + ".tmp"
    # Write to a temporary file first with an exclusive lock
    with open(temp_path, "w") as f:
        fcntl.flock(f, fcntl.LOCK_EX)
        json.dump(scores, f, indent=2)
        f.flush()
        os.fsync(f.fileno())
        fcntl.flock(f, fcntl.LOCK_UN)
    # Atomically replace the original file with the temporary file
    os.replace(temp_path, DATA_FILE)

def backup_scores():
    os.makedirs(BACKUP_FOLDER, exist_ok=True)
    from datetime import datetime
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = os.path.join(BACKUP_FOLDER, f"leaderboard_backup_{timestamp}.json")
    scores = load_scores()
    with open(backup_path, "w") as f:
        json.dump(scores, f, indent=2)
    log_event(f"💾 Backup saved: {backup_path}")