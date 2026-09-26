"""
Task Model
Represents tasks tracked in the system, supporting assignment, priorities, and completion.
"""

import uuid
from datetime import datetime, timezone
from app.extensions import db
from app.models.types import GUID


class Task(db.Model):
    __tablename__ = "tasks"

    id = db.Column(GUID(), primary_key=True, default=uuid.uuid4)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)

    # Ownership & Assignment
    created_by = db.Column(
        GUID(),
        db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    assigned_to = db.Column(
        GUID(),
        db.ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Task Lifecycle & Priority
    status = db.Column(
        db.String(50),
        nullable=False,
        default="TODO",
        index=True,
    )
    priority = db.Column(
        db.String(50),
        nullable=False,
        default="MEDIUM",
        index=True,
    )

    # Dates
    due_date = db.Column(db.DateTime(timezone=True), nullable=True, index=True)
    created_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
    completed_at = db.Column(db.DateTime(timezone=True), nullable=True)

    # Relationships
    creator = db.relationship(
        "User",
        foreign_keys=[created_by],
        back_populates="created_tasks",
    )
    assignee = db.relationship(
        "User",
        foreign_keys=[assigned_to],
        back_populates="assigned_tasks",
    )

    def to_dict(self, include_users: bool = True) -> dict:
        """Serializes task record into a clean dictionary for JSON responses."""
        data = {
            "id": str(self.id),
            "title": self.title,
            "description": self.description,
            "created_by": str(self.created_by),
            "assigned_to": str(self.assigned_to) if self.assigned_to else None,
            "status": self.status,
            "priority": self.priority,
            "due_date": self.due_date.isoformat() if self.due_date else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }

        if include_users:
            data["creator"] = self.creator.to_dict() if self.creator else None
            data["assignee"] = self.assignee.to_dict() if self.assignee else None

        return data

    def __repr__(self) -> str:
        return f"<Task {self.title} [{self.status}] ({self.id})>"
