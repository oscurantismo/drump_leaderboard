from flask import Flask
from flask_cors import CORS
import logging
import sys
import os
from flask import Blueprint, request
import os
from utils.storage import BACKUP_FOLDER, DATA_FILE
from utils.logging import log_event

# ✅ Ensure logs print immediately to Railway logs panel
logging.basicConfig(level=logging.DEBUG, stream=sys.stdout)

# Import blueprints
from routes.user import user_routes
from routes.leaderboard import leaderboard_routes
from routes.referral import referral_routes
from routes.logging import log_routes
from utils.logging import log_event
from utils.storage import backup_scores
from routes.admin import admin_routes


admin_routes = Blueprint("admin_routes", __name__)

@admin_routes.route("/restore-backup")
def restore_backup():
    filename = request.args.get("file")

    if not filename or not filename.endswith(".json"):
        return "❌ Invalid or missing filename."

    if "/" in filename or ".." in filename:
        return "❌ Unsafe filename."

    backup_path = os.path.join(BACKUP_FOLDER, filename)

    if not os.path.exists(backup_path):
        return f"❌ Backup not found: {filename}"

    try:
        with open(backup_path, "r") as f:
            data = f.read()

        with open(DATA_FILE, "w") as f:
            f.write(data)

        log_event(f"🔁 Restored scores.json from backup: {filename}")
        return f"✅ Successfully restored scores.json from: {filename}"
    except Exception as e:
        log_event(f"❌ Restore failed: {e}")
        return f"❌ Restore failed: {e}"

# Scheduler setup
from flask_apscheduler import APScheduler

class Config:
    SCHEDULER_API_ENABLED = True

app = Flask(__name__)
app.config.from_object(Config())
scheduler = APScheduler()
scheduler.init_app(app)

# ✅ Log app startup
log_event("🚀 Initializing Flask app")

try:
    CORS(app, origins=["https://oscurantismo.github.io"])
    log_event("✅ CORS applied for GitHub Pages")
except Exception as e:
    log_event(f"❌ CORS setup failed: {e}")

# Register blueprints
app.register_blueprint(user_routes)
app.register_blueprint(leaderboard_routes)
app.register_blueprint(referral_routes)
app.register_blueprint(log_routes)
app.register_blueprint(admin_routes)
log_event("✅ All blueprints registered")

# ✅ Scheduled backup every 6 hours
@scheduler.task("interval", id="regular_backup", hours=6)
def scheduled_backup():
    log_event("🕒 Running scheduled backup")
    backup_scores()

scheduler.start()

# ✅ Run app
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    try:
        log_event(f"🟢 Starting Flask app on port {port}")
        app.run(debug=False, host="0.0.0.0", port=port)
    except Exception as e:
        log_event(f"❌ Server crashed during startup: {e}")
