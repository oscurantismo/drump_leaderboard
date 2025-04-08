import os
import json
import time
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
@log_routes.route("/backups")
def view_backups():
    try:
        files = sorted(os.listdir(BACKUP_FOLDER), reverse=True)
    except Exception as e:
        return f"<p>❌ Could not read backup directory: {e}</p>"

    json_files = [f for f in files if f.endswith(".json")]

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
                padding: 10px 15px;
                border-radius: 8px;
                box-shadow: 0 2px 5px rgba(0,0,0,0.1);
                display: flex;
                justify-content: space-between;
                align-items: center;
            }
            .btn {
                background: #007bff;
                color: #fff;
                padding: 6px 12px;
                text-decoration: none;
                border-radius: 6px;
                font-weight: bold;
                transition: background 0.3s;
            }
            .btn:hover {
                background: #0056b3;
            }
        </style>
    </head>
    <body>
        <h2>📦 Leaderboard & Referral Backups</h2>
        <ul>
    """

    for filename in json_files:
        html += f"""
        <li>
            {filename}
            <a class="btn" href="/download-backup?file={filename}">Download</a>
        </li>
        """

    html += """
        </ul>
    </body>
    </html>
    """

    return html
