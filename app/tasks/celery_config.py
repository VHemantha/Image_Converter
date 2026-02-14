"""
Celery configuration for asynchronous task processing.
"""
import os
from kombu import Queue


class CeleryConfig:
    """Celery configuration settings."""

    # Broker settings
    broker_url = os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0')
    result_backend = os.getenv('CELERY_RESULT_BACKEND', 'redis://localhost:6379/1')

    # Serialization
    task_serializer = 'json'
    result_serializer = 'json'
    accept_content = ['json']
    timezone = 'UTC'
    enable_utc = True

    # Task execution
    task_track_started = True
    task_time_limit = 300  # 5 minutes max per task
    task_soft_time_limit = 270  # Soft limit at 4.5 minutes
    task_acks_late = True  # Acknowledge task after completion
    task_reject_on_worker_lost = True  # Requeue if worker dies
    worker_prefetch_multiplier = 1  # Process one task at a time
    worker_max_tasks_per_child = 1000  # Restart worker after 1000 tasks

    # Result backend settings
    result_expires = 3600  # Results expire after 1 hour
    result_persistent = True  # Persist results to backend

    # Connection settings
    broker_connection_retry_on_startup = True
    broker_connection_max_retries = 10

    # Task routes (optional - for prioritization)
    task_routes = {
        'app.tasks.conversion_tasks.convert_single_image': {'queue': 'conversions'},
        'app.tasks.conversion_tasks.convert_batch_images': {'queue': 'conversions'},
        'app.tasks.cleanup_tasks.*': {'queue': 'cleanup'},
    }

    # Default queue
    task_default_queue = 'conversions'
    task_queues = (
        Queue('conversions', routing_key='conversion.#'),
        Queue('cleanup', routing_key='cleanup.#'),
    )

    # Beat schedule for periodic tasks
    beat_schedule = {
        'cleanup-old-files-every-15-minutes': {
            'task': 'app.tasks.cleanup_tasks.cleanup_old_files',
            'schedule': 900.0,  # 15 minutes in seconds
        },
    }


# Export config
celery_config = CeleryConfig()
