"""
User Service
Provides business logic for querying and filtering user profiles.
"""

from typing import List, Dict, Any, Optional
from sqlalchemy import or_
from app.models.user import User


class UserService:
    """Service handling user directory search and profile listings."""

    @staticmethod
    def get_assignable_users(search: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Retrieves public user profiles for task assignment dropdowns.
        Excludes sensitive authentication identifiers.
        
        Args:
            search: Optional case-insensitive substring to filter by name or email.
            
        Returns:
            List of sanitized user dictionaries.
        """
        query = User.query

        if search:
            search_pattern = f"%{search.strip()}%"
            query = query.filter(
                or_(
                    User.name.ilike(search_pattern),
                    User.email.ilike(search_pattern),
                )
            )

        users = query.order_by(User.name.asc()).all()

        return [
            {
                "id": str(u.id),
                "name": u.name,
                "email": u.email,
                "profile_image": u.profile_image,
            }
            for u in users
        ]
