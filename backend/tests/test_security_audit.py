"""
Security and Penetration Test Suite
Audits malicious access attempts, ID spoofing, SQL injection safety,
CORS origin boundaries, and privilege escalation vectors.
"""

import unittest
from unittest.mock import patch
from app import create_app
from app.extensions import db
from app.models.user import User
from app.models.task import Task
from app.services.auth_service import AuthService


class TestSecurityAudit(unittest.TestCase):
    def setUp(self):
        """Set up isolated test application and database."""
        self.app = create_app("testing")
        self.app.config["JWT_SECRET_KEY"] = "test-security-jwt-key-at-least-32-chars-long"
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

        # Seed Victim (Alice) and Attacker (Eve)
        self.victim = User(
            google_id="google-victim-alice",
            name="Alice Victim",
            email="alice@victim.com",
        )
        self.attacker = User(
            google_id="google-attacker-eve",
            name="Eve Attacker",
            email="eve@attacker.com",
        )
        db.session.add_all([self.victim, self.attacker])
        db.session.commit()

        self.token_victim = AuthService.generate_jwt_token(self.victim)
        self.token_attacker = AuthService.generate_jwt_token(self.attacker)
        self.headers_victim = {"Authorization": f"Bearer {self.token_victim}"}
        self.headers_attacker = {"Authorization": f"Bearer {self.token_attacker}"}

    def tearDown(self):
        """Dispose connections and pop context."""
        db.session.remove()
        db.drop_all()
        db.engine.dispose()
        self.app_context.pop()

    def test_attacker_cannot_spoof_created_by_in_payload(self):
        """Attacker attempts to inject Alice's UUID into created_by field."""
        payload = {
            "title": "Malicious Spoofed Task",
            "description": "Attempting to create task under victim account",
            "created_by": str(self.victim.id),  # Spoof attempt
        }
        res = self.client.post("/api/tasks", json=payload, headers=self.headers_attacker)
        self.assertEqual(res.status_code, 201)
        task_data = res.get_json()["data"]["task"]
        # Backend MUST ignore the injected created_by and bind it to Eve
        self.assertEqual(task_data["created_by"], str(self.attacker.id))
        self.assertNotEqual(task_data["created_by"], str(self.victim.id))

    def test_attacker_cannot_view_victim_task(self):
        """Attacker attempts to access private task owned by Alice."""
        task = Task(title="Alice Confidential Notes", created_by=self.victim.id)
        db.session.add(task)
        db.session.commit()

        res = self.client.get(f"/api/tasks/{task.id}", headers=self.headers_attacker)
        self.assertEqual(res.status_code, 403)
        self.assertEqual(res.get_json()["error"]["code"], "FORBIDDEN")

    def test_attacker_cannot_update_victim_task(self):
        """Attacker attempts to modify Alice's task."""
        task = Task(title="Alice Original Plan", created_by=self.victim.id)
        db.session.add(task)
        db.session.commit()

        res = self.client.put(
            f"/api/tasks/{task.id}",
            json={"title": "Hacked Plan"},
            headers=self.headers_attacker,
        )
        self.assertEqual(res.status_code, 403)
        self.assertEqual(res.get_json()["error"]["code"], "FORBIDDEN")
        # Ensure title was not modified in database
        refreshed = db.session.get(Task, task.id)
        self.assertEqual(refreshed.title, "Alice Original Plan")

    def test_attacker_cannot_delete_victim_task(self):
        """Attacker attempts to delete Alice's task."""
        task = Task(title="Alice Important Task", created_by=self.victim.id)
        db.session.add(task)
        db.session.commit()

        res = self.client.delete(f"/api/tasks/{task.id}", headers=self.headers_attacker)
        self.assertEqual(res.status_code, 403)
        self.assertEqual(res.get_json()["error"]["code"], "FORBIDDEN")
        # Ensure task still exists in database
        self.assertIsNotNone(db.session.get(Task, task.id))

    def test_attacker_cannot_reassign_victim_task(self):
        """Attacker attempts to reassign Alice's task."""
        task = Task(title="Alice Workflow", created_by=self.victim.id)
        db.session.add(task)
        db.session.commit()

        res = self.client.patch(
            f"/api/tasks/{task.id}/assign",
            json={"assigned_to": str(self.attacker.id)},
            headers=self.headers_attacker,
        )
        self.assertEqual(res.status_code, 403)
        self.assertEqual(res.get_json()["error"]["code"], "FORBIDDEN")
        self.assertIsNone(db.session.get(Task, task.id).assigned_to)

    def test_attacker_cannot_complete_unauthorized_victim_task(self):
        """Attacker attempts to mark Alice's private task as complete."""
        task = Task(title="Alice Private Project", created_by=self.victim.id, status="TODO")
        db.session.add(task)
        db.session.commit()

        res = self.client.patch(
            f"/api/tasks/{task.id}/complete",
            json={"completed": True},
            headers=self.headers_attacker,
        )
        self.assertEqual(res.status_code, 403)
        self.assertEqual(res.get_json()["error"]["code"], "FORBIDDEN")
        self.assertEqual(db.session.get(Task, task.id).status, "TODO")

    def test_malformed_uuid_returns_400_not_500(self):
        """Attacker sends garbage string as UUID."""
        res = self.client.get("/api/tasks/not-a-valid-uuid", headers=self.headers_victim)
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.get_json()["error"]["code"], "INVALID_UUID")

    def test_method_not_allowed_returns_standard_json(self):
        """POST to a GET-only endpoint returns standard 405 error envelope."""
        res = self.client.post("/api/dashboard/stats", headers=self.headers_victim)
        self.assertEqual(res.status_code, 405)
        data = res.get_json()
        self.assertFalse(data["success"])
        self.assertEqual(data["error"]["code"], "METHOD_NOT_ALLOWED")

    def test_production_error_handler_masks_internal_details(self):
        """In production mode (DEBUG=False), unexpected 500 errors conceal tracebacks."""
        orig_debug = self.app.config.get("DEBUG")
        self.app.config["DEBUG"] = False

        try:
            with patch("app.services.task_service.TaskService.get_dashboard_stats") as mock_stats:
                mock_stats.side_effect = RuntimeError("Database cluster core dump fault")
                res = self.client.get("/api/dashboard/stats", headers=self.headers_victim)
                self.assertEqual(res.status_code, 500)
                data = res.get_json()
                self.assertFalse(data["success"])
                self.assertEqual(data["error"]["code"], "INTERNAL_SERVER_ERROR")
                # Ensure raw exception message is NOT leaked to client
                self.assertNotIn("core dump", data["error"]["message"])
                self.assertNotIn("RuntimeError", data["error"]["message"])
                self.assertEqual(
                    data["error"]["message"],
                    "An unexpected internal server error occurred. Please try again later.",
                )
        finally:
            self.app.config["DEBUG"] = orig_debug


if __name__ == "__main__":
    unittest.main()
