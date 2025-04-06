from flask import Flask
from flask_cors import CORS

# Import route blueprints
from routes.user import user_routes
from routes.leaderboard import leaderboard_routes
from routes.referral import referral_routes
from routes.logging import log_routes

app = Flask(__name__)
CORS(app)

# Register blueprints
app.register_blueprint(user_routes)
app.register_blueprint(leaderboard_routes)
app.register_blueprint(referral_routes)
app.register_blueprint(log_routes)

if __name__ == "__main__":
    app.run(debug=True, port=5000)
