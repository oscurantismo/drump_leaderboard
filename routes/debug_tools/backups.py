from flask import Blueprint, request, redirect, abort, send_from_directory
import os
import time
from datetime import datetime, timedelta
from utils.storage import BACKUP_FOLDER, backup_scores
from utils.logging import log_event

backup_routes = Blueprint("backup_routes", __name__)

@backup_routes.route("/download-latest-backup", methods=["POST"])
def download_latest_backup():
    try:
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        filename = f"leaderboard_backup_{timestamp}_manual.json"
        backup_scores(tag="manual")
        time.sleep(1)
        return redirect(f"/download-backup?file={filename}")
    except Exception as e:
        log_event(f"❌ Failed to create manual backup: {e}")
        return f"❌ Failed to create backup: {e}", 500

@backup_routes.route("/download-backup")
def download_backup():
    filename = request.args.get("file")
    if not filename or not filename.endswith(".json") or "/" in filename or "\\" in filename:
        return abort(400, "Invalid filename")
    path = os.path.join(BACKUP_FOLDER, filename)
    if not os.path.exists(path):
        return abort(404, "File not found")
    return send_from_directory(BACKUP_FOLDER, filename, as_attachment=True)

@backup_routes.route("/delete-backup")
def delete_backup():
    filename = request.args.get("file")
    if not filename or "/" in filename or "\\" in filename or not filename.endswith(".json"):
        return abort(400, "Invalid file name.")
    full_path = os.path.join(BACKUP_FOLDER, filename)
    if not os.path.exists(full_path):
        return abort(404, "File not found")
    os.remove(full_path)
    log_event(f"🗑️ Deleted backup: {filename}")
    return redirect("/backups")

@backup_routes.route("/preview-backup")
def preview_backup():
    filename = request.args.get("file")
    if not filename or "/" in filename or "\\" in filename or not filename.endswith(".json"):
        return abort(400, "Invalid file name.")
    path = os.path.join(BACKUP_FOLDER, filename)
    if not os.path.exists(path):
        return abort(404, "File not found")
    try:
        with open(path, "r") as f:
            return "".join(f.readlines()[:500])
    except Exception as e:
        return f"❌ Failed to preview file: {e}"
