from flask import Flask
from flask_cors import CORS
import logging
import sys
import os
from utils.logging import log_event
from utils.storage import backup_scores
from routes.debug_tools.subscriptions import auto_backup_subscriptions
from flask_apscheduler import APScheduler

# ✅ Ensure logs print immediately to Railway logs panel
logging.basicConfig(level=logging.DEBUG, stream=sys.stdout)

# ✅ App config for APScheduler
class Config:
    SCHEDULER_API_ENABLED = True

# ✅ Initialize app and scheduler
app = Flask(__name__)
app.config.from_object(Config())
app.secret_key = os.getenv("SECRET_KEY", "dev_secret_for_debug_only")

scheduler = APScheduler()
scheduler.init_app(app)

# ✅ Add scheduled jobs
scheduler.add_job(id="regular_backup", func=backup_scores, trigger="interval", hours=6)
scheduler.add_job(id="daily_subscription_backup", func=auto_backup_subscriptions, trigger="interval", hours=24)
scheduler.start()

# ✅ Import blueprints
from routes.user import user_routes
from routes.leaderboard import leaderboard_routes
from routes.referral import referral_routes
from routes.admin import admin_routes
from routes.rewards import rewards_bp
from routes.debug_tools.reward_logs import reward_logs_bp
from routes.tasks import tasks_routes
from routes.notifications import notifications_routes
from routes.debug_tools import subscription_routes
from routes.debug_tools import register_logging_routes

# ✅ Log startup
log_event("🚀 Initializing Flask app")

# ✅ Enable CORS for frontend
try:
    CORS(app, origins=["https://oscurantismo.github.io"])
    log_event("✅ CORS applied for GitHub Pages")
except Exception as e:
    log_event(f"❌ CORS setup failed: {e}")

# ✅ Register all blueprints
app.register_blueprint(user_routes)
app.register_blueprint(leaderboard_routes)
app.register_blueprint(referral_routes)
app.register_blueprint(admin_routes)
app.register_blueprint(rewards_bp)
app.register_blueprint(reward_logs_bp)
app.register_blueprint(tasks_routes)
app.register_blueprint(notifications_routes)
app.register_blueprint(subscription_routes)
register_logging_routes(app)

log_event("✅ All blueprints registered")

# ✅ Run the app
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    try:
        log_event(f"🟢 Starting Flask app on port {port}")
        app.run(debug=False, host="0.0.0.0", port=port)
    except Exception as e:
        log_event(f"❌ Server crashed during startup: {e}")
