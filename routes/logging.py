import os
import json
import time
from datetime import datetime, timedelta
from flask import (
    Blueprint, request, abort, send_file, send_from_directory,
    session, redirect, url_for, render_template_string, redirect
)
from utils.storage import load_scores, BACKUP_FOLDER, backup_scores
from utils.logging import log_event

log_routes = Blueprint("log_routes", __name__)

# === Login Protection ===
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "changeme")

@log_routes.before_request
def require_login():
    exempt_paths = {"/login"}
    if request.path in exempt_paths:
        return
    if not session.get("logged_in"):
        return redirect(url_for("log_routes.login"))

@log_routes.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        if request.form.get("username") == ADMIN_USERNAME and request.form.get("password") == ADMIN_PASSWORD:
            session["logged_in"] = True
            return redirect(url_for("log_routes.view_logs"))
        else:
            return "❌ Invalid login", 401

    return '''
        <form method="post">
            <h3>🔐 Admin Login</h3>
            <input name="username" placeholder="Username" required>
            <input name="password" type="password" placeholder="Password" required>
            <button type="submit">Login</button>
        </form>
    '''

# === Download Logs ===
@log_routes.route("/download-logs")
def download_logs():
    log_path = "/app/data/logs.txt"
    if not os.path.exists(log_path):
        return "❌ No logs.txt file found."
    return send_file(log_path, as_attachment=True)

# === Manual Backup Creator and Downloader ===
@log_routes.route("/download-latest-backup", methods=["POST"])
def download_latest_backup():
    try:
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        filename = f"leaderboard_backup_{timestamp}_manual.json"
        backup_scores(tag="manual")
        time.sleep(1)
        return redirect(url_for("log_routes.download_backup", file=filename))
    except Exception as e:
        log_event(f"❌ Failed to create manual backup: {e}")
        return f"❌ Failed to create backup: {e}", 500

