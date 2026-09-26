"""
Authentication Decorators
Provides route protection decorators to enforce valid JWT bearer tokens.
"""

from functools import wraps
from flask import request
import jwt
from app.extensions import db
from app.models.user import User
from app.services.auth_service import AuthService
from app.utils.responses import error_response


def token_required(f):
    """
    Decorator to protect API routes with JWT authentication.
    Extracts the Bearer token from the Authorization header, verifies signature,
    and injects `current_user` as a parameter to the decorated endpoint.
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get("Authorization")

        if not auth_header:
            return error_response(
                message="Authorization header is missing. Please provide 'Authorization: Bearer <token>'.",
                code="UNAUTHORIZED",
                status_code=401,
            )

        parts = auth_header.split(" ", 1)
        if len(parts) != 2 or parts[0].lower() != "bearer":
            return error_response(
                message="Invalid Authorization header format. Expected 'Bearer <token>'.",
                code="INVALID_HEADER_FORMAT",
                status_code=401,
            )

        token_str = parts[1].strip()

        try:
            payload = AuthService.decode_jwt_token(token_str)
            user_id = payload.get("sub")
            if not user_id:
                return error_response(
                    message="Malformed token: missing subject claim.",
                    code="INVALID_TOKEN",
                    status_code=401,
                )

            current_user = db.session.get(User, user_id)
            if not current_user:
                return error_response(
                    message="The user associated with this token was not found.",
                    code="USER_NOT_FOUND",
                    status_code=401,
                )

        except jwt.ExpiredSignatureError:
            return error_response(
                message="Authentication token has expired. Please sign in again.",
                code="TOKEN_EXPIRED",
                status_code=401,
            )
        except jwt.InvalidTokenError as e:
            return error_response(
                message=f"Invalid authentication token: {str(e)}",
                code="INVALID_TOKEN",
                status_code=401,
            )
        except Exception as e:
            return error_response(
                message="Authentication verification failed.",
                code="AUTH_FAILED",
                status_code=401,
            )

        return f(current_user, *args, **kwargs)

    return decorated
