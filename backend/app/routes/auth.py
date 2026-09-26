"""
Authentication Routes
Endpoints for Google OAuth 2.0 exchange, user profile inspection, and session logout.
"""

from flask import Blueprint, request, current_app
from app.services.auth_service import AuthService
from app.utils.responses import success_response, error_response
from app.utils.decorators import token_required

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/google", methods=["POST"])
def google_auth():
    """
    POST /api/auth/google
    Authenticates a user via a Google ID token from Google Identity Services.
    Verifies the token server-side, creates or updates the user profile,
    and returns a backend session JWT.
    """
    data = request.get_json(silent=True)
    if data is None:
        return error_response(
            message="Invalid request payload. Expected JSON body.",
            code="INVALID_PAYLOAD",
            status_code=400,
        )

    # Google Identity Services sends 'credential', some clients may send 'id_token' or 'token'
    token_str = data.get("credential") or data.get("id_token") or data.get("token")
    if not token_str:
        return error_response(
            message="Missing Google ID token. Please provide 'credential' or 'id_token'.",
            code="MISSING_TOKEN",
            status_code=400,
        )

    try:
        # Step 1: Verify token server-side using Google's public certificates
        google_user_info = AuthService.verify_google_id_token(token_str)

        # Step 2: Upsert user in the database (find or create)
        user = AuthService.upsert_user(google_user_info)

        # Step 3: Issue our backend JWT
        access_token = AuthService.generate_jwt_token(user)

        return success_response(
            data={
                "token": access_token,
                "user": user.to_dict(),
            },
            message="User authenticated successfully.",
            status_code=200,
        )

    except ValueError as e:
        current_app.logger.warning(f"Google token verification failed: {e}")
        return error_response(
            message=f"Google token verification failed: {str(e)}",
            code="INVALID_GOOGLE_TOKEN",
            status_code=401,
        )
    except Exception as e:
        current_app.logger.exception(f"Unexpected error during Google authentication: {e}")
        return error_response(
            message="An unexpected error occurred during authentication.",
            code="AUTH_PROCESSING_ERROR",
            status_code=500,
        )


@auth_bp.route("/me", methods=["GET"])
@token_required
def get_current_user_profile(current_user):
    """
    GET /api/auth/me
    Returns the authenticated user's profile.
    Protected by @token_required.
    """
    return success_response(
        data={"user": current_user.to_dict()},
        message="Current user profile retrieved successfully.",
    )


@auth_bp.route("/logout", methods=["POST"])
def logout():
    """
    POST /api/auth/logout
    Stateless JWT logout endpoint. Notifies client to clear local token storage.
    """
    return success_response(
        data={},
        message="Successfully logged out.",
    )
