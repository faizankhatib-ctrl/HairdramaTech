"""
Quick test script to verify Gmail SMTP email delivery.
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

backend_dir = Path(__file__).resolve().parent
load_dotenv(backend_dir / ".env")
sys.path.insert(0, str(backend_dir))

from app import create_app

app = create_app("development")

with app.app_context():
    from app.services.email_service import EmailService
    from flask import render_template

    recipient = os.environ.get("MAIL_USERNAME", "test@example.com")
    recipient_name = recipient.split("@")[0].capitalize()

    # Render the test notification template
    html_body = render_template(
        "emails/test_notification.html",
        recipient_name=recipient_name,
        recipient_email=recipient,
        frontend_url="http://localhost:3000",
    )

    result = EmailService._send_smtp_email_sync(
        app,
        recipient,
        "Hairdrama Tech — Email Notifications Working!",
        html_body,
        f"Hello {recipient_name}, Gmail SMTP integration is working correctly for Hairdrama Tech!",
    )

    if result:
        print(f"\n[SUCCESS] Test email sent to {recipient}")
        print("Check your Gmail inbox (and spam folder).")
    else:
        print("\n[FAILED] Could not send email. Check SMTP credentials in .env")
