"""
Backend Application Entry Point
Starts the Flask development server or provides the WSGI callable for production servers (gunicorn).
"""

import os
from app import create_app

app = create_app()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    debug = app.config.get("DEBUG", False)
    
    print(f"Starting Hairdrama Task Management API server...")
    print(f"Host: http://127.0.0.1:{port}")
    print(f"Health check: http://127.0.0.1:{port}/api/health")
    print(f"Debug mode: {'Enabled' if debug else 'Disabled'}")
    
    app.run(host="0.0.0.0", port=port, debug=debug)
