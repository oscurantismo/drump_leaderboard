from flask import Blueprint, request, send_file
import os

log_routes = Blueprint("log_routes", __name__)
LOG_PATH = "/app/data/logs.txt"

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
