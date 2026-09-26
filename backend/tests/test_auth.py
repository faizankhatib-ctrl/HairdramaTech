"""
Authentication Test Suite
Verifies Google OAuth token exchange, user creation/upsert, JWT generation,
@token_required decorator, and protected profile routes using mocked Google verification.
"""

import unittest
from unittest.mock import patch
from datetime import datetime, timezone, timedelta
import jwt
from app import create_app
from app.extensions import db
from app.models.user import User


class TestAuth(unittest.TestCase):
    def setUp(self):
        """Set up test environment and in-memory database."""
        self.app = create_app("testing")
        self.app.config["JWT_SECRET_KEY"] = "test-jwt-secret-key-at-least-32-chars-long"
        self.app.config["GOOGLE_CLIENT_ID"] = "test-google-client-id.apps.googleusercontent.com"
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

    def tearDown(self):
        """Tear down database and pop context."""
        db.session.remove()
        db.drop_all()
        db.engine.dispose()
        self.app_context.pop()

    def test_missing_google_token(self):
        """Test 1: POST /api/auth/google rejects requests missing an ID token."""
        response = self.client.post("/api/auth/google", json={})
        self.assertEqual(response.status_code, 400)
        data = response.get_json()
        self.assertFalse(data["success"])
        self.assertEqual(data["error"]["code"], "MISSING_TOKEN")

    @patch("google.oauth2.id_token.verify_oauth2_token")
    def test_invalid_google_token(self, mock_verify):
        """Test 2: POST /api/auth/google returns 401 when Google rejects the token."""
        mock_verify.side_effect = ValueError("Token signature verification failed")
        
        response = self.client.post(
            "/api/auth/google",
            json={"credential": "invalid-bogus-token"},
        )
        self.assertEqual(response.status_code, 401)
        data = response.get_json()
        self.assertFalse(data["success"])
        self.assertEqual(data["error"]["code"], "INVALID_GOOGLE_TOKEN")

    @patch("google.oauth2.id_token.verify_oauth2_token")
    def test_valid_google_auth_new_user_creation(self, mock_verify):
        """Test 3 & 4: Valid Google authentication creates a new user and returns JWT."""
        mock_verify.return_value = {
            "sub": "google-uid-1001",
            "email": "sarah.connor@example.com",
            "name": "Sarah Connor",
            "picture": "https://lh3.googleusercontent.com/avatar1.jpg",
            "email_verified": True,
        }

        response = self.client.post(
            "/api/auth/google",
            json={"credential": "mocked-valid-google-jwt"},
        )
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertTrue(data["success"])
        self.assertIn("token", data["data"])
        
        user_info = data["data"]["user"]
        self.assertEqual(user_info["email"], "sarah.connor@example.com")
        self.assertEqual(user_info["name"], "Sarah Connor")
        self.assertEqual(user_info["profile_image"], "https://lh3.googleusercontent.com/avatar1.jpg")

        # Verify record exists in database
        db_user = User.query.filter_by(email="sarah.connor@example.com").first()
        self.assertIsNotNone(db_user)
        self.assertEqual(db_user.google_id, "google-uid-1001")

    @patch("google.oauth2.id_token.verify_oauth2_token")
    def test_existing_user_login_upsert(self, mock_verify):
        """Test 5: Logging in an existing user updates their profile without duplicating."""
        # Pre-seed user with older name/avatar
        existing_user = User(
            google_id="google-uid-2002",
            email="john.doe@example.com",
            name="John Doe Old",
            profile_image="https://example.com/old_pic.jpg",
        )
        db.session.add(existing_user)
        db.session.commit()
        original_id = existing_user.id

        # Mock updated info from Google login
        mock_verify.return_value = {
            "sub": "google-uid-2002",
            "email": "john.doe@example.com",
            "name": "John Doe Updated",
            "picture": "https://lh3.googleusercontent.com/new_pic.jpg",
        }

        response = self.client.post(
            "/api/auth/google",
            json={"credential": "mocked-valid-google-jwt-2"},
        )
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data["data"]["user"]["name"], "John Doe Updated")
        self.assertEqual(data["data"]["user"]["profile_image"], "https://lh3.googleusercontent.com/new_pic.jpg")

        # Verify no duplicate user was created
        all_users = User.query.filter_by(email="john.doe@example.com").all()
        self.assertEqual(len(all_users), 1)
        self.assertEqual(all_users[0].id, original_id)

    @patch("google.oauth2.id_token.verify_oauth2_token")
    def test_get_current_user_profile_with_valid_jwt(self, mock_verify):
        """Test 6: GET /api/auth/me succeeds with a valid JWT Bearer token."""
        mock_verify.return_value = {
            "sub": "google-uid-3003",
            "email": "auth.user@example.com",
            "name": "Auth User",
            "picture": "https://example.com/auth.jpg",
        }

        # Sign in to get JWT
        login_res = self.client.post(
            "/api/auth/google",
            json={"credential": "mock-token-3"},
        )
        token = login_res.get_json()["data"]["token"]

        # Call GET /api/auth/me with Bearer token
        me_res = self.client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        self.assertEqual(me_res.status_code, 200)
        data = me_res.get_json()
        self.assertTrue(data["success"])
        self.assertEqual(data["data"]["user"]["email"], "auth.user@example.com")

    def test_get_current_user_without_jwt(self):
        """Test 7: GET /api/auth/me rejects requests missing the Authorization header."""
        response = self.client.get("/api/auth/me")
        self.assertEqual(response.status_code, 401)
        data = response.get_json()
        self.assertFalse(data["success"])
        self.assertEqual(data["error"]["code"], "UNAUTHORIZED")

    def test_expired_and_invalid_jwt(self):
        """Test 8: GET /api/auth/me rejects invalid and expired JWTs."""
        # 1. Malformed token
        res_invalid = self.client.get(
            "/api/auth/me",
            headers={"Authorization": "Bearer invalid.token.string"},
        )
        self.assertEqual(res_invalid.status_code, 401)
        self.assertEqual(res_invalid.get_json()["error"]["code"], "INVALID_TOKEN")

        # 2. Expired token
        past_time = datetime.now(timezone.utc) - timedelta(hours=2)
        expired_payload = {
            "sub": "some-uuid",
            "email": "expired@example.com",
            "iat": past_time - timedelta(hours=1),
            "exp": past_time,
        }
        expired_token = jwt.encode(
            expired_payload,
            self.app.config["JWT_SECRET_KEY"],
            algorithm="HS256",
        )
        res_expired = self.client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {expired_token}"},
        )
        self.assertEqual(res_expired.status_code, 401)
        self.assertEqual(res_expired.get_json()["error"]["code"], "TOKEN_EXPIRED")

    def test_logout(self):
        """Test 9: POST /api/auth/logout returns clean confirmation."""
        response = self.client.post("/api/auth/logout")
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertTrue(data["success"])
        self.assertEqual(data["message"], "Successfully logged out.")


if __name__ == "__main__":
    unittest.main()
