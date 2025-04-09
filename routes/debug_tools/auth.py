from flask import Blueprint, request, session, redirect, url_for

auth_routes = Blueprint("auth_routes", __name__)
import os

ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "changeme")

@auth_routes.before_app_request
def require_login():
    exempt_paths = {"/login", "/leaderboard-page", "/leaderboard"}
    if request.path in exempt_paths:
        return
    if not session.get("logged_in"):
        return redirect(url_for("auth_routes.login"))

@auth_routes.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        if request.form.get("username") == ADMIN_USERNAME and request.form.get("password") == ADMIN_PASSWORD:
            session["logged_in"] = True
            return redirect(url_for("log_routes.view_logs"))
        return "❌ Invalid login", 401

    return '''
        <form method="post">
            <h3>🔐 Admin Login</h3>
            <input name="username" placeholder="Username" required>
            <input name="password" type="password" placeholder="Password" required>
            <button type="submit">Login</button>
        </form>
    '''
