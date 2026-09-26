"""
Template Rendering Test Suite
Verifies that Jinja email templates load and render cleanly under all scenarios
including full data, missing optional fields, and all priority branches.
"""

import unittest
from flask import render_template
from app import create_app


class TestEmailTemplates(unittest.TestCase):
    def setUp(self):
        """Create application in testing mode."""
        self.app = create_app("testing")
        self.app_context = self.app.app_context()
        self.app_context.push()

    def tearDown(self):
        """Pop application context."""
        self.app_context.pop()

    def test_task_assigned_template_full_data(self):
        """Render task_assigned.html with all fields populated."""
        rendered = render_template(
            "emails/task_assigned.html",
            recipient_name="Bob Assignee",
            creator_name="Alice Author",
            task_title="Implement Comprehensive Error Resolution Audit",
            task_description="Perform deep inspection of templates, routes, and configs.",
            task_priority="HIGH",
            task_status="IN_PROGRESS",
            due_date="October 15, 2026",
            task_url="http://localhost:3000/dashboard/tasks",
        )

        self.assertIsInstance(rendered, str)
        self.assertGreater(len(rendered), 100)
        self.assertIn("Bob Assignee", rendered)
        self.assertIn("Alice Author", rendered)
        self.assertIn("Implement Comprehensive Error Resolution Audit", rendered)
        self.assertIn("Perform deep inspection of templates", rendered)
        self.assertIn("HIGH", rendered)
        self.assertIn("October 15, 2026", rendered)
        self.assertIn("http://localhost:3000/dashboard/tasks", rendered)
        self.assertIn("View Task in Dashboard", rendered)

    def test_task_assigned_template_missing_optional_fields(self):
        """Render task_assigned.html with optional fields (description, due_date, url) omitted."""
        rendered = render_template(
            "emails/task_assigned.html",
            recipient_name="Charlie Worker",
            creator_name="Alice Author",
            task_title="Quick Hotfix Task",
            task_description=None,
            task_priority="MEDIUM",
            task_status="TODO",
            due_date=None,
            task_url=None,
        )

        self.assertIsInstance(rendered, str)
        self.assertIn("Charlie Worker", rendered)
        self.assertIn("Quick Hotfix Task", rendered)
        self.assertIn("MEDIUM", rendered)
        self.assertIn("TODO", rendered)
        # Verify optional sections are omitted cleanly without Jinja errors
        self.assertNotIn("Due Date:", rendered)
        self.assertNotIn("View Task in Dashboard", rendered)

    def test_task_assigned_priority_color_branches(self):
        """Test every priority branch to verify conditional rendering and color coding."""
        color_map = {
            "URGENT": "#ef4444",
            "HIGH": "#f97316",
            "MEDIUM": "#eab308",
            "LOW": "#10b981",
            "UNKNOWN": "#10b981",
        }
        for priority, expected_color in color_map.items():
            rendered = render_template(
                "emails/task_assigned.html",
                recipient_name="Test User",
                creator_name="Author User",
                task_title="Priority Test",
                task_priority=priority,
                task_status="TODO",
            )
            self.assertIn(priority, rendered)
            self.assertIn("Priority:", rendered)
            self.assertIn(expected_color, rendered)

    def test_task_completed_template_full_data(self):
        """Render task_completed.html with all fields populated."""
        rendered = render_template(
            "emails/task_completed.html",
            recipient_name="Alice Author",
            actor_name="Bob Assignee",
            creator_name="Alice Author",
            task_title="Finish Database Migrations",
            task_description="Create initial schema with uuid and triggers.",
            completed_at="September 24, 2026 at 22:30 UTC",
            task_url="http://localhost:3000/dashboard/tasks",
        )

        self.assertIsInstance(rendered, str)
        self.assertGreater(len(rendered), 100)
        self.assertIn("Alice Author", rendered)
        self.assertIn("Bob Assignee", rendered)
        self.assertIn("Finish Database Migrations", rendered)
        self.assertIn("September 24, 2026 at 22:30 UTC", rendered)
        self.assertIn("http://localhost:3000/dashboard/tasks", rendered)
        self.assertIn("DONE", rendered)

    def test_task_completed_template_missing_optional_fields(self):
        """Render task_completed.html with optional description and url omitted."""
        rendered = render_template(
            "emails/task_completed.html",
            recipient_name="Alice Author",
            actor_name="Alice Author",
            creator_name="Alice Author",
            task_title="Self-Completed Task",
            task_description=None,
            completed_at="Just now",
            task_url=None,
        )

        self.assertIsInstance(rendered, str)
        self.assertIn("Self-Completed Task", rendered)
        self.assertIn("Just now", rendered)
        self.assertNotIn("View Task Details", rendered)


if __name__ == "__main__":
    unittest.main()
