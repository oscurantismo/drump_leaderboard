import json
from flask import Blueprint, request
import os
from utils.storage import BACKUP_FOLDER, DATA_FILE
from utils.logging import log_event

admin_routes = Blueprint("admin_routes", __name__)

@admin_routes.route("/restore-backup")
def restore_backup():
    filename = request.args.get("file")

    if not filename or not filename.endswith(".json"):
        return "❌ Invalid or missing filename."

    # Sanity check: prevent directory traversal
    if "/" in filename or ".." in filename:
        return "❌ Unsafe filename."

    backup_path = os.path.join(BACKUP_FOLDER, filename)

    if not os.path.exists(backup_path):
        return f"❌ Backup not found: {filename}"

    try:
        with open(backup_path, "r") as f:
            data = f.read()

        with open(DATA_FILE, "w") as f:
            f.write(data)

        log_event(f"🔁 Restored scores.json from backup: {filename}")
        return f"✅ Successfully restored scores.json from: {filename}"
    except Exception as e:
        log_event(f"❌ Restore failed: {e}")
        return f"❌ Restore failed: {e}"

@admin_routes.route("/upload-scores", methods=["POST"])
def upload_scores():
    try:
        file_data = request.data
        with open(DATA_FILE, "wb") as f:
            f.write(file_data)
        log_event("⚠️ Directly wrote raw uploaded data to scores.json (crash test)")
        return "✅ Uploaded new scores.json", 200
    except Exception as e:
        log_event(f"❌ Upload failed: {e}")
        return f"❌ Upload failed: {e}", 500
