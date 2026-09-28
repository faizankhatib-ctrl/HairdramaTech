"""
Application Configuration
Loads environment variables and defines configuration classes for different environments.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Locate and load the .env file from backend/ or the project root
basedir = Path(__file__).resolve().parent.parent
dotenv_path = basedir / ".env"
root_dotenv_path = basedir.parent / ".env"

if dotenv_path.exists():
    load_dotenv(dotenv_path)
elif root_dotenv_path.exists():
    load_dotenv(root_dotenv_path)
else:
    load_dotenv()  # Fallback to standard search


class Config:
    """Base configuration class with common defaults."""

    # Security
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-insecure-secret-key-replace-in-production")
    
    # Supabase PostgreSQL Database URI
    # Note: Handles legacy 'postgres://' URLs by replacing with 'postgresql://' for SQLAlchemy compatibility
    # Explicitly uses 'postgresql+psycopg2://' driver to avoid newer SQLAlchemy versions
    # defaulting to psycopg (v3) which may not be installed.
    raw_db_url = os.environ.get("DATABASE_URL", "")
    if raw_db_url.startswith("postgres://"):
        raw_db_url = raw_db_url.replace("postgres://", "postgresql+psycopg2://", 1)
    elif raw_db_url.startswith("postgresql://"):
        raw_db_url = raw_db_url.replace("postgresql://", "postgresql+psycopg2://", 1)
    
    # If no DATABASE_URL is configured yet in local environment, default to local SQLite for immediate safety
    instance_dir = basedir / "instance"
    instance_dir.mkdir(parents=True, exist_ok=True)
    SQLALCHEMY_DATABASE_URI = raw_db_url or f"sqlite:///{instance_dir / 'dev.db'}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Connection pooling options:
    # pool_pre_ping verifies connections are alive before using them (vital for Supabase idle connection drops)
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
        "pool_recycle": 300,
    }

    # JWT Authentication
    JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", SECRET_KEY)
    JWT_EXPIRATION_DAYS = int(os.environ.get("JWT_EXPIRATION_DAYS", 7))

    # Google OAuth 2.0 Credentials
    GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID", "")
    GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET", "")

    # Gmail SMTP Email Notification Configuration
    MAIL_SERVER = os.environ.get("MAIL_SERVER", "smtp.gmail.com")
    MAIL_PORT = int(os.environ.get("MAIL_PORT", 587))
    MAIL_USE_TLS = os.environ.get("MAIL_USE_TLS", "true").lower() in ("true", "1", "yes")
    MAIL_USERNAME = os.environ.get("MAIL_USERNAME") or os.environ.get("GMAIL_USER", "")
    MAIL_PASSWORD = os.environ.get("MAIL_PASSWORD") or os.environ.get("GMAIL_APP_PASSWORD", "")
    MAIL_DEFAULT_SENDER = os.environ.get("MAIL_DEFAULT_SENDER") or os.environ.get("MAIL_FROM_NAME", "Hairdrama Tech Tasks")

    # Frontend CORS
    FRONTEND_URL = os.environ.get("FRONTEND_URL", "http://localhost:3000")

    # JSON response formatting
    JSON_SORT_KEYS = False

    @staticmethod
    def init_app(app):
        """Hook for environment-specific initializations."""
        pass


class DevelopmentConfig(Config):
    """Development environment specific configuration."""
    DEBUG = True
    FLASK_ENV = "development"


class ProductionConfig(Config):
    """Production environment configuration with strict checks."""
    DEBUG = False
    FLASK_ENV = "production"

    @classmethod
    def init_app(cls, app):
        Config.init_app(app)
        # In production, ensure a real database URL is supplied
        if not os.environ.get("DATABASE_URL"):
            raise ValueError("DATABASE_URL environment variable must be set in production mode.")


class TestingConfig(Config):
    """Testing environment configuration."""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"


# Configuration dictionary for environment selection
config_by_name = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "testing": TestingConfig,
    "default": DevelopmentConfig,
}
