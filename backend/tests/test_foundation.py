"""
Foundation Test Suite
Verifies application factory, database models, relationships, response helpers, and health route.
"""

import unittest
from datetime import datetime, timezone
from app import create_app
from app.extensions import db
from app.models import User, Task


class TestBackendFoundation(unittest.TestCase):
    def setUp(self):
        """Set up test application and in-memory database."""
        self.app = create_app("testing")
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

    def tearDown(self):
        """Clean up test database and context."""
        db.session.remove()
        db.drop_all()
        db.engine.dispose()
        self.app_context.pop()

    def test_health_endpoint(self):
        """Test GET /api/health returns operational status and 200."""
        response = self.client.get("/api/health")
        self.assertEqual(response.status_code, 200)
        json_data = response.get_json()
        self.assertTrue(json_data["success"])
        self.assertEqual(json_data["data"]["status"], "healthy")
        self.assertEqual(json_data["data"]["database"]["status"], "connected")

    def test_404_error_handler(self):
        """Test that unknown routes return standardized JSON error format."""
        response = self.client.get("/api/non-existent-route")
        self.assertEqual(response.status_code, 404)
        json_data = response.get_json()
        self.assertFalse(json_data["success"])
        self.assertEqual(json_data["error"]["code"], "NOT_FOUND")

    def test_user_and_task_models_and_relationships(self):
        """Test User and Task model creation, relationships, and serialization."""
        # Create creator user
        creator = User(
            google_id="google-creator-12345",
            name="Alice Creator",
            email="alice@example.com",
            profile_image="https://example.com/alice.jpg",
        )
        # Create assignee user
        assignee = User(
            google_id="google-assignee-67890",
            name="Bob Assignee",
            email="bob@example.com",
            profile_image="https://example.com/bob.jpg",
        )
        db.session.add_all([creator, assignee])
        db.session.commit()

        # Verify users exist
        self.assertIsNotNone(creator.id)
        self.assertIsNotNone(assignee.id)

        # Create Task
        task = Task(
            title="Complete Internship Task Management Module",
            description="Build robust Flask backend and Next.js frontend.",
            created_by=creator.id,
            assigned_to=assignee.id,
            status="IN_PROGRESS",
            priority="HIGH",
        )
        db.session.add(task)
        db.session.commit()

        # Test relationships
        self.assertEqual(task.creator.id, creator.id)
        self.assertEqual(task.creator.email, "alice@example.com")
        self.assertEqual(task.assignee.id, assignee.id)
        self.assertEqual(task.assignee.email, "bob@example.com")

        # Test user reverse relationships
        self.assertEqual(creator.created_tasks.count(), 1)
        self.assertEqual(assignee.assigned_tasks.count(), 1)

        # Test serialization
        user_dict = creator.to_dict()
        self.assertEqual(user_dict["name"], "Alice Creator")
        self.assertEqual(user_dict["email"], "alice@example.com")
        self.assertIn("id", user_dict)

        task_dict = task.to_dict(include_users=True)
        self.assertEqual(task_dict["title"], "Complete Internship Task Management Module")
        self.assertEqual(task_dict["status"], "IN_PROGRESS")
        self.assertEqual(task_dict["priority"], "HIGH")
        self.assertIsNotNone(task_dict["creator"])
        self.assertEqual(task_dict["creator"]["email"], "alice@example.com")
        self.assertIsNotNone(task_dict["assignee"])
        self.assertEqual(task_dict["assignee"]["email"], "bob@example.com")


if __name__ == "__main__":
    unittest.main()
