"""
Email Notification Service
Handles asynchronous dispatch of HTML emails via Gmail SMTP with TLS.
Ensures database operations are never aborted if email sending fails.
"""

import smtplib
import threading
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Dict, Any, Optional
from flask import current_app, render_template

logger = logging.getLogger(__name__)


class EmailService:
    """Service for sending application emails in background threads."""

    @staticmethod
    def _send_smtp_email_sync(
        app_obj,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: Optional[str] = None,
    ) -> bool:
        """
        Synchronous SMTP worker invoked inside a background thread.
        Never exposes passwords in logs or bubbles exceptions up.
        """
        with app_obj.app_context():
            config = app_obj.config
            mail_server = config.get("MAIL_SERVER", "smtp.gmail.com")
            mail_port = int(config.get("MAIL_PORT", 587))
            mail_use_tls = config.get("MAIL_USE_TLS", True)
            mail_user = config.get("MAIL_USERNAME") or config.get("GMAIL_USER")
            mail_pass = config.get("MAIL_PASSWORD") or config.get("GMAIL_APP_PASSWORD")
            sender_name = config.get("MAIL_DEFAULT_SENDER", "Hairdrama Tech Tasks")

            # If SMTP credentials are not configured, log and gracefully exit
            if not mail_user or not mail_pass:
                logger.info(
                    f"Email notification to {to_email} skipped: MAIL_USERNAME or MAIL_PASSWORD not configured."
                )
                return False

            try:
                msg = MIMEMultipart("alternative")
                msg["Subject"] = subject
                msg["From"] = f"{sender_name} <{mail_user}>"
                msg["To"] = to_email

                # Attach plain text fallback
                if text_content:
                    msg.attach(MIMEText(text_content, "plain"))
                else:
                    msg.attach(MIMEText("Please view this email in an HTML-compatible client.", "plain"))

                # Attach HTML payload
                msg.attach(MIMEText(html_content, "html"))

                # Connect via SMTP with TLS
                server = smtplib.SMTP(mail_server, mail_port, timeout=15)
                if mail_use_tls:
                    server.starttls()
                server.login(mail_user, mail_pass)
                server.send_message(msg)
                server.quit()

                logger.info(f"Successfully sent notification email to {to_email} [Subject: '{subject}']")
                return True

            except smtplib.SMTPAuthenticationError:
                logger.error("Gmail SMTP authentication failed. Please check your Gmail App Password.")
                return False
            except smtplib.SMTPException as e:
                logger.error(f"Gmail SMTP error sending email to {to_email}: {type(e).__name__}")
                return False
            except Exception as e:
                logger.error(f"Unexpected error sending email to {to_email}: {type(e).__name__}")
                return False

    @staticmethod
    def _dispatch_async(to_email: str, subject: str, html_content: str, text_content: Optional[str] = None) -> None:
        """Launches a daemon background thread to perform SMTP delivery without blocking the API."""
        try:
            app_obj = current_app._get_current_object()
            thread = threading.Thread(
                target=EmailService._send_smtp_email_sync,
                args=(app_obj, to_email, subject, html_content, text_content),
                daemon=True,
            )
            thread.start()
        except Exception as e:
            logger.error(f"Failed to spawn background email thread: {e}")

    @classmethod
    def send_task_assigned_email(cls, task, assignee, creator) -> None:
        """
        Sends an assignment notification email to the assigned user.
        Non-blocking: runs in background thread.
        """
        if not assignee or not assignee.email:
            return

        try:
            frontend_url = current_app.config.get("FRONTEND_URL", "http://localhost:3000")
            task_url = f"{frontend_url}/dashboard/tasks"

            due_date_str = task.due_date.strftime("%B %d, %Y") if task.due_date else None

            html_body = render_template(
                "emails/task_assigned.html",
                recipient_name=assignee.name,
                creator_name=creator.name if creator else "A team member",
                task_title=task.title,
                task_description=task.description,
                task_priority=task.priority,
                task_status=task.status,
                due_date=due_date_str,
                task_url=task_url,
            )

            subject = f"You have been assigned a new task: {task.title}"
            plain_text = (
                f"Hello {assignee.name},\n\n"
                f"{creator.name if creator else 'A team member'} has assigned you a new task: '{task.title}'.\n"
                f"Priority: {task.priority}\n"
                f"Status: {task.status}\n\n"
                f"View your task at: {task_url}\n"
            )

            cls._dispatch_async(
                to_email=assignee.email,
                subject=subject,
                html_content=html_body,
                text_content=plain_text,
            )
        except Exception as e:
            logger.error(f"Error preparing task assignment email: {e}")

    @classmethod
    def send_task_completed_email(cls, task, recipient, actor) -> None:
        """
        Sends a completion notification email to the relevant user (author or assignee).
        Non-blocking: runs in background thread.
        """
        if not recipient or not recipient.email:
            return

        try:
            frontend_url = current_app.config.get("FRONTEND_URL", "http://localhost:3000")
            task_url = f"{frontend_url}/dashboard/tasks"

            completed_at_str = (
                task.completed_at.strftime("%B %d, %Y at %H:%M UTC")
                if task.completed_at
                else "Just now"
            )

            creator_name = task.creator.name if task.creator else "Original Author"

            html_body = render_template(
                "emails/task_completed.html",
                recipient_name=recipient.name,
                actor_name=actor.name if actor else "A team member",
                creator_name=creator_name,
                task_title=task.title,
                task_description=task.description,
                completed_at=completed_at_str,
                task_url=task_url,
            )

            subject = f"Task completed: {task.title}"
            plain_text = (
                f"Hello {recipient.name},\n\n"
                f"The task '{task.title}' has been marked as COMPLETED by {actor.name if actor else 'a team member'}.\n"
                f"Completed at: {completed_at_str}\n\n"
                f"View task details at: {task_url}\n"
            )

            cls._dispatch_async(
                to_email=recipient.email,
                subject=subject,
                html_content=html_body,
                text_content=plain_text,
            )
        except Exception as e:
            logger.error(f"Error preparing task completion email: {e}")

    @classmethod
    def send_test_email(cls, user) -> bool:
        """
        Sends a test verification email to the authenticated user.
        Returns True if successfully queued (runs async in background thread).
        """
        if not user or not user.email:
            return False

        try:
            frontend_url = current_app.config.get("FRONTEND_URL", "http://localhost:3000")

            html_body = render_template(
                "emails/test_notification.html",
                recipient_name=user.name,
                recipient_email=user.email,
                frontend_url=frontend_url,
            )

            subject = "✅ Hairdrama Tech — Email Notifications Working!"
            plain_text = (
                f"Hello {user.name},\n\n"
                f"This is a test notification from the Hairdrama Tech Task Management Application.\n"
                f"If you received this email, your Gmail SMTP integration is configured correctly!\n\n"
                f"— Hairdrama Tech\n"
            )

            cls._dispatch_async(
                to_email=user.email,
                subject=subject,
                html_content=html_body,
                text_content=plain_text,
            )
            return True
        except Exception as e:
            logger.error(f"Error preparing test email: {e}")
            return False

    @classmethod
    def send_task_status_update_email(cls, task, recipient, actor, old_status, new_status) -> None:
        """
        Sends a notification when a task's status changes (e.g., TODO → IN_PROGRESS).
        Non-blocking: runs in background thread.
        """
        if not recipient or not recipient.email:
            return

        # Don't send for COMPLETED transitions (handled by send_task_completed_email)
        if new_status == "COMPLETED":
            return

        try:
            frontend_url = current_app.config.get("FRONTEND_URL", "http://localhost:3000")
            task_url = f"{frontend_url}/dashboard/tasks"

            html_body = render_template(
                "emails/task_status_update.html",
                recipient_name=recipient.name,
                actor_name=actor.name if actor else "A team member",
                task_title=task.title,
                task_description=task.description,
                old_status=old_status,
                new_status=new_status,
                task_priority=task.priority,
                task_url=task_url,
            )

            subject = f"Task status updated: {task.title} ({old_status} → {new_status})"
            plain_text = (
                f"Hello {recipient.name},\n\n"
                f"{actor.name if actor else 'A team member'} updated the status of '{task.title}'.\n"
                f"Status changed: {old_status} → {new_status}\n\n"
                f"View task at: {task_url}\n"
            )

            cls._dispatch_async(
                to_email=recipient.email,
                subject=subject,
                html_content=html_body,
                text_content=plain_text,
            )
        except Exception as e:
            logger.error(f"Error preparing task status update email: {e}")

    @classmethod
    def send_due_date_reminder_email(cls, task, recipient) -> None:
        """
        Sends a due-date reminder for tasks approaching their deadline.
        Non-blocking: runs in background thread.
        """
        if not recipient or not recipient.email:
            return

        try:
            frontend_url = current_app.config.get("FRONTEND_URL", "http://localhost:3000")
            task_url = f"{frontend_url}/dashboard/tasks"
            due_date_str = task.due_date.strftime("%B %d, %Y") if task.due_date else "Not set"

            html_body = render_template(
                "emails/due_date_reminder.html",
                recipient_name=recipient.name,
                task_title=task.title,
                task_description=task.description,
                task_priority=task.priority,
                due_date=due_date_str,
                task_url=task_url,
            )

            subject = f"⏰ Reminder: '{task.title}' is due soon ({due_date_str})"
            plain_text = (
                f"Hello {recipient.name},\n\n"
                f"Reminder: Your task '{task.title}' is due on {due_date_str}.\n"
                f"Priority: {task.priority}\n\n"
                f"View task at: {task_url}\n"
            )

            cls._dispatch_async(
                to_email=recipient.email,
                subject=subject,
                html_content=html_body,
                text_content=plain_text,
            )
        except Exception as e:
            logger.error(f"Error preparing due date reminder email: {e}")