# === View Logs Page ===
@log_routes.route("/debug-logs")
def view_logs():
    log_path = "/app/data/logs.txt"
    debug_enabled = request.args.get("debug") == "true"

    if not os.path.exists(log_path):
        log_html = "<p>No logs yet.</p>"
    else:
        with open(log_path, "r") as f:
            log_content = f.read().replace("\n", "<br>")
        log_html = f"<div>{log_content}</div>"

    crash_upload_html = ""
    if debug_enabled:
        crash_upload_html = """
        <form action="/upload-scores" method="post" enctype="application/json" style="margin-bottom: 20px;">
            <h4>🧪 Crash Test Upload</h4>
            <input type="file" name="file" accept=".json" required>
            <button type="submit">Upload raw scores.json</button>
        </form>
        """

    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>🪵 Debug Logs</title>
        <style>
            body {{
                font-family: monospace;
                background: #f9f9f9;
                padding: 20px;
                color: #222;
            }}
            h2 {{
                color: #002868;
            }}
            .nav-links {{
                margin-bottom: 20px;
            }}
            .nav-links a {{
                display: inline-block;
                margin-right: 12px;
                margin-bottom: 10px;
                padding: 8px 14px;
                background: #007bff;
                color: white;
                text-decoration: none;
                border-radius: 6px;
                font-size: 14px;
                font-weight: bold;
                transition: background 0.3s;
            }}
            .nav-links a:hover {{
                background: #0056b3;
            }}
            .log-box {{
                background: #fff;
                padding: 20px;
                border-radius: 8px;
                box-shadow: 0 2px 6px rgba(0,0,0,0.1);
                max-height: 600px;
                overflow-y: scroll;
                font-size: 13px;
            }}
        </style>
    </head>
    <body>
        <h2>🪵 Debug Logs</h2>

        <div class="nav-links">
            <a href="/backups">📦 View Backups</a>
            <a href="/leaderboard-page">🏆 Leaderboard</a>
            <a href="/referral-history-table">📨 Referral History</a>
            <a href="/user-logs">👥 User Logs</a>
            <a href="/download-logs">⬇️ Download logs.txt</a>
        </div>

        <h3>🛠 Leaderboard Tools</h3>

        <form action="/upload-scores" method="post" enctype="multipart/form-data" onsubmit="return validateUpload()" style="margin-bottom: 20px;">
            <h4>📤 Upload Leaderboard Backup (.json)</h4>
            <input type="file" id="jsonFile" name="file" accept=".json" required onchange="previewJSON()">
            <br><br>
            <button type="submit">Upload scores.json</button>
        </form>

        <pre id="jsonPreview" style="background:#f0f0f0;padding:10px;border-radius:6px;max-height:200px;overflow:auto;font-size:13px;"></pre>

        <form action="/download-latest-backup" method="post" style="margin-bottom: 30px;">
            <h4>💾 Create + Download Manual Backup</h4>
            <button type="submit">Save Manual Backup</button>
        </form>

        {crash_upload_html}

        <div class="log-box">
            {log_html}
        </div>

        <script>
        function validateUpload() {{
            const fileInput = document.getElementById('jsonFile');
            if (!fileInput.files.length) {{
                alert("Please select a JSON file.");
                return false;
            }}
            const file = fileInput.files[0];
            if (!file.name.endsWith(".json")) {{
                alert("Only .json files are allowed.");
                return false;
            }}
            return true;
        }}

        function previewJSON() {{
            const file = document.getElementById('jsonFile').files[0];
            if (!file) return;

            const reader = new FileReader();
            reader.onload = function(e) {{
                try {{
                    const obj = JSON.parse(e.target.result);
                    const formatted = JSON.stringify(obj, null, 2);
                    document.getElementById('jsonPreview').textContent = formatted;
                }} catch (err) {{
                    document.getElementById('jsonPreview').textContent = "❌ Invalid JSON: " + err.message;
                }}
            }};
            reader.readAsText(file);
        }}
        </script>
    </body>
    </html>
    """

# === Download Backup Files ===
@log_routes.route("/download-backup")
def download_backup():
    filename = request.args.get("file")
    if not filename or not filename.endswith(".json") or "/" in filename or "\\" in filename:
        return abort(400, "Invalid filename")
    full_path = os.path.join(BACKUP_FOLDER, filename)
    if not os.path.exists(full_path):
        return abort(404, "File not found")
    return send_from_directory(BACKUP_FOLDER, filename, as_attachment=True)

# === View Available Backups ===
from datetime import datetime, timedelta

@log_routes.route("/backups")
def view_backups():
    try:
        # Cleanup: remove backups older than 3 weeks
        cutoff = datetime.now() - timedelta(weeks=3)
        files = []

        for filename in os.listdir(BACKUP_FOLDER):
            if filename.endswith(".json"):
                path = os.path.join(BACKUP_FOLDER, filename)
                try:
                    ts_str = filename.replace("leaderboard_backup_", "").replace(".json", "").replace("_manual", "")
                    ts = datetime.strptime(ts_str, "%Y%m%d_%H%M%S")
                    if ts < cutoff:
                        os.remove(path)
                        continue
                    files.append((ts, filename))
                except Exception:
                    continue

        # Sort newest first regardless of manual/auto
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
    
@log_routes.route("/delete-backup")
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

@log_routes.route("/preview-backup")
def preview_backup():
    filename = request.args.get("file")
    if not filename or "/" in filename or "\\" in filename or not filename.endswith(".json"):
        return abort(400, "Invalid file name.")
    full_path = os.path.join(BACKUP_FOLDER, filename)
    if not os.path.exists(full_path):
        return abort(404, "File not found")
    try:
        with open(full_path, "r") as f:
            lines = f.readlines()
            return "".join(lines[:500])  # Return first 20 lines
    except Exception as e:
        return f"❌ Failed to preview file: {e}"

@log_routes.route("/debug-logs")
def debug_logs_base():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>🪵 Debug Tools</title>
        <style>
            body { font-family: monospace; padding: 20px; background: #f8f9f9; color: #222; }
            h2 { color: #002868; }
            .nav-links a {
                display: inline-block; margin-right: 12px; padding: 8px 14px;
                background: #007bff; color: white; text-decoration: none;
                border-radius: 6px; font-weight: bold;
            }
            .nav-links a:hover { background: #0056b3; }
            .section { margin-top: 30px; }
        </style>
    </head>
    <body>
        <h2>🧰 Debug Tools</h2>
        <div class="nav-links">
            <a href="/backups">📦 Backups</a>
            <a href="/upload-tools">📤 Upload Tools</a>
            <a href="/manual-tools">💾 Manual Backup</a>
            <a href="/download-logs">⬇️ Download logs.txt</a>
        </div>

        <div class="section">
            <h3>🪵 Latest Logs</h3>
            <pre id="log-box" style="background:#fff;padding:12px;border-radius:6px;max-height:600px;overflow:auto;"></pre>
        </div>

        <script>
        fetch("/debug-logs/content")
          .then(res => res.text())
          .then(html => { document.getElementById("log-box").innerHTML = html; });
        </script>
    </body>
    </html>
    """

@log_routes.route("/debug-logs/content")
def debug_logs_content():
    log_path = "/app/data/logs.txt"
    if not os.path.exists(log_path):
        return "❌ No logs found."
    with open(log_path, "r") as f:
        lines = f.readlines()[-300:]
    return "<br>".join(line.strip() for line in lines)
@log_routes.route("/upload-tools")
def upload_tools():
    return """
    <h3>📤 Upload Leaderboard Backup (.json)</h3>
    <form action="/upload-scores" method="post" enctype="multipart/form-data">
        <input type="file" name="file" accept=".json" required>
        <button type="submit">Upload scores.json</button>
    </form>
    """
@log_routes.route("/manual-tools")
def manual_tools():
    return """
    <h3>💾 Manual Backup</h3>
    <form action="/download-latest-backup" method="post">
        <button type="submit">Create + Download Manual Backup</button>
    </form>
    """

