"""
Dashboard Metrics Routes
Aggregates summary metrics for the authenticated user's tasks.
"""

from flask import Blueprint
from app.services.task_service import TaskService
from app.utils.responses import success_response
from app.utils.decorators import token_required

dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.route("/stats", methods=["GET"])
@token_required
def get_stats(current_user):
    """
    GET /api/dashboard/stats
    Returns task metrics for the authenticated user:
    - total_tasks
    - todo
    - in_progress
    - completed
    - assigned_to_me
    - created_by_me
    """
    stats = TaskService.get_dashboard_stats(current_user)

    return success_response(
        data=stats,
        message="Dashboard statistics retrieved successfully.",
    )
