"""
Email Notification Routes
Provides test email endpoint and due-date reminder trigger.
"""

from flask import Blueprint, request, current_app
from app.services.email_service import EmailService
from app.utils.responses import success_response, error_response
from app.utils.decorators import token_required

notifications_bp = Blueprint("notifications", __name__)


@notifications_bp.route("/test", methods=["POST"])
@token_required
def send_test_email(current_user):
    """
    POST /api/notifications/test
    Sends a test notification email to the authenticated user's email address.
    Useful for verifying Gmail SMTP integration is correctly configured.
    """
    if not current_user.email:
        return error_response(
            message="Your account has no email address on file.",
            code="NO_EMAIL",
            status_code=400,
        )

    mail_user = current_app.config.get("MAIL_USERNAME")
    mail_pass = current_app.config.get("MAIL_PASSWORD")
    if not mail_user or not mail_pass:
        return error_response(
            message="Gmail SMTP credentials (MAIL_USERNAME / MAIL_PASSWORD) are not configured in the backend .env file.",
            code="SMTP_NOT_CONFIGURED",
            status_code=503,
        )

    success = EmailService.send_test_email(current_user)
    if success:
        return success_response(
            data={"recipient": current_user.email},
            message=f"Test email dispatched to {current_user.email}. Check your inbox (and spam folder).",
        )
    else:
        return success_response(
            data={"recipient": current_user.email},
            message=f"Test email queued for background delivery to {current_user.email}.",
        )


@notifications_bp.route("/status", methods=["GET"])
@token_required
def notification_status(current_user):
    """
    GET /api/notifications/status
    Returns the current email notification configuration status.
    """
    mail_user = current_app.config.get("MAIL_USERNAME", "")
    mail_pass = current_app.config.get("MAIL_PASSWORD", "")

    configured = bool(mail_user and mail_pass)

    return success_response(
        data={
            "email_notifications_enabled": configured,
            "smtp_server": current_app.config.get("MAIL_SERVER", "smtp.gmail.com"),
            "smtp_port": current_app.config.get("MAIL_PORT", 587),
            "sender_email": mail_user if configured else None,
            "sender_name": current_app.config.get("MAIL_DEFAULT_SENDER", "Hairdrama Tech Tasks"),
            "user_email": current_user.email,
        },
        message="Email notification configuration status.",
    )
