"""
Health Check Route
Provides an operational status endpoint to verify service uptime and database connectivity.
"""

from flask import Blueprint, current_app
from sqlalchemy import text
from app.extensions import db
from app.utils.responses import success_response, error_response

health_bp = Blueprint("health", __name__)


@health_bp.route("/health", methods=["GET"])
def health_check():
    """
    GET /api/health
    Returns service health status and tests database connectivity.
    """
    db_status = "unknown"
    db_error = None

    try:
        # Perform lightweight connectivity probe
        db.session.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception as e:
        db_status = "error"
        db_error = str(e)
        current_app.logger.warning(f"Database health probe failed: {e}")

    payload = {
        "status": "healthy" if db_status == "connected" else "degraded",
        "service": "hairdrama-task-api",
        "environment": current_app.config.get("FLASK_ENV", "development"),
        "database": {
            "status": db_status,
            "engine": db.engine.name if db.engine else "unknown",
        },
    }

    if db_error:
        try:
            db.session.rollback()
        except Exception:
            pass
        if current_app.config.get("DEBUG", False):
            payload["database"]["error_details"] = db_error

    return success_response(
        data=payload,
        message="Backend service is operational",
        status_code=200 if db_status == "connected" else 200,  # Service itself is responding
    )
