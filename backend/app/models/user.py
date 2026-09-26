"""
User Model
Represents registered users authenticated via Google OAuth 2.0.
"""

import uuid
from datetime import datetime, timezone
from app.extensions import db
from app.models.types import GUID


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(GUID(), primary_key=True, default=uuid.uuid4)
    google_id = db.Column(db.String(255), unique=True, nullable=False, index=True)
    name = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    profile_image = db.Column(db.Text, nullable=True)
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

    # Relationships
    # Tasks created by this user
    created_tasks = db.relationship(
        "Task",
        foreign_keys="Task.created_by",
        back_populates="creator",
        cascade="all, delete-orphan",
        lazy="dynamic",
    )

    # Tasks assigned to this user
    assigned_tasks = db.relationship(
        "Task",
        foreign_keys="Task.assigned_to",
        back_populates="assignee",
        lazy="dynamic",
    )

    def to_dict(self) -> dict:
        """Serializes user record into a clean dictionary for JSON responses."""
        return {
            "id": str(self.id),
            "google_id": self.google_id,
            "name": self.name,
            "email": self.email,
            "profile_image": self.profile_image,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def __repr__(self) -> str:
        return f"<User {self.email} ({self.id})>"
