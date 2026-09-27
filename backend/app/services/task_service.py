"""
Task Service
Encapsulates task business logic, validations, role-based authorization, and query filters.
"""

from datetime import datetime, timezone
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy import or_, and_
from app.extensions import db
from app.models.task import Task
from app.models.user import User
from app.utils.validators import is_valid_uuid, parse_iso_datetime, VALID_STATUSES, VALID_PRIORITIES
from app.services.email_service import EmailService


class TaskService:
    """Business operations and database queries for Task entities."""

    @staticmethod
    def list_tasks(
        current_user: User,
        status: Optional[str] = None,
        priority: Optional[str] = None,
        search: Optional[str] = None,
        scope: Optional[str] = "all",
    ) -> List[Task]:
        """
        Retrieves tasks matching the provided filters and authorization scope.
        
        Scope Definitions:
        - 'assigned_to_me': Tasks where current_user is the assignee.
        - 'created_by_me': Tasks authored by current_user.
        - 'all': Tasks where current_user is either author OR assignee (prevents cross-user data leakage).
        """
        query = Task.query

        # Scope filter (enforces strict authorization boundaries)
        if scope == "assigned_to_me":
            query = query.filter(Task.assigned_to == current_user.id)
        elif scope == "created_by_me":
            query = query.filter(Task.created_by == current_user.id)
        else:
            # Default 'all': user can view tasks they authored or were assigned to
            query = query.filter(
                or_(
                    Task.created_by == current_user.id,
                    Task.assigned_to == current_user.id,
                )
            )

        # Status filter
        if status and status.upper() in VALID_STATUSES:
            query = query.filter(Task.status == status.upper())

        # Priority filter
        if priority and priority.upper() in VALID_PRIORITIES:
            query = query.filter(Task.priority == priority.upper())

        # Text search (matches title or description case-insensitively)
        if search:
            pattern = f"%{search.strip()}%"
            query = query.filter(
                or_(
                    Task.title.ilike(pattern),
                    Task.description.ilike(pattern),
                )
            )

        return query.order_by(Task.created_at.desc()).all()

    @staticmethod
    def get_task(task_id: str, current_user: User) -> Tuple[Optional[Task], Optional[Dict[str, Any]], int]:
        """
        Retrieves a single task and enforces viewing authorization.
        Returns: (task, error_dict, http_status)
        """
        if not is_valid_uuid(task_id):
            return None, {"code": "INVALID_UUID", "message": "The task ID format is invalid."}, 400

        task = db.session.get(Task, task_id)
        if not task:
            return None, {"code": "TASK_NOT_FOUND", "message": "The requested task was not found."}, 404

        # Authorization check: only author or assignee may view private task details
        if task.created_by != current_user.id and task.assigned_to != current_user.id:
            return None, {"code": "FORBIDDEN", "message": "You are not authorized to view this task."}, 403

        return task, None, 200

    @staticmethod
    def create_task(current_user: User, data: Dict[str, Any]) -> Tuple[Optional[Task], Optional[Dict[str, Any]], int]:
        """
        Validates input and creates a new task entity.
        Returns: (created_task, error_dict, http_status)
        """
        # Validate title
        title = data.get("title")
        if not title or not isinstance(title, str) or not title.strip():
            return None, {"code": "MISSING_TITLE", "message": "Task title is required and cannot be empty."}, 400

        if len(title.strip()) > 255:
            return None, {"code": "INVALID_TITLE", "message": "Task title cannot exceed 255 characters."}, 400

        # Validate status
        status = data.get("status", "TODO")
        if status:
            status = str(status).upper()
            if status not in VALID_STATUSES:
                return None, {
                    "code": "INVALID_STATUS",
                    "message": f"Invalid status '{status}'. Valid options are: {', '.join(sorted(VALID_STATUSES))}.",
                }, 400
        else:
            status = "TODO"

        # Validate priority
        priority = data.get("priority", "MEDIUM")
        if priority:
            priority = str(priority).upper()
            if priority not in VALID_PRIORITIES:
                return None, {
                    "code": "INVALID_PRIORITY",
                    "message": f"Invalid priority '{priority}'. Valid options are: {', '.join(sorted(VALID_PRIORITIES))}.",
                }, 400
        else:
            priority = "MEDIUM"

        # Validate assigned_to
        assigned_to_id = data.get("assigned_to")
        if assigned_to_id:
            if not is_valid_uuid(assigned_to_id):
                return None, {"code": "INVALID_ASSIGNEE", "message": "Assigned user ID is not a valid UUID."}, 400
            
            target_user = db.session.get(User, assigned_to_id)
            if not target_user:
                return None, {"code": "INVALID_ASSIGNEE", "message": "Assigned user does not exist."}, 400

        # Validate due_date
        due_date_obj, date_err = parse_iso_datetime(data.get("due_date"))
        if date_err:
            return None, {"code": "INVALID_DATE_FORMAT", "message": date_err}, 400

        # Completion timestamp if status is COMPLETED
        completed_at = datetime.now(timezone.utc) if status == "COMPLETED" else None

        task = Task(
            title=title.strip(),
            description=data.get("description", "").strip() if data.get("description") else None,
            created_by=current_user.id,
            assigned_to=assigned_to_id if assigned_to_id else None,
            status=status,
            priority=priority,
            due_date=due_date_obj,
            completed_at=completed_at,
        )

        db.session.add(task)
        db.session.commit()

        # Trigger notification if assigned upon creation
        if task.assigned_to:
            assignee = db.session.get(User, task.assigned_to)
            if assignee:
                EmailService.send_task_assigned_email(task, assignee, current_user)

        return task, None, 201

    @staticmethod
    def update_task(
        task_id: str,
        current_user: User,
        data: Dict[str, Any],
    ) -> Tuple[Optional[Task], Optional[Dict[str, Any]], int]:
        """
        Updates task attributes with server-side authorization enforcement.
        Author: Can edit all fields (title, description, status, priority, due_date, assigned_to).
        Assignee: Can update status, description, and due_date.
        Others: 403 Forbidden.
        """
        task, err, status_code = TaskService.get_task(task_id, current_user)
        if err:
            return None, err, status_code

        is_author = task.created_by == current_user.id
        is_assignee = task.assigned_to == current_user.id

        if not is_author and not is_assignee:
            return None, {"code": "FORBIDDEN", "message": "You are not authorized to update this task."}, 403

        # Track pre-update state for conditional notifications
        was_completed = task.status == "COMPLETED"
        previous_assignee_id = task.assigned_to

        # Title update (author only)
        if "title" in data:
            if not is_author:
                return None, {"code": "FORBIDDEN", "message": "Only the task author may change the title."}, 403
            title = data["title"]
            if not title or not isinstance(title, str) or not title.strip():
                return None, {"code": "INVALID_TITLE", "message": "Title cannot be empty."}, 400
            if len(title.strip()) > 255:
                return None, {"code": "INVALID_TITLE", "message": "Title cannot exceed 255 characters."}, 400
            task.title = title.strip()

        # Description update
        if "description" in data:
            task.description = data["description"].strip() if data["description"] else None

        # Priority update (author only)
        if "priority" in data:
            if not is_author:
                return None, {"code": "FORBIDDEN", "message": "Only the task author may change priority."}, 403
            p = str(data["priority"]).upper()
            if p not in VALID_PRIORITIES:
                return None, {"code": "INVALID_PRIORITY", "message": f"Invalid priority '{p}'."}, 400
            task.priority = p

        # Status update
        if "status" in data:
            s = str(data["status"]).upper()
            if s not in VALID_STATUSES:
                return None, {"code": "INVALID_STATUS", "message": f"Invalid status '{s}'."}, 400
            
            if s == "COMPLETED" and task.status != "COMPLETED":
                task.completed_at = datetime.now(timezone.utc)
            elif s != "COMPLETED" and task.status == "COMPLETED":
                task.completed_at = None
            task.status = s

        # Due date update
        if "due_date" in data:
            due_date_obj, date_err = parse_iso_datetime(data["due_date"])
            if date_err:
                return None, {"code": "INVALID_DATE_FORMAT", "message": date_err}, 400
            task.due_date = due_date_obj

        # Assignee update (author only)
        if "assigned_to" in data:
            if not is_author:
                return None, {"code": "FORBIDDEN", "message": "Only the task author may reassign this task."}, 403
            new_assignee_id = data["assigned_to"]
            if new_assignee_id:
                if not is_valid_uuid(new_assignee_id):
                    return None, {"code": "INVALID_ASSIGNEE", "message": "Assigned user ID is not a valid UUID."}, 400
                target_user = db.session.get(User, new_assignee_id)
                if not target_user:
                    return None, {"code": "INVALID_ASSIGNEE", "message": "Assigned user does not exist."}, 400
                task.assigned_to = target_user.id
            else:
                task.assigned_to = None

        db.session.commit()

        # Trigger email notifications for status transitions (non-COMPLETED; COMPLETED handled by toggle_completion)
        if "status" in data:
            new_status_str = task.status
            old_status_str = "COMPLETED" if was_completed else "TODO"
            if old_status_str != new_status_str and new_status_str != "COMPLETED":
                # Notify the other party involved in the task
                if is_author and task.assignee:
                    EmailService.send_task_status_update_email(task, task.assignee, current_user, old_status_str, new_status_str)
                elif is_assignee and task.creator:
                    EmailService.send_task_status_update_email(task, task.creator, current_user, old_status_str, new_status_str)

        return task, None, 200

    @staticmethod
    def assign_task(
        task_id: str,
        current_user: User,
        assignee_id: Optional[str],
    ) -> Tuple[Optional[Task], Optional[Dict[str, Any]], int]:
        """
        Assigns or reassigns task to a registered user, or unassigns if None is provided.
        """
        task, err, status_code = TaskService.get_task(task_id, current_user)
        if err:
            return None, err, status_code

        # Only author may assign / reassign
        if task.created_by != current_user.id:
            return None, {"code": "FORBIDDEN", "message": "Only the task creator may reassign this task."}, 403

        previous_assignee_id = task.assigned_to

        if assignee_id:
            if not is_valid_uuid(assignee_id):
                return None, {"code": "INVALID_ASSIGNEE", "message": "Assigned user ID is not a valid UUID."}, 400
            target_user = db.session.get(User, assignee_id)
            if not target_user:
                return None, {"code": "INVALID_ASSIGNEE", "message": "Target assignee does not exist."}, 400
            task.assigned_to = target_user.id
        else:
            task.assigned_to = None

        db.session.commit()

        # Trigger email to new assignee (only if assigned to a user and changed from previous)
        if task.assigned_to and task.assigned_to != previous_assignee_id:
            new_assignee = db.session.get(User, task.assigned_to)
            if new_assignee:
                EmailService.send_task_assigned_email(task, new_assignee, current_user)

        return task, None, 200

    @staticmethod
    def toggle_completion(
        task_id: str,
        current_user: User,
        completed_flag: Optional[bool] = None,
    ) -> Tuple[Optional[Task], Optional[Dict[str, Any]], int]:
        """
        Marks task as completed or reopens it.
        Both the task creator and the assignee have permission to complete a task.
        """
        task, err, status_code = TaskService.get_task(task_id, current_user)
        if err:
            return None, err, status_code

        was_completed = task.status == "COMPLETED"

        # If explicit flag passed, set accordingly
        if completed_flag is True:
            task.status = "COMPLETED"
            task.completed_at = datetime.now(timezone.utc)
        elif completed_flag is False:
            task.status = "TODO"
            task.completed_at = None
        else:
            # Toggle current state
            if task.status == "COMPLETED":
                task.status = "TODO"
                task.completed_at = None
            else:
                task.status = "COMPLETED"
                task.completed_at = datetime.now(timezone.utc)

        db.session.commit()

        # Only send completion notification if the task actually transitioned to COMPLETED
        if not was_completed and task.status == "COMPLETED":
            # 1. Notify the task creator
            if task.creator:
                EmailService.send_task_completed_email(task, task.creator, current_user)

            # 2. If the assignee is different from the creator, notify the assignee as well
            if task.assignee and task.assigned_to and task.assigned_to != task.created_by:
                EmailService.send_task_completed_email(task, task.assignee, current_user)

        return task, None, 200

    @staticmethod
    def delete_task(task_id: str, current_user: User) -> Tuple[bool, Optional[Dict[str, Any]], int]:
        """
        Deletes a task record. Restricted strictly to the task creator.
        """
        task, err, status_code = TaskService.get_task(task_id, current_user)
        if err:
            return False, err, status_code

        if task.created_by != current_user.id:
            return False, {
                "code": "FORBIDDEN",
                "message": "Only the task creator is permitted to delete this task.",
            }, 403

        db.session.delete(task)
        db.session.commit()
        return True, None, 200

    @staticmethod
    def get_dashboard_stats(current_user: User) -> Dict[str, int]:
        """
        Computes task metrics scoped to the authenticated user.
        """
        user_tasks = Task.query.filter(
            or_(
                Task.created_by == current_user.id,
                Task.assigned_to == current_user.id,
            )
        ).all()

        total = len(user_tasks)
        todo = sum(1 for t in user_tasks if t.status == "TODO")
        in_progress = sum(1 for t in user_tasks if t.status == "IN_PROGRESS")
        completed = sum(1 for t in user_tasks if t.status == "COMPLETED")
        assigned_to_me = sum(1 for t in user_tasks if t.assigned_to == current_user.id)
        created_by_me = sum(1 for t in user_tasks if t.created_by == current_user.id)

        return {
            "total_tasks": total,
            "todo": todo,
            "in_progress": in_progress,
            "completed": completed,
            "assigned_to_me": assigned_to_me,
            "created_by_me": created_by_me,
        }
