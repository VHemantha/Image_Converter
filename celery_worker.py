"""
Celery worker entry point.
Ensures proper Flask app context for Celery tasks.
"""
import os
import sys

# Add project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Import Flask app to initialize context
from app import create_app

# Create Flask app instance
flask_app = create_app()

# Import Celery app (this will have Flask context available)
from app.tasks.celery_app import celery_app

# Push Flask app context for Celery tasks
flask_app.app_context().push()

# Export celery_app for the worker
__all__ = ['celery_app']
