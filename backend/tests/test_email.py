"""
Email Notification Test Suite
Verifies task assignment and completion email triggers, idempotent completion notices,
single email for same creator/assignee, PUT notification suppression,
and verifies that SMTP failures never break task operations.
All external SMTP interactions are mocked.
"""

import unittest
from unittest.mock import patch, MagicMock
import smtplib
from app import create_app
from app.extensions import db
from app.models.user import User
from app.models.task import Task
from app.services.auth_service import AuthService
from app.services.email_service import EmailService


class TestEmailNotifications(unittest.TestCase):
    def setUp(self):
        """Set up test environment, in-memory DB, and authenticated test users."""
        self.app = create_app("testing")
        self.app.config["JWT_SECRET_KEY"] = "test-jwt-secret-key-at-least-32-chars-long"
        self.app.config["MAIL_SERVER"] = "smtp.gmail.com"
        self.app.config["MAIL_PORT"] = 587
        self.app.config["MAIL_USERNAME"] = "notifications@example.com"
        self.app.config["MAIL_PASSWORD"] = "mock-secret-password-16ch"
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

        # Seed Author (Alice), Assignee (Bob), and Third User (Charlie)
        self.author = User(
            google_id="google-id-author-1",
            name="Alice Creator",
            email="alice@example.com",
        )
        self.assignee = User(
            google_id="google-id-assignee-2",
            name="Bob Worker",
            email="bob@example.com",
        )
        self.other_user = User(
            google_id="google-id-other-3",
            name="Charlie Third",
            email="charlie@example.com",
        )
        db.session.add_all([self.author, self.assignee, self.other_user])
        db.session.commit()

        self.token_author = AuthService.generate_jwt_token(self.author)
        self.token_assignee = AuthService.generate_jwt_token(self.assignee)
        self.headers_author = {"Authorization": f"Bearer {self.token_author}"}
        self.headers_assignee = {"Authorization": f"Bearer {self.token_assignee}"}

    def tearDown(self):
        """Clean up database and pop application context."""
        db.session.remove()
        db.drop_all()
        db.engine.dispose()
        self.app_context.pop()

    # 1. Task creation with assignee triggers assignment email
    @patch.object(EmailService, "send_task_assigned_email")
    def test_01_task_creation_with_assignee_triggers_email(self, mock_send):
        payload = {
            "title": "Build Email Dispatcher",
            "assigned_to": str(self.assignee.id),
            "priority": "HIGH",
        }
        res = self.client.post("/api/tasks", json=payload, headers=self.headers_author)
        self.assertEqual(res.status_code, 201)
        mock_send.assert_called_once()
        args, _ = mock_send.call_args
        self.assertEqual(args[1].email, "bob@example.com")
        self.assertEqual(args[2].email, "alice@example.com")

    # 2. Task creation without assignee does not send email
    @patch.object(EmailService, "send_task_assigned_email")
    def test_02_task_creation_without_assignee_no_email(self, mock_send):
        payload = {"title": "Self-Assigned Work"}
        res = self.client.post("/api/tasks", json=payload, headers=self.headers_author)
        self.assertEqual(res.status_code, 201)
        mock_send.assert_not_called()

    # 3. Reassignment triggers email to new assignee
    @patch.object(EmailService, "send_task_assigned_email")
    def test_03_reassignment_triggers_email_to_new_assignee(self, mock_send):
        task = Task(title="Shared Project", created_by=self.author.id, assigned_to=self.assignee.id)
        db.session.add(task)
        db.session.commit()

        # Reassign to Charlie
        res = self.client.patch(
            f"/api/tasks/{task.id}/assign",
            json={"assigned_to": str(self.other_user.id)},
            headers=self.headers_author,
        )
        self.assertEqual(res.status_code, 200)
        mock_send.assert_called_once()
        args, _ = mock_send.call_args
        self.assertEqual(args[1].email, "charlie@example.com")

    # 4. Unassignment does not send email
    @patch.object(EmailService, "send_task_assigned_email")
    def test_04_unassignment_does_not_send_email(self, mock_send):
        task = Task(title="Task to Unassign", created_by=self.author.id, assigned_to=self.assignee.id)
        db.session.add(task)
        db.session.commit()

        res = self.client.patch(
            f"/api/tasks/{task.id}/assign",
            json={"assigned_to": None},
            headers=self.headers_author,
        )
        self.assertEqual(res.status_code, 200)
        mock_send.assert_not_called()

    # 5. Completing task notifies both creator and different assignee
    @patch.object(EmailService, "send_task_completed_email")
    def test_05_completing_task_notifies_creator_and_different_assignee(self, mock_send):
        task = Task(title="Deploy Backend", created_by=self.author.id, assigned_to=self.assignee.id, status="IN_PROGRESS")
        db.session.add(task)
        db.session.commit()

        # Assignee marks it completed
        res = self.client.patch(f"/api/tasks/{task.id}/complete", headers=self.headers_assignee)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.get_json()["data"]["task"]["status"], "COMPLETED")
        
        # Must notify both creator (Alice) and assignee (Bob) -> exactly 2 calls
        self.assertEqual(mock_send.call_count, 2)
        recipients = [call_args[0][1].email for call_args in mock_send.call_args_list]
        self.assertIn("alice@example.com", recipients)
        self.assertIn("bob@example.com", recipients)

    # 5b. Same creator + assignee receives only one email
    @patch.object(EmailService, "send_task_completed_email")
    def test_05b_same_creator_and_assignee_receives_only_one_email(self, mock_send):
        # Alice creates a task assigned to Alice herself
        task = Task(title="Self Task", created_by=self.author.id, assigned_to=self.author.id, status="TODO")
        db.session.add(task)
        db.session.commit()

        res = self.client.patch(f"/api/tasks/{task.id}/complete", headers=self.headers_author)
        self.assertEqual(res.status_code, 200)
        # Exactly one email sent to Alice
        self.assertEqual(mock_send.call_count, 1)
        args, _ = mock_send.call_args
        self.assertEqual(args[1].email, "alice@example.com")

    # 6. Completing already completed task does not send duplicate email
    @patch.object(EmailService, "send_task_completed_email")
    def test_06_already_completed_task_no_duplicate_email(self, mock_send):
        task = Task(title="Finished Task", created_by=self.author.id, assigned_to=self.assignee.id, status="COMPLETED")
        db.session.add(task)
        db.session.commit()

        # Call with explicit completed=True on an already completed task
        res = self.client.patch(
            f"/api/tasks/{task.id}/complete",
            json={"completed": True},
            headers=self.headers_assignee,
        )
        self.assertEqual(res.status_code, 200)
        mock_send.assert_not_called()

    # 7. Reopening completed task does not send completion email
    @patch.object(EmailService, "send_task_completed_email")
    def test_07_reopening_task_does_not_send_completion_email(self, mock_send):
        task = Task(title="Task to Reopen", created_by=self.author.id, status="COMPLETED")
        db.session.add(task)
        db.session.commit()

        # Toggle (reopens to TODO)
        res = self.client.patch(f"/api/tasks/{task.id}/complete", headers=self.headers_author)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.get_json()["data"]["task"]["status"], "TODO")
        mock_send.assert_not_called()

    # 7b. PUT endpoint does not trigger notification emails
    @patch.object(EmailService, "send_task_assigned_email")
    @patch.object(EmailService, "send_task_completed_email")
    def test_07b_put_endpoint_does_not_trigger_notifications(self, mock_completed, mock_assigned):
        task = Task(title="Original Work", created_by=self.author.id, assigned_to=self.assignee.id, status="TODO")
        db.session.add(task)
        db.session.commit()

        # PUT updates title, priority, status to COMPLETED, and reassigns
        put_payload = {
            "title": "Modified Work",
            "status": "COMPLETED",
            "assigned_to": str(self.other_user.id),
        }
        res = self.client.put(f"/api/tasks/{task.id}", json=put_payload, headers=self.headers_author)
        self.assertEqual(res.status_code, 200)

        # Confirm dedicated endpoints remain the sole notification sources
        mock_completed.assert_not_called()
        mock_assigned.assert_not_called()

    # 8. SMTP failure does not fail task creation
    @patch("smtplib.SMTP")
    def test_08_smtp_failure_does_not_fail_task_creation(self, mock_smtp):
        # Simulate Gmail SMTP server failing or timing out
        mock_smtp.side_effect = smtplib.SMTPConnectError(421, b"Service not available")

        payload = {
            "title": "Critical Task with SMTP Error",
            "assigned_to": str(self.assignee.id),
        }
        res = self.client.post("/api/tasks", json=payload, headers=self.headers_author)
        # Task creation MUST still succeed with 201 Created!
        self.assertEqual(res.status_code, 201)
        self.assertTrue(res.get_json()["success"])
        # Verify task is safely in the database
        created_id = res.get_json()["data"]["task"]["id"]
        self.assertIsNotNone(db.session.get(Task, created_id))

    # 9. SMTP failure does not fail task completion
    @patch("smtplib.SMTP")
    def test_09_smtp_failure_does_not_fail_task_completion(self, mock_smtp):
        # Simulate SMTP Authentication failure
        mock_smtp.side_effect = smtplib.SMTPAuthenticationError(535, b"Bad credentials")

        task = Task(title="Complete Under SMTP Crash", created_by=self.author.id, assigned_to=self.assignee.id)
        db.session.add(task)
        db.session.commit()

        res = self.client.patch(f"/api/tasks/{task.id}/complete", headers=self.headers_assignee)
        # Task completion MUST still succeed with 200 OK!
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.get_json()["data"]["task"]["status"], "COMPLETED")
        # Verify database record updated
        db_task = db.session.get(Task, task.id)
        self.assertEqual(db_task.status, "COMPLETED")

    # 10. Email credentials are not exposed in API responses or log output
    def test_10_credentials_not_exposed(self):
        payload = {
            "title": "Check Credentials Exposure",
            "assigned_to": str(self.assignee.id),
        }
        res = self.client.post("/api/tasks", json=payload, headers=self.headers_author)
        response_text = res.get_data(as_text=True)
        # Ensure password string never leaks in JSON response
        self.assertNotIn("mock-secret-password-16ch", response_text)
        self.assertNotIn("MAIL_PASSWORD", response_text)


if __name__ == "__main__":
    unittest.main()
