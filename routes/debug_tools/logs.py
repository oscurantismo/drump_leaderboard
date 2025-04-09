from flask import Blueprint, request, send_file
import os

log_routes = Blueprint("log_routes", __name__)
LOG_PATH = "/app/data/logs.txt"

@log_routes.route("/debug-logs")
def view_logs():
    return """
    <html>
    <head><title>🪵 Debug Logs</title></head>
    <body style="font-family: monospace; padding: 20px;">
        <h2>Debug Logs</h2>
        <pre id="log-content">Loading...</pre>
        <script>
        fetch("/debug-logs/content")
            .then(res => res.text())
            .then(html => { document.getElementById("log-content").innerHTML = html; });
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
