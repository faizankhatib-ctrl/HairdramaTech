"""
Flask Extensions Initialization
Centralized initialization to avoid circular imports across modules.
"""

from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS

db = SQLAlchemy()
cors = CORS()
