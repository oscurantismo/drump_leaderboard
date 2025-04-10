import json
from flask import Blueprint, request, redirect
import os
from utils.storage import BACKUP_FOLDER, SCORES_FILE
from utils.logging import log_event

admin_routes = Blueprint("admin_routes", __name__)

@admin_routes.route("/restore-backup")
def restore_backup():
    filename = request.args.get("file")

    if not filename or not filename.endswith(".json"):
        return "❌ Invalid or missing filename."

    if "/" in filename or ".." in filename:
        return "❌ Unsafe filename."

    backup_path = os.path.join(BACKUP_FOLDER, filename)

    if not os.path.exists(backup_path):
        return f"❌ Backup not found: {filename}"

    try:
        with open(backup_path, "r") as f:
            data = json.load(f)  # ✅ Safely parse JSON

        with open(DATA_FILE, "w") as f:
            json.dump(data, f, indent=2)  # ✅ Write clean JSON

        log_event(f"🔁 Restored scores.json from backup: {filename}")
        return f"✅ Successfully restored scores.json from: {filename}"
    except json.JSONDecodeError as e:
        log_event(f"❌ Restore failed — corrupted JSON: {e}")
        return f"❌ Restore failed — corrupted JSON: {e}", 400
    except Exception as e:
        log_event(f"❌ Restore failed: {e}")
        return f"❌ Restore failed: {e}", 500

@admin_routes.route("/upload-scores", methods=["POST"])
def upload_scores():
    try:
        uploaded_file = request.files.get("file")
        if not uploaded_file or not uploaded_file.filename.endswith(".json"):
            return "❌ Invalid file. Only .json files are allowed.", 400

        file_data = uploaded_file.read()
        data = json.loads(file_data)  # Check it's valid JSON

        # ✅ Save current scores.json as backup before replacing
        from utils.storage import backup_scores
        backup_scores(tag="before_upload")

        # ✅ Overwrite scores.json
        with open(DATA_FILE, "w") as f:
            f.write(file_data.decode("utf-8"))

        log_event("✅ scores.json manually uploaded via /upload-scores")
        return redirect("/debug-logs")
    except Exception as e:
        log_event(f"❌ Upload failed: {e}")
        return f"❌ Upload failed: {e}", 500
