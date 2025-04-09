from .auth import auth_routes
from .logs import log_routes
from .backups import backup_routes
from .tools import tool_routes

def register_logging_routes(app):
    app.register_blueprint(auth_routes)
    app.register_blueprint(log_routes)
    app.register_blueprint(backup_routes)
    app.register_blueprint(tool_routes)
