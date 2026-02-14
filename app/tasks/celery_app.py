"""
Celery application instance with Flask integration.
"""
import os
import sys
from celery import Celery

# Add project root to path for imports
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from .celery_config import celery_config

# Create Celery instance
celery_app = Celery('image_converter')

# Load configuration
celery_app.config_from_object(celery_config)

# Auto-discover tasks
celery_app.autodiscover_tasks(['app.tasks'])


def init_celery(app=None):
    """
    Initialize Celery with Flask app context.
    Call this from Flask app factory if needed.
    """
    if app:
        celery_app.conf.update(app.config)

        class ContextTask(celery_app.Task):
            def __call__(self, *args, **kwargs):
                with app.app_context():
                    return self.run(*args, **kwargs)

        celery_app.Task = ContextTask

    return celery_app
