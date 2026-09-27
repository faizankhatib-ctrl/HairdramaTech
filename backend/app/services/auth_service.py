"""
Authentication Service
Handles Google ID token verification, user upsert logic, and JWT issuance & validation.
"""

from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional
import jwt
import requests
from flask import current_app
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests

from app.extensions import db
from app.models.user import User


class AuthService:
    """Encapsulates authentication, OAuth verification, and token management."""

    @staticmethod
    def exchange_code_for_user_info(code: str, redirect_uri: Optional[str] = None) -> Dict[str, Any]:
        """
        Exchanges an OAuth 2.0 authorization code for tokens and extracts verified user info.
        
        Args:
            code: The authorization code returned by Google OAuth.
            redirect_uri: The redirect URI used during the initial authorization request.
            
        Returns:
            Normalized dictionary containing verified user attributes:
            {'google_id': ..., 'email': ..., 'name': ..., 'profile_image': ...}
        """
        client_id = current_app.config.get("GOOGLE_CLIENT_ID")
        client_secret = current_app.config.get("GOOGLE_CLIENT_SECRET")
        if not client_id or not client_secret:
            raise ValueError("GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET must be configured in environment.")

        token_endpoint = "https://oauth2.googleapis.com/token"
        payload = {
            "code": code,
            "client_id": client_id,
            "client_secret": client_secret,
            "redirect_uri": redirect_uri or current_app.config.get("FRONTEND_URL", "http://localhost:3000"),
            "grant_type": "authorization_code",
        }
        res = requests.post(token_endpoint, data=payload, timeout=10)
        if not res.ok:
            error_msg = res.text
            try:
                error_data = res.json()
                error_msg = error_data.get("error_description") or error_data.get("error") or error_msg
            except Exception:
                pass
            raise ValueError(f"Google token exchange failed: {error_msg}")

        token_data = res.json()
        raw_id_token = token_data.get("id_token")
        if raw_id_token:
            return AuthService.verify_google_id_token(raw_id_token)

        access_token = token_data.get("access_token")
        if not access_token:
            raise ValueError("No id_token or access_token received from Google.")

        userinfo_res = requests.get(
            "https://www.googleapis.com/oauth2/v3/userinfo",
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=10,
        )
        if not userinfo_res.ok:
            raise ValueError("Failed to retrieve user profile from Google.")

        info = userinfo_res.json()
        return {
            "google_id": info.get("sub"),
            "email": info.get("email", "").lower().strip(),
            "name": info.get("name") or info.get("email", "").split("@")[0],
            "profile_image": info.get("picture"),
        }

    @staticmethod
    def verify_google_id_token(token_str: str) -> Dict[str, Any]:
        """
        Verifies a Google OAuth 2.0 ID Token server-side using Google's public keys.
        
        Args:
            token_str: The raw Google ID token (JWT) provided by the client.
            
        Returns:
            Normalized dictionary containing verified user attributes:
            {'google_id': ..., 'email': ..., 'name': ..., 'profile_image': ...}
            
        Raises:
            ValueError: If the token is invalid, expired, or audience does not match.
        """
        client_id = current_app.config.get("GOOGLE_CLIENT_ID")
        
        # Verify token cryptographically against Google's certificates
        # Note: If client_id is configured, audience verification is strictly enforced
        request = google_requests.Request()
        id_info = id_token.verify_oauth2_token(
            token_str,
            request,
            audience=client_id if client_id else None,
        )

        google_id = id_info.get("sub")
        email = id_info.get("email")

        if not google_id or not email:
            raise ValueError("Token payload is missing essential claims (sub or email).")

        return {
            "google_id": google_id,
            "email": email.lower().strip(),
            "name": id_info.get("name") or email.split("@")[0],
            "profile_image": id_info.get("picture"),
        }

    @staticmethod
    def upsert_user(user_data: Dict[str, Any]) -> User:
        """
        Finds or creates a user record based on verified Google identity.
        Maintains uniqueness on email and google_id.
        """
        google_id = user_data["google_id"]
        email = user_data["email"]

        # First, search by google_id
        user = User.query.filter_by(google_id=google_id).first()

        # If not found by google_id, check by email (handles re-linking or pre-existing accounts)
        if not user:
            user = User.query.filter_by(email=email).first()

        if user:
            # Update existing profile with latest Google data
            user.google_id = google_id
            user.name = user_data.get("name") or user.name
            if user_data.get("profile_image"):
                user.profile_image = user_data.get("profile_image")
        else:
            # Create new user record
            user = User(
                google_id=google_id,
                email=email,
                name=user_data.get("name", email.split("@")[0]),
                profile_image=user_data.get("profile_image"),
            )
            db.session.add(user)

        db.session.commit()
        return user

    @staticmethod
    def generate_jwt_token(user: User) -> str:
        """
        Issues a signed JSON Web Token (JWT) representing the user's session.
        
        Payload contains:
        - sub: User UUID
        - email: User's email
        - name: User's full name
        - iat: Issued at timestamp (UTC)
        - exp: Expiration timestamp (UTC)
        """
        secret_key = current_app.config.get("JWT_SECRET_KEY")
        expiration_days = current_app.config.get("JWT_EXPIRATION_DAYS", 7)
        now = datetime.now(timezone.utc)

        payload = {
            "sub": str(user.id),
            "email": user.email,
            "name": user.name,
            "iat": now,
            "exp": now + timedelta(days=expiration_days),
        }

        token = jwt.encode(payload, secret_key, algorithm="HS256")
        # Ensure return type is string (PyJWT v2 returns str)
        return token if isinstance(token, str) else token.decode("utf-8")

    @staticmethod
    def decode_jwt_token(token_str: str) -> Dict[str, Any]:
        """
        Decodes and cryptographically verifies an application JWT.
        
        Returns:
            Dict containing token claims.
            
        Raises:
            jwt.ExpiredSignatureError: If token has expired.
            jwt.InvalidTokenError: If signature or format is invalid.
        """
        secret_key = current_app.config.get("JWT_SECRET_KEY")
        return jwt.decode(token_str, secret_key, algorithms=["HS256"])
