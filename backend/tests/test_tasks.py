"""
Task and User API Test Suite
Covers all 24 required test scenarios for User directory, Task CRUD,
Authorization, Assignment, Completion toggle, Filtering, Scope, and Dashboard statistics.
"""

import unittest
from datetime import datetime, timezone, timedelta
import jwt
from app import create_app
from app.extensions import db
from app.models.user import User
from app.models.task import Task
from app.services.auth_service import AuthService


class TestTaskManagement(unittest.TestCase):
    def setUp(self):
        """Set up testing application, in-memory DB, and test users."""
        self.app = create_app("testing")
        self.app.config["JWT_SECRET_KEY"] = "test-jwt-secret-key-at-least-32-chars-long"
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

        # Seed three distinct users for role and authorization testing
        self.user_a = User(
            google_id="google-id-alice-101",
            name="Alice Author",
            email="alice@example.com",
            profile_image="https://example.com/alice.jpg",
        )
        self.user_b = User(
            google_id="google-id-bob-102",
            name="Bob Assignee",
            email="bob@example.com",
            profile_image="https://example.com/bob.jpg",
        )
        self.user_c = User(
            google_id="google-id-charlie-103",
            name="Charlie Outsider",
            email="charlie@example.com",
            profile_image="https://example.com/charlie.jpg",
        )
        db.session.add_all([self.user_a, self.user_b, self.user_c])
        db.session.commit()

        # Generate tokens
        self.token_a = AuthService.generate_jwt_token(self.user_a)
        self.token_b = AuthService.generate_jwt_token(self.user_b)
        self.token_c = AuthService.generate_jwt_token(self.user_c)

        self.headers_a = {"Authorization": f"Bearer {self.token_a}"}
        self.headers_b = {"Authorization": f"Bearer {self.token_b}"}
        self.headers_c = {"Authorization": f"Bearer {self.token_c}"}

    def tearDown(self):
        """Clean up database and pop application context."""
        db.session.remove()
        db.drop_all()
        db.engine.dispose()
        self.app_context.pop()

    # 1. GET users authenticated
    def test_01_get_users_authenticated(self):
        response = self.client.get("/api/users", headers=self.headers_a)
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertTrue(data["success"])
        users = data["data"]["users"]
        self.assertEqual(len(users), 3)

        # Confirm sensitive data like google_id is not exposed
        for u in users:
            self.assertIn("id", u)
            self.assertIn("name", u)
            self.assertIn("email", u)
            self.assertIn("profile_image", u)
            self.assertNotIn("google_id", u)

        # Test optional search
        search_res = self.client.get("/api/users?search=bob", headers=self.headers_a)
        search_data = search_res.get_json()["data"]["users"]
        self.assertEqual(len(search_data), 1)
        self.assertEqual(search_data[0]["name"], "Bob Assignee")

    # 2. GET users without authentication
    def test_02_get_users_without_auth(self):
        response = self.client.get("/api/users")
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.get_json()["error"]["code"], "UNAUTHORIZED")

    # 3. Create task successfully
    def test_03_create_task(self):
        payload = {
            "title": "Design System Architecture",
            "description": "Establish tokens, components, and responsive grid.",
            "assigned_to": str(self.user_b.id),
            "priority": "HIGH",
            "status": "TODO",
            "due_date": "2026-10-15T18:00:00Z",
        }
        response = self.client.post("/api/tasks", json=payload, headers=self.headers_a)
        self.assertEqual(response.status_code, 201)
        data = response.get_json()
        self.assertTrue(data["success"])
        task = data["data"]["task"]
        self.assertEqual(task["title"], "Design System Architecture")
        self.assertEqual(task["created_by"], str(self.user_a.id))
        self.assertEqual(task["assigned_to"], str(self.user_b.id))
        self.assertEqual(task["priority"], "HIGH")
        self.assertEqual(task["status"], "TODO")

    # 4. Create task without title
    def test_04_create_task_without_title(self):
        payload = {"title": "   ", "priority": "MEDIUM"}
        response = self.client.post("/api/tasks", json=payload, headers=self.headers_a)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.get_json()["error"]["code"], "MISSING_TITLE")

    # 5. Create task with invalid priority
    def test_05_create_task_with_invalid_priority(self):
        payload = {"title": "Test Task", "priority": "SUPER_MAX"}
        response = self.client.post("/api/tasks", json=payload, headers=self.headers_a)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.get_json()["error"]["code"], "INVALID_PRIORITY")

    # 6. Create task with invalid status
    def test_06_create_task_with_invalid_status(self):
        payload = {"title": "Test Task", "status": "UNKNOWN_STATUS"}
        response = self.client.post("/api/tasks", json=payload, headers=self.headers_a)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.get_json()["error"]["code"], "INVALID_STATUS")

    # 7. Create task with invalid assignee
    def test_07_create_task_with_invalid_assignee(self):
        payload = {"title": "Test Task", "assigned_to": "00000000-0000-0000-0000-000000000000"}
        response = self.client.post("/api/tasks", json=payload, headers=self.headers_a)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.get_json()["error"]["code"], "INVALID_ASSIGNEE")

    # 8. Get task
    def test_08_get_task(self):
        # Create a task as User A assigned to User B
        task = Task(
            title="Database Optimization",
            description="Add composite indexes on foreign keys.",
            created_by=self.user_a.id,
            assigned_to=self.user_b.id,
        )
        db.session.add(task)
        db.session.commit()

        # Both Author (A) and Assignee (B) can view
        res_a = self.client.get(f"/api/tasks/{task.id}", headers=self.headers_a)
        self.assertEqual(res_a.status_code, 200)
        self.assertEqual(res_a.get_json()["data"]["task"]["title"], "Database Optimization")

        res_b = self.client.get(f"/api/tasks/{task.id}", headers=self.headers_b)
        self.assertEqual(res_b.status_code, 200)

    # 9. Get unauthorized task
    def test_09_get_unauthorized_task(self):
        task = Task(
            title="Private Author Task",
            created_by=self.user_a.id,
        )
        db.session.add(task)
        db.session.commit()

        # User C is neither creator nor assignee
        res_c = self.client.get(f"/api/tasks/{task.id}", headers=self.headers_c)
        self.assertEqual(res_c.status_code, 403)
        self.assertEqual(res_c.get_json()["error"]["code"], "FORBIDDEN")

    # 10. Update authorized task
    def test_10_update_authorized_task(self):
        task = Task(
            title="Original Title",
            description="Original Description",
            created_by=self.user_a.id,
            assigned_to=self.user_b.id,
            priority="LOW",
        )
        db.session.add(task)
        db.session.commit()

        # Author updates title and priority
        update_payload = {
            "title": "Updated Title",
            "priority": "URGENT",
            "status": "IN_PROGRESS",
        }
        res = self.client.put(f"/api/tasks/{task.id}", json=update_payload, headers=self.headers_a)
        self.assertEqual(res.status_code, 200)
        updated_data = res.get_json()["data"]["task"]
        self.assertEqual(updated_data["title"], "Updated Title")
        self.assertEqual(updated_data["priority"], "URGENT")
        self.assertEqual(updated_data["status"], "IN_PROGRESS")

    # 11. Update unauthorized task
    def test_11_update_unauthorized_task(self):
        task = Task(title="Guarded Task", created_by=self.user_a.id)
        db.session.add(task)
        db.session.commit()

        # User C tries to update
        res = self.client.put(f"/api/tasks/{task.id}", json={"title": "Hacked Title"}, headers=self.headers_c)
        self.assertEqual(res.status_code, 403)
        self.assertEqual(res.get_json()["error"]["code"], "FORBIDDEN")

    # 12. Assign task
    def test_12_assign_task(self):
        task = Task(title="Delegated Work", created_by=self.user_a.id)
        db.session.add(task)
        db.session.commit()

        # Assign to User B
        res = self.client.patch(
            f"/api/tasks/{task.id}/assign",
            json={"assigned_to": str(self.user_b.id)},
            headers=self.headers_a,
        )
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.get_json()["data"]["task"]["assigned_to"], str(self.user_b.id))

        # Unassign
        res_unassign = self.client.patch(
            f"/api/tasks/{task.id}/assign",
            json={"assigned_to": None},
            headers=self.headers_a,
        )
        self.assertEqual(res_unassign.status_code, 200)
        self.assertIsNone(res_unassign.get_json()["data"]["task"]["assigned_to"])

    # 13. Assign to invalid user
    def test_13_assign_to_invalid_user(self):
        task = Task(title="Task to assign", created_by=self.user_a.id)
        db.session.add(task)
        db.session.commit()

        res = self.client.patch(
            f"/api/tasks/{task.id}/assign",
            json={"assigned_to": "11111111-2222-3333-4444-555555555555"},
            headers=self.headers_a,
        )
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.get_json()["error"]["code"], "INVALID_ASSIGNEE")

    # 14. Complete task (toggle)
    def test_14_complete_task(self):
        task = Task(title="Task to complete", created_by=self.user_a.id, assigned_to=self.user_b.id)
        db.session.add(task)
        db.session.commit()

        # Mark complete
        res_complete = self.client.patch(f"/api/tasks/{task.id}/complete", headers=self.headers_b)
        self.assertEqual(res_complete.status_code, 200)
        completed_task = res_complete.get_json()["data"]["task"]
        self.assertEqual(completed_task["status"], "COMPLETED")
        self.assertIsNotNone(completed_task["completed_at"])

        # Reopen (toggle)
        res_reopen = self.client.patch(f"/api/tasks/{task.id}/complete", headers=self.headers_b)
        self.assertEqual(res_reopen.status_code, 200)
        reopened_task = res_reopen.get_json()["data"]["task"]
        self.assertEqual(reopened_task["status"], "TODO")
        self.assertIsNone(reopened_task["completed_at"])

    # 15. Delete task as creator
    def test_15_delete_task_as_creator(self):
        task = Task(title="Disposable Task", created_by=self.user_a.id)
        db.session.add(task)
        db.session.commit()

        res = self.client.delete(f"/api/tasks/{task.id}", headers=self.headers_a)
        self.assertEqual(res.status_code, 200)
        self.assertTrue(res.get_json()["success"])

        # Verify gone from DB
        self.assertIsNone(db.session.get(Task, task.id))

    # 16. Attempt deletion as unauthorized user
    def test_16_attempt_deletion_as_unauthorized_user(self):
        task = Task(title="Protected Task", created_by=self.user_a.id, assigned_to=self.user_b.id)
        db.session.add(task)
        db.session.commit()

        # Even the assignee cannot delete; only creator can
        res = self.client.delete(f"/api/tasks/{task.id}", headers=self.headers_b)
        self.assertEqual(res.status_code, 403)
        self.assertEqual(res.get_json()["error"]["code"], "FORBIDDEN")

    # 17. Task filtering by status
    def test_17_task_filtering_by_status(self):
        t1 = Task(title="Task Todo", status="TODO", created_by=self.user_a.id)
        t2 = Task(title="Task In Prog", status="IN_PROGRESS", created_by=self.user_a.id)
        t3 = Task(title="Task Done", status="COMPLETED", created_by=self.user_a.id)
        db.session.add_all([t1, t2, t3])
        db.session.commit()

        res = self.client.get("/api/tasks?status=IN_PROGRESS", headers=self.headers_a)
        self.assertEqual(res.status_code, 200)
        tasks = res.get_json()["data"]["tasks"]
        self.assertEqual(len(tasks), 1)
        self.assertEqual(tasks[0]["status"], "IN_PROGRESS")

    # 18. Task filtering by priority
    def test_18_task_filtering_by_priority(self):
        t1 = Task(title="Low priority", priority="LOW", created_by=self.user_a.id)
        t2 = Task(title="Urgent priority", priority="URGENT", created_by=self.user_a.id)
        db.session.add_all([t1, t2])
        db.session.commit()

        res = self.client.get("/api/tasks?priority=URGENT", headers=self.headers_a)
        self.assertEqual(res.status_code, 200)
        tasks = res.get_json()["data"]["tasks"]
        self.assertEqual(len(tasks), 1)
        self.assertEqual(tasks[0]["priority"], "URGENT")

    # 19. Task search
    def test_19_task_search(self):
        t1 = Task(title="Implement OAuth 2.0 flow", description="Use Google ID token", created_by=self.user_a.id)
        t2 = Task(title="Write Frontend Components", description="Navbar and Sidebar", created_by=self.user_a.id)
        db.session.add_all([t1, t2])
        db.session.commit()

        res = self.client.get("/api/tasks?search=oauth", headers=self.headers_a)
        self.assertEqual(res.status_code, 200)
        tasks = res.get_json()["data"]["tasks"]
        self.assertEqual(len(tasks), 1)
        self.assertIn("OAuth", tasks[0]["title"])

    # 20. assigned_to_me scope
    def test_20_assigned_to_me_scope(self):
        t1 = Task(title="Assigned to Bob", created_by=self.user_a.id, assigned_to=self.user_b.id)
        t2 = Task(title="Created by Bob", created_by=self.user_b.id, assigned_to=self.user_a.id)
        db.session.add_all([t1, t2])
        db.session.commit()

        # Bob queries scope=assigned_to_me
        res = self.client.get("/api/tasks?scope=assigned_to_me", headers=self.headers_b)
        self.assertEqual(res.status_code, 200)
        tasks = res.get_json()["data"]["tasks"]
        self.assertEqual(len(tasks), 1)
        self.assertEqual(tasks[0]["title"], "Assigned to Bob")

    # 21. created_by_me scope
    def test_21_created_by_me_scope(self):
        t1 = Task(title="Alice Task 1", created_by=self.user_a.id)
        t2 = Task(title="Alice Task 2", created_by=self.user_a.id, assigned_to=self.user_b.id)
        t3 = Task(title="Bob Task", created_by=self.user_b.id)
        db.session.add_all([t1, t2, t3])
        db.session.commit()

        res = self.client.get("/api/tasks?scope=created_by_me", headers=self.headers_a)
        self.assertEqual(res.status_code, 200)
        tasks = res.get_json()["data"]["tasks"]
        self.assertEqual(len(tasks), 2)

    # 22. Dashboard statistics
    def test_22_dashboard_statistics(self):
        # Create varied tasks for Alice (user_a)
        t1 = Task(title="T1", status="TODO", created_by=self.user_a.id, assigned_to=self.user_a.id)
        t2 = Task(title="T2", status="IN_PROGRESS", created_by=self.user_a.id, assigned_to=self.user_b.id)
        t3 = Task(title="T3", status="COMPLETED", created_by=self.user_b.id, assigned_to=self.user_a.id)
        db.session.add_all([t1, t2, t3])
        db.session.commit()

        res = self.client.get("/api/dashboard/stats", headers=self.headers_a)
        self.assertEqual(res.status_code, 200)
        stats = res.get_json()["data"]
        self.assertEqual(stats["total_tasks"], 3)
        self.assertEqual(stats["todo"], 1)
        self.assertEqual(stats["in_progress"], 1)
        self.assertEqual(stats["completed"], 1)
        self.assertEqual(stats["assigned_to_me"], 2)  # t1 and t3
        self.assertEqual(stats["created_by_me"], 2)   # t1 and t2

    # 23. Missing JWT
    def test_23_missing_jwt(self):
        res = self.client.post("/api/tasks", json={"title": "Unauthorized"})
        self.assertEqual(res.status_code, 401)
        self.assertEqual(res.get_json()["error"]["code"], "UNAUTHORIZED")

    # 24. Expired JWT
    def test_24_expired_jwt(self):
        past_time = datetime.now(timezone.utc) - timedelta(days=2)
        expired_payload = {
            "sub": str(self.user_a.id),
            "email": self.user_a.email,
            "iat": past_time - timedelta(days=1),
            "exp": past_time,
        }
        expired_token = jwt.encode(
            expired_payload,
            self.app.config["JWT_SECRET_KEY"],
            algorithm="HS256",
        )
        res = self.client.get(
            "/api/tasks",
            headers={"Authorization": f"Bearer {expired_token}"},
        )
        self.assertEqual(res.status_code, 401)
        self.assertEqual(res.get_json()["error"]["code"], "TOKEN_EXPIRED")


if __name__ == "__main__":
    unittest.main()
