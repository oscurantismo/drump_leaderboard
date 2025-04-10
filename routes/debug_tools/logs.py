from flask import Blueprint, request, send_file
import os

log_routes = Blueprint("log_routes", __name__)
LOG_PATH = "/app/data/logs.txt"

@log_routes.route("/download-logs")
def download_logs():
    if not os.path.exists(LOG_PATH):
        return "❌ No logs.txt file found."
    return send_file(LOG_PATH, as_attachment=True)

@log_routes.route("/debug-logs")
def view_logs():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>🪵 Debug Logs</title>
        <style>
            body {
                font-family: monospace;
                background: #f9f9f9;
                padding: 20px;
                color: #222;
            }
            h2 {
                color: #002868;
            }
            .nav-links {
                margin-bottom: 20px;
            }
            .nav-links a {
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
            }
            .nav-links a:hover {
                background: #0056b3;
            }
            .log-box {
                background: #fff;
                padding: 20px;
                border-radius: 8px;
                box-shadow: 0 2px 6px rgba(0,0,0,0.1);
                max-height: 600px;
                overflow-y: scroll;
                font-size: 13px;
                margin-bottom: 20px;
            }
            .btn-row button {
                margin-right: 10px;
                padding: 6px 12px;
                font-size: 13px;
                font-weight: bold;
                border: none;
                border-radius: 6px;
                cursor: pointer;
                background: #6c757d;
                color: #fff;
            }
            .btn-row button:hover {
                background: #5a6268;
            }
            .filter-row {
                margin-bottom: 15px;
            }
            input[type="text"], select {
                padding: 6px 10px;
                font-size: 13px;
                border-radius: 4px;
                border: 1px solid #ccc;
                margin-right: 10px;
            }
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
            <a href="/reward-logs">⬇️ Reward logs</a>
        </div>

        <div class="filter-row">
            <input type="text" id="search" placeholder="Search keyword...">
            <select id="category">
                <option value="">All Categories</option>
                <option value="referral">Referrals</option>
                <option value="submit">Score Submissions</option>
                <option value="register">User Registration</option>
            </select>
            <button onclick="loadLogs('filtered')">🔍 Filter</button>
        </div>

        <div class="btn-row">
            <button onclick="loadLogs('current')">🔄 Latest 300 lines</button>
            <button onclick="loadLogs('previous')">⏮ Previous 300 lines</button>
            <button onclick="loadLogs('all')">📄 Show all logs</button>
        </div>

        <div class="log-box" id="log-box">Loading logs...</div>

        <script>
        let offset = 0;

        function loadLogs(type) {
            let url = "/debug-logs/content";
            const keyword = document.getElementById("search").value;
            const category = document.getElementById("category").value;

            const params = new URLSearchParams();
            if (type === 'previous') {
                offset += 300;
                params.append("offset", offset);
            } else if (type === 'all') {
                params.append("all", "true");
                offset = 0;
            } else if (type === 'filtered') {
                offset = 0;
                if (keyword) params.append("search", keyword);
                if (category) params.append("category", category);
            } else {
                offset = 0;
            }

            if (params.toString()) {
                url += "?" + params.toString();
            }

            fetch(url)
              .then(res => res.text())
              .then(html => {
                  document.getElementById("log-box").innerHTML = html;
              });
        }

        loadLogs('current');
        </script>
    </body>
    </html>
    """

@log_routes.route("/debug-logs/content")
def debug_logs_content():
    if not os.path.exists(LOG_PATH):
        return "❌ No logs found."

    all_requested = request.args.get("all") == "true"
    offset = int(request.args.get("offset", 0))
    keyword = request.args.get("search", "").lower()
    category = request.args.get("category", "")

    with open(LOG_PATH, "r") as f:
        lines = f.readlines()

    if all_requested:
        selected = lines
    else:
        selected = lines[-300 - offset: -offset or None]

    if keyword:
        selected = [line for line in selected if keyword in line.lower()]

    if category:
        if category == "referral":
            selected = [line for line in selected if "referral" in line.lower()]
        elif category == "submit":
            selected = [line for line in selected if "score submitted" in line.lower()]
        elif category == "register":
            selected = [line for line in selected if "registered" in line.lower()]

    return "<br>".join(line.strip() for line in selected)
