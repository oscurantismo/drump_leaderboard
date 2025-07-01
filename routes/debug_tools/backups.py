from flask import Blueprint, request, redirect, abort, send_from_directory, render_template_string
import os
import json
import time
from datetime import datetime, timedelta
from utils.timeutils import gmt4_now
from utils.storage import BACKUP_FOLDER, backup_scores, SCORES_FILE, save_scores
from utils.logging import log_event

backup_routes = Blueprint("backup_routes", __name__)

@backup_routes.route("/download-latest-backup", methods=["POST"])
def download_latest_backup():
    try:
        backup_scores(tag="manual")
        time.sleep(1)

        # Find most recent _manual backup
        matching = sorted([
            f for f in os.listdir(BACKUP_FOLDER)
            if f.endswith("_manual.json")
        ], key=lambda f: os.path.getmtime(os.path.join(BACKUP_FOLDER, f)), reverse=True)

        if not matching:
            raise FileNotFoundError("No recent manual backup found")

        return redirect(f"/download-backup?file={matching[0]}")
    except Exception as e:
        log_event(f"❌ Failed to create manual backup: {e}")
        return f"❌ Failed to create backup: {e}", 500


@backup_routes.route("/upload-backup", methods=["POST"])
def upload_backup():
    try:
        file = request.files.get("file")
        if not file or not file.filename.endswith(".json"):
            return "❌ Invalid file.", 400
        timestamp = gmt4_now().strftime("%Y%m%d_%H%M%S")
        save_path = os.path.join(BACKUP_FOLDER, f"leaderboard_backup_{timestamp}.json")
        file.save(save_path)
        log_event(f"✅ Admin uploaded backup {save_path}")
        return redirect("/backups")
    except Exception as e:
        return f"❌ Failed to upload backup: {e}", 500

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

@backup_routes.route("/backups")
def view_backups():
    try:
        cutoff = gmt4_now() - timedelta(weeks=3)
        files = []

        for filename in os.listdir(BACKUP_FOLDER):
            if filename.endswith(".json"):
                path = os.path.join(BACKUP_FOLDER, filename)
                try:
                    ts_str = filename.replace("leaderboard_backup_", "").replace(".json", "").replace("_manual", "")
                    try:
                        ts = datetime.strptime(ts_str, "%Y%m%d_%H%M%S_%f")
                    except ValueError:
                        ts = datetime.strptime(ts_str, "%Y%m%d_%H%M%S")

                    if ts < cutoff:
                        os.remove(path)
                        continue
                    files.append((ts, filename))
                except Exception:
                    continue

        sorted_files = sorted(files, reverse=True)

    except Exception as e:
        return f"<p>❌ Could not read backup directory: {e}</p>"

    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>📦 Backups</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                background: #f4f4f4;
                padding: 20px;
                color: #333;
            }
            h2 {
                color: #0047ab;
            }
            form {
                margin-bottom: 20px;
            }
            ul {
                list-style: none;
                padding: 0;
            }
            li {
                background: #fff;
                margin-bottom: 10px;
                padding: 12px 15px;
                border-radius: 8px;
                box-shadow: 0 2px 5px rgba(0,0,0,0.1);
                display: flex;
                justify-content: space-between;
                align-items: center;
            }
            .actions {
                display: flex;
                gap: 10px;
            }
            .btn {
                background: #007bff;
                color: #fff;
                padding: 6px 12px;
                text-decoration: none;
                border-radius: 6px;
                font-weight: bold;
                transition: background 0.3s;
                border: none;
                cursor: pointer;
            }
            .btn:hover {
                background: #0056b3;
            }
            .danger {
                background: #dc3545;
            }
            .danger:hover {
                background: #a71d2a;
            }
            .preview-box {
                margin-top: 10px;
                background: #f8f9fa;
                padding: 10px;
                font-size: 12px;
                border-radius: 6px;
                max-height: 250px;
                overflow-y: auto;
                display: none;
                white-space: pre;
            }
        </style>
        <script>
        function confirmDelete(filename) {
            const confirmInput = prompt(`Type DELETE to remove "${filename}" permanently:`);
            if (confirmInput === "DELETE") {
                window.location.href = `/delete-backup?file=${filename}`;
            }
        }

        function togglePreview(filename) {
            const previewBox = document.getElementById(`preview-${filename}`);
            if (previewBox.style.display === "none") {
                fetch(`/preview-backup?file=${filename}`)
                    .then(res => res.text())
                    .then(text => {
                        previewBox.textContent = text;
                        previewBox.style.display = "block";
                    })
                    .catch(err => {
                        previewBox.textContent = "❌ Failed to load preview: " + err;
                        previewBox.style.display = "block";
                    });
            } else {
                previewBox.style.display = "none";
            }
        }
        </script>
    </head>
    <body>
        <h2>📦 Leaderboard & Referral Backups</h2>

        <form action="/download-latest-backup" method="post">
            <button class="btn">💾 Create + Download Manual Backup</button>
        </form>

        <form action="/upload-scores" method="post" enctype="multipart/form-data">
            <label><b>Upload scores.json</b></label><br>
            <input type="file" name="file" accept=".json" required>
            <button class="btn">⬆️ Upload Scores</button>
        </form>

        <form action="/upload-backup" method="post" enctype="multipart/form-data">
            <label><b>Upload New Backup (.json)</b></label><br>
            <input type="file" name="file" accept=".json" required>
            <button class="btn">⬆️ Upload Backup</button>
        </form>

        <ul>
    """

    for ts, filename in sorted_files:
        html += f"""
        <li>
            {filename}
            <div class="actions">
                <a class="btn" href="/download-backup?file={filename}">Download</a>
                <button class="btn" onclick="togglePreview('{filename}')">Preview</button>
                <button class="btn danger" onclick="confirmDelete('{filename}')">Delete</button>
            </div>
        </li>
        <pre class="preview-box" id="preview-{filename}"></pre>
        """

    html += """
        </ul>
    </body>
    </html>
    """

    return html
