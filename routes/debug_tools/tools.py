from flask import Blueprint

tool_routes = Blueprint("tool_routes", __name__)

@tool_routes.route("/upload-tools")
def upload_tools():
    return """
    <h3>📤 Upload Leaderboard Backup (.json)</h3>
    <form action="/upload-scores" method="post" enctype="multipart/form-data">
        <input type="file" name="file" accept=".json" required>
        <button type="submit">Upload scores.json</button>
    </form>
    """

@tool_routes.route("/manual-tools")
def manual_tools():
    return """
    <h3>💾 Manual Backup</h3>
    <form action="/download-latest-backup" method="post">
        <button type="submit">Create + Download Manual Backup</button>
    </form>
    """
