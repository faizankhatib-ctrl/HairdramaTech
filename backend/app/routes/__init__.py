"""
Routes package
"""

from app.routes.health import health_bp
from app.routes.auth import auth_bp
from app.routes.users import users_bp
from app.routes.tasks import tasks_bp
from app.routes.dashboard import dashboard_bp

__all__ = ["health_bp", "auth_bp", "users_bp", "tasks_bp", "dashboard_bp"]
