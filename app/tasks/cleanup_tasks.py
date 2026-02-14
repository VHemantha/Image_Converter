"""
Periodic cleanup tasks for maintaining file system hygiene.
Automatically removes old uploaded and converted files.
"""
import os
import logging
from datetime import datetime, timedelta
from .celery_app import celery_app

logger = logging.getLogger(__name__)


def get_file_age_minutes(file_path):
    """
    Get the age of a file in minutes.

    Args:
        file_path: Path to file

    Returns:
        float: Age in minutes
    """
    try:
        file_mtime = os.path.getmtime(file_path)
        file_time = datetime.fromtimestamp(file_mtime)
        age = datetime.now() - file_time
        return age.total_seconds() / 60
    except Exception:
        return 0


def cleanup_directory(directory, max_age_minutes):
    """
    Clean up old files in a directory.

    Args:
        directory: Directory to clean
        max_age_minutes: Maximum file age in minutes

    Returns:
        dict: Cleanup results
    """
    if not os.path.exists(directory):
        return {'files_removed': 0, 'errors': 0}

    files_removed = 0
    errors = 0

    try:
        for filename in os.listdir(directory):
            file_path = os.path.join(directory, filename)

            if not os.path.isfile(file_path):
                continue

            try:
                file_age = get_file_age_minutes(file_path)

                if file_age > max_age_minutes:
                    os.remove(file_path)
                    files_removed += 1
                    logger.info(f"Removed old file: {filename} (age: {file_age:.1f} minutes)")

            except Exception as e:
                errors += 1
                logger.error(f"Error removing file {filename}: {str(e)}")

    except Exception as e:
        logger.error(f"Error accessing directory {directory}: {str(e)}")
        errors += 1

    return {
        'files_removed': files_removed,
        'errors': errors,
    }


@celery_app.task(name='app.tasks.cleanup_tasks.cleanup_old_files')
def cleanup_old_files():
    """
    Periodic task to cleanup old uploaded and converted files.
    Runs every 15 minutes via Celery Beat.

    Returns:
        dict: Cleanup summary
    """
    from app.config import BaseConfig

    # Get configuration
    upload_folder = BaseConfig.UPLOAD_FOLDER
    converted_folder = BaseConfig.CONVERTED_FOLDER
    max_age = BaseConfig.FILE_RETENTION_MINUTES

    logger.info(f"Starting cleanup task (max age: {max_age} minutes)")

    # Cleanup uploads
    uploads_result = cleanup_directory(upload_folder, max_age)

    # Cleanup converted files
    converted_result = cleanup_directory(converted_folder, max_age)

    # Summary
    total_removed = uploads_result['files_removed'] + converted_result['files_removed']
    total_errors = uploads_result['errors'] + converted_result['errors']

    logger.info(
        f"Cleanup complete: {total_removed} files removed, "
        f"{total_errors} errors"
    )

    return {
        'success': True,
        'uploads_removed': uploads_result['files_removed'],
        'converted_removed': converted_result['files_removed'],
        'total_removed': total_removed,
        'errors': total_errors,
        'timestamp': datetime.utcnow().isoformat(),
    }


@celery_app.task(name='app.tasks.cleanup_tasks.cleanup_task_files')
def cleanup_task_files(task_id, converted_folder=None):
    """
    Clean up files associated with a specific task.
    Called after successful download or on task timeout.

    Args:
        task_id: Task identifier
        converted_folder: Path to converted files folder

    Returns:
        dict: Cleanup result
    """
    if converted_folder is None:
        from app.config import BaseConfig
        converted_folder = BaseConfig.CONVERTED_FOLDER

    files_removed = 0
    errors = 0

    try:
        if not os.path.exists(converted_folder):
            return {'files_removed': 0, 'errors': 0}

        # Find and remove files starting with task_id
        for filename in os.listdir(converted_folder):
            if filename.startswith(task_id):
                file_path = os.path.join(converted_folder, filename)

                try:
                    if os.path.isfile(file_path):
                        os.remove(file_path)
                        files_removed += 1
                        logger.info(f"Cleaned up task file: {filename}")
                except Exception as e:
                    errors += 1
                    logger.error(f"Error removing task file {filename}: {str(e)}")

    except Exception as e:
        logger.error(f"Error in cleanup_task_files for {task_id}: {str(e)}")
        errors += 1

    return {
        'success': True,
        'task_id': task_id,
        'files_removed': files_removed,
        'errors': errors,
    }


@celery_app.task(name='app.tasks.cleanup_tasks.cleanup_failed_uploads')
def cleanup_failed_uploads():
    """
    Clean up orphaned upload files that were never processed.
    These are files older than 30 minutes in the upload folder.

    Returns:
        dict: Cleanup result
    """
    from app.config import BaseConfig

    upload_folder = BaseConfig.UPLOAD_FOLDER
    max_age = 30  # 30 minutes for failed/orphaned uploads

    result = cleanup_directory(upload_folder, max_age)

    logger.info(f"Cleaned up {result['files_removed']} orphaned upload files")

    return {
        'success': True,
        'files_removed': result['files_removed'],
        'errors': result['errors'],
        'timestamp': datetime.utcnow().isoformat(),
    }
