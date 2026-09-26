"""
Standardized API Response Helpers
Provides consistent JSON envelope formats for all API endpoints.
"""

from typing import Any, Optional, Dict
from flask import jsonify, Response


def success_response(
    data: Any = None,
    message: str = "Operation completed successfully",
    status_code: int = 200,
    meta: Optional[Dict[str, Any]] = None,
) -> tuple[Response, int]:
    """
    Constructs a standardized success response.

    Format:
    {
        "success": true,
        "message": "...",
        "data": { ... },
        "meta": { ... } # Optional pagination or auxiliary metadata
    }
    """
    payload: Dict[str, Any] = {
        "success": True,
        "message": message,
        "data": data if data is not None else {},
    }

    if meta is not None:
        payload["meta"] = meta

    return jsonify(payload), status_code


def error_response(
    message: str = "An unexpected error occurred",
    code: str = "INTERNAL_SERVER_ERROR",
    status_code: int = 500,
    details: Optional[Any] = None,
) -> tuple[Response, int]:
    """
    Constructs a standardized error response.

    Format:
    {
        "success": false,
        "error": {
            "code": "...",
            "message": "...",
            "details": ... # Optional validation or field error list
        }
    }
    """
    error_payload: Dict[str, Any] = {
        "code": code,
        "message": message,
    }

    if details is not None:
        error_payload["details"] = details

    payload = {
        "success": False,
        "error": error_payload,
    }

    return jsonify(payload), status_code
