"""
Celery worker entry point.
Initializes Flask app context for Celery tasks.
Works with both local development and Docker deployment.
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

# Import Flask app and Celery app
from app import create_app
from app.tasks.celery_app import celery_app, init_celery

# Create Flask app instance
flask_app = create_app(config_name=os.getenv('FLASK_ENV', 'development'))

# Initialize Celery with Flask context
init_celery(flask_app)

# Export celery_app for the worker
# Start with: celery -A celery_worker.celery_app worker --loglevel=info
__all__ = ['celery_app']

if __name__ == '__main__':
    celery_app.start()
