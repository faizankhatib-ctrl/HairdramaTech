"""
Task Management Routes
Provides CRUD endpoints, assignment, completion toggles, and query filtering for tasks.
"""

from flask import Blueprint, request
from app.services.task_service import TaskService
from app.utils.responses import success_response, error_response
from app.utils.decorators import token_required

tasks_bp = Blueprint("tasks", __name__)


@tasks_bp.route("", methods=["GET"])
@token_required
def list_tasks(current_user):
    """
    GET /api/tasks
    List tasks with query parameters:
    - status: 'TODO' | 'IN_PROGRESS' | 'COMPLETED'
    - priority: 'LOW' | 'MEDIUM' | 'HIGH' | 'URGENT'
    - search: substring search in title and description
    - scope: 'all' | 'assigned_to_me' | 'created_by_me'
    """
    status = request.args.get("status")
    priority = request.args.get("priority")
    search = request.args.get("search")
    scope = request.args.get("scope", "all")

    tasks = TaskService.list_tasks(
        current_user=current_user,
        status=status,
        priority=priority,
        search=search,
        scope=scope,
    )

    serialized = [t.to_dict(include_users=True) for t in tasks]
    return success_response(
        data={"tasks": serialized, "total": len(serialized)},
        message="Tasks retrieved successfully.",
    )


@tasks_bp.route("", methods=["POST"])
@token_required
def create_task(current_user):
    """
    POST /api/tasks
    Creates a new task authored by the authenticated user.
    """
    payload = request.get_json(silent=True)
    if payload is None:
        return error_response(
            message="Invalid JSON payload.",
            code="INVALID_PAYLOAD",
            status_code=400,
        )

    task, err, status_code = TaskService.create_task(current_user, payload)
    if err:
        return error_response(
            message=err["message"],
            code=err["code"],
            status_code=status_code,
        )

    return success_response(
        data={"task": task.to_dict(include_users=True)},
        message="Task created successfully.",
        status_code=201,
    )


@tasks_bp.route("/<task_id>", methods=["GET"])
@token_required
def get_task(current_user, task_id):
    """
    GET /api/tasks/<task_id>
    Retrieves full details of a single task.
    """
    task, err, status_code = TaskService.get_task(task_id, current_user)
    if err:
        return error_response(
            message=err["message"],
            code=err["code"],
            status_code=status_code,
        )

    return success_response(
        data={"task": task.to_dict(include_users=True)},
        message="Task retrieved successfully.",
    )


@tasks_bp.route("/<task_id>", methods=["PUT"])
@token_required
def update_task(current_user, task_id):
    """
    PUT /api/tasks/<task_id>
    Updates task properties with authorization checks.
    """
    payload = request.get_json(silent=True)
    if payload is None:
        return error_response(
            message="Invalid JSON payload.",
            code="INVALID_PAYLOAD",
            status_code=400,
        )

    task, err, status_code = TaskService.update_task(task_id, current_user, payload)
    if err:
        return error_response(
            message=err["message"],
            code=err["code"],
            status_code=status_code,
        )

    return success_response(
        data={"task": task.to_dict(include_users=True)},
        message="Task updated successfully.",
    )


@tasks_bp.route("/<task_id>/assign", methods=["PATCH"])
@token_required
def assign_task(current_user, task_id):
    """
    PATCH /api/tasks/<task_id>/assign
    Assigns or unassigns task to a registered user.
    """
    payload = request.get_json(silent=True)
    if payload is None:
        return error_response(
            message="Invalid JSON payload.",
            code="INVALID_PAYLOAD",
            status_code=400,
        )

    assignee_id = payload.get("assigned_to")
    task, err, status_code = TaskService.assign_task(task_id, current_user, assignee_id)
    if err:
        return error_response(
            message=err["message"],
            code=err["code"],
            status_code=status_code,
        )

    return success_response(
        data={"task": task.to_dict(include_users=True)},
        message="Task assigned successfully.",
    )


@tasks_bp.route("/<task_id>/complete", methods=["PATCH"])
@token_required
def complete_task(current_user, task_id):
    """
    PATCH /api/tasks/<task_id>/complete
    Marks task complete or toggles completion status.
    """
    payload = request.get_json(silent=True) or {}
    completed_flag = payload.get("completed") if "completed" in payload else None

    task, err, status_code = TaskService.toggle_completion(task_id, current_user, completed_flag)
    if err:
        return error_response(
            message=err["message"],
            code=err["code"],
            status_code=status_code,
        )

    action_msg = "Task marked as completed." if task.status == "COMPLETED" else "Task reopened."
    return success_response(
        data={"task": task.to_dict(include_users=True)},
        message=action_msg,
    )


@tasks_bp.route("/<task_id>", methods=["DELETE"])
@token_required
def delete_task(current_user, task_id):
    """
    DELETE /api/tasks/<task_id>
    Deletes a task. Restricted to author only.
    """
    success, err, status_code = TaskService.delete_task(task_id, current_user)
    if err:
        return error_response(
            message=err["message"],
            code=err["code"],
            status_code=status_code,
        )

    return success_response(
        data={"id": task_id},
        message="Task deleted successfully.",
        status_code=200,
    )
