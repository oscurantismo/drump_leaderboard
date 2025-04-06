from flask import Flask
from flask_cors import CORS
import logging
import sys
import os

# ✅ Ensure logs print immediately to Railway logs panel
logging.basicConfig(level=logging.DEBUG, stream=sys.stdout)

# Import blueprints
from routes.user import user_routes
from routes.leaderboard import leaderboard_routes
from routes.referral import referral_routes
from routes.logging import log_routes
from utils.logging import log_event
from utils.storage import backup_scores

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
