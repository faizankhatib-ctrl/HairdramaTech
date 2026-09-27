"""
Flask Application Factory
Initializes extensions, loads configuration, registers blueprints, and sets up global error handlers.
"""

import os
import logging
from flask import Flask
from werkzeug.exceptions import HTTPException
from app.config import config_by_name
from app.extensions import db, cors
from app.utils.responses import success_response, error_response


def create_app(config_name: str = None) -> Flask:
    """
    Application factory pattern.
    Creates and configures an instance of the Flask application.
    """
    if config_name is None:
        config_name = os.environ.get("FLASK_ENV", "development")

    app = Flask(__name__)
    
    # Load configuration
    config_class = config_by_name.get(config_name, config_by_name["default"])
    app.config.from_object(config_class)

    # Initialize extensions
    db.init_app(app)

    # Configure CORS
    frontend_url_env = app.config.get("FRONTEND_URL", "http://localhost:3000")
    if app.config.get("FLASK_ENV") == "production":
        import re
        raw_origins = [url.strip() for url in frontend_url_env.split(",") if url.strip()]
        allowed_origins = [o for o in raw_origins if o != "*"]
        if "*" in raw_origins:
            allowed_origins = ["*"]
        else:
            # Automatically permit Vercel domains (e.g. *.vercel.app)
            allowed_origins.append(re.compile(r"^https://[a-zA-Z0-9\-]+(?:\.[a-zA-Z0-9\-]+)*\.vercel\.app$"))
    else:
        # In development/testing, permit localhost variations alongside configured FRONTEND_URL
        allowed_origins = list({
            frontend_url_env.strip(),
            "http://localhost:3000",
            "http://127.0.0.1:3000",
        })

    cors.init_app(
        app,
        resources={
            r"/api/*": {
                "origins": allowed_origins,
                "methods": ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
                "allow_headers": ["Content-Type", "Authorization"],
                "supports_credentials": True,
            }
        },
    )

    # Register blueprints
    from app.routes.health import health_bp
    from app.routes.auth import auth_bp
    from app.routes.users import users_bp
    from app.routes.tasks import tasks_bp
    from app.routes.dashboard import dashboard_bp
    from app.routes.notifications import notifications_bp
    app.register_blueprint(health_bp, url_prefix="/api")
    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(users_bp, url_prefix="/api/users")
    app.register_blueprint(tasks_bp, url_prefix="/api/tasks")
    app.register_blueprint(dashboard_bp, url_prefix="/api/dashboard")
    app.register_blueprint(notifications_bp, url_prefix="/api/notifications")

    @app.route("/")
    def index():
        return success_response(
            data={
                "service": "hairdrama-task-api",
                "version": "1.0.0",
                "status": "online",
                "endpoints": {
                    "health": "/api/health",
                    "auth": "/api/auth",
                    "tasks": "/api/tasks",
                    "users": "/api/users",
                    "dashboard": "/api/dashboard",
                    "notifications": "/api/notifications",
                },
            },
            message="Hairdrama Task Management API is running",
        )

    # Register global error handlers
    register_error_handlers(app)

    # Logging setup
    configure_logging(app)

    return app


def register_error_handlers(app: Flask) -> None:
    """Registers consistent JSON error handlers for common HTTP status codes and exceptions."""

    @app.errorhandler(404)
    def handle_not_found(e):
        return error_response(
            message="The requested resource or endpoint was not found.",
            code="NOT_FOUND",
            status_code=404,
        )

    @app.errorhandler(405)
    def handle_method_not_allowed(e):
        return error_response(
            message="The HTTP method is not allowed for this endpoint.",
            code="METHOD_NOT_ALLOWED",
            status_code=405,
        )

    @app.errorhandler(400)
    def handle_bad_request(e):
        return error_response(
            message=getattr(e, "description", "Bad request syntax or invalid parameters."),
            code="BAD_REQUEST",
            status_code=400,
        )

    @app.errorhandler(HTTPException)
    def handle_http_exception(e):
        return error_response(
            message=e.description,
            code=e.name.upper().replace(" ", "_"),
            status_code=e.code,
        )

    @app.errorhandler(Exception)
    def handle_unexpected_exception(e):
        app.logger.exception(f"Unhandled server error: {e}")
        
        # In development mode, provide error message for easier debugging
        # In production mode, conceal internal trace details
        if app.config.get("DEBUG", False):
            msg = f"Internal server error: {str(e)}"
        else:
            msg = "An unexpected internal server error occurred. Please try again later."

        return error_response(
            message=msg,
            code="INTERNAL_SERVER_ERROR",
            status_code=500,
        )


def configure_logging(app: Flask) -> None:
    """Configures structured application logging."""
    if not app.debug:
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s [%(levelname)s] in %(module)s: %(message)s",
        )
