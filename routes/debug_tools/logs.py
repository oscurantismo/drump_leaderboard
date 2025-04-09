from flask import Blueprint, request, send_file
import os

log_routes = Blueprint("log_routes", __name__)
LOG_PATH = "/app/data/logs.txt"

@log_routes.route("/debug-logs")
def view_logs():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>🪵 Debug Logs</title>
        <style>
            body { font-family: monospace; padding: 20px; background: #f9f9f9; color: #222; }
            h2 { color: #002868; }
            .nav {
                margin-bottom: 20px;
            }
            .nav a {
                margin-right: 10px;
                background: #007bff;
                color: white;
                padding: 8px 12px;
                border-radius: 6px;
                text-decoration: none;
                font-weight: bold;
            }
            .nav a:hover {
                background: #0056b3;
            }
        </style>
    </head>
    <body>
        <h2>🪵 Debug Logs</h2>
        <div class="nav">
            <a href="/debug-logs">Logs</a>
            <a href="/upload-tools">Upload Tools</a>
            <a href="/manual-tools">Manual Backup</a>
            <a href="/backups">Backups</a>
            <a href="/user-logs">User Logs</a>
        </div>
        <pre id="log-box" style="background:#fff;padding:12px;border-radius:6px;max-height:600px;overflow:auto;"></pre>
        <script>
        fetch("/debug-logs/content")
          .then(res => res.text())
          .then(html => { document.getElementById("log-box").innerHTML = html; });
        </script>
    </body>
    </html>
    """

@log_routes.route("/download-logs")
def download_logs():
    if not os.path.exists(LOG_PATH):
        return "❌ No logs.txt file found."
    return send_file(LOG_PATH, as_attachment=True)

@log_routes.route("/debug-logs/content")
def debug_logs_content():
    if not os.path.exists(LOG_PATH):
        return "❌ No logs found."
    with open(LOG_PATH, "r") as f:
        lines = f.readlines()[-300:]
    return "<br>".join(line.strip() for line in lines)
