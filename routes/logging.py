import os
import json
from flask import (
    Blueprint, request, abort, send_file, send_from_directory,
    session, redirect, url_for, render_template_string
)
from utils.storage import load_scores, BACKUP_FOLDER
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
        if (request.form.get("username") == ADMIN_USERNAME and
                request.form.get("password") == ADMIN_PASSWORD):
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

        {''
        if not debug_enabled else '''
        <form action="/upload-scores" method="post" enctype="application/json" style="margin-bottom: 20px;">
            <h4>🧪 Crash Test Upload</h4>
            <input type="file" name="file" accept=".json" required>
            <button type="submit">Upload raw scores.json</button>
        </form>
        '''}

        <div class="log-box">
            {log_html}
        </div>
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
            body {{
                font-family: Arial, sans-serif;
                background: #f4f4f4;
                padding: 20px;
                color: #333;
            }}
            h2 {{
                color: #0047ab;
            }}
            ul {{
                list-style: none;
                padding: 0;
            }}
            li {{
                background: #fff;
                margin-bottom: 10px;
                padding: 10px 15px;
                border-radius: 8px;
                box-shadow: 0 2px 5px rgba(0,0,0,0.1);
                display: flex;
                justify-content: space-between;
                align-items: center;
            }}
            .btn {{
                background: #007bff;
                color: #fff;
                padding: 6px 12px;
                text-decoration: none;
                border-radius: 6px;
                font-weight: bold;
                transition: background 0.3s;
            }}
            .btn:hover {{
                background: #0056b3;
            }}
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
