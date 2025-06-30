import os
from .timeutils import utc_timestamp

LOG_FILE = "/app/data/logs.txt"

def log_event(message):
    timestamp = utc_timestamp()
    full = f"[{timestamp}] {message}"
    print(full)  # ✅ Railway console logs
    try:
        os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
        with open(LOG_FILE, "a") as f:
            f.write(full + "\n")
    except Exception as e:
        print(f"[{timestamp}] ❌ Failed to write log: {e}")
