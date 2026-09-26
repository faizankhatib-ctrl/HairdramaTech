"""
User Directory Routes
Endpoint for retrieving selectable users for task assignment.
"""

from flask import Blueprint, request
from app.services.user_service import UserService
from app.utils.responses import success_response
from app.utils.decorators import token_required

users_bp = Blueprint("users", __name__)


@users_bp.route("", methods=["GET"])
@token_required
def get_users(current_user):
    """
    GET /api/users
    Returns registered users for the task assignment dropdown.
    Supports optional ?search= query parameter.
    Does not expose authentication IDs or sensitive data.
    """
    search_query = request.args.get("search")
    users = UserService.get_assignable_users(search=search_query)

    return success_response(
        data={"users": users, "total": len(users)},
        message="Users retrieved successfully.",
    )
