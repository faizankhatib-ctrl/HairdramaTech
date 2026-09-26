"""
Validation Helpers
Provides common validation utilities for UUIDs, enums, and timestamps.
"""

import uuid
from datetime import datetime
from typing import Optional, Tuple

VALID_STATUSES = {"TODO", "IN_PROGRESS", "COMPLETED"}
VALID_PRIORITIES = {"LOW", "MEDIUM", "HIGH", "URGENT"}


def is_valid_uuid(val: str) -> bool:
    """Checks if a string is a valid UUID."""
    if not val:
        return False
    try:
        uuid_obj = uuid.UUID(str(val))
        return str(uuid_obj) == str(val).lower()
    except (ValueError, AttributeError, TypeError):
        return False


def parse_iso_datetime(date_str: Optional[str]) -> Tuple[Optional[datetime], Optional[str]]:
    """
    Parses ISO-8601 or YYYY-MM-DD date strings.
    Returns (datetime_obj, error_message).
    """
    if not date_str:
        return None, None

    date_str = str(date_str).strip()
    # Try parsing full ISO string
    try:
        # Handle 'Z' suffix for UTC
        normalized = date_str.replace("Z", "+00:00")
        dt = datetime.fromisoformat(normalized)
        return dt, None
    except ValueError:
        pass

    # Try parsing simple YYYY-MM-DD
    try:
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        return dt, None
    except ValueError:
        return None, f"Invalid date format: '{date_str}'. Expected ISO-8601 (e.g., '2026-10-01T12:00:00Z' or '2026-10-01')."
