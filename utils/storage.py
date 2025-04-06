import os
import json
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
            return json.load(f)
        except json.JSONDecodeError:
            log_event("❌ Failed to decode JSON")
            return []
            
def save_scores(scores):
    with open(DATA_FILE, "w") as f:
        json.dump(scores, f, indent=2)

def backup_scores():
    os.makedirs(BACKUP_FOLDER, exist_ok=True)
    from datetime import datetime
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = os.path.join(BACKUP_FOLDER, f"leaderboard_backup_{timestamp}.json")
    scores = load_scores()
    with open(backup_path, "w") as f:
        json.dump(scores, f, indent=2)
    log_event(f"💾 Backup saved: {backup_path}")
