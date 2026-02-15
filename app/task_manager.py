"""
In-memory task manager using Python threading.
Replaces Redis + Celery for zero-dependency async processing.
Provides progress tracking, SSE streaming support, and periodic cleanup.
"""
import os
import threading
import logging
import time
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger(__name__)

# Thread-safe task state store
_task_store = {}
_task_lock = threading.Lock()

# Thread pool for background work
_executor = ThreadPoolExecutor(max_workers=4)

# Cleanup scheduler
_cleanup_thread = None


def get_task(task_id):
    """Get task state by ID (thread-safe)."""
    with _task_lock:
        return _task_store.get(task_id, {}).copy()


def update_task(task_id, **kwargs):
    """Update task state (thread-safe)."""
    with _task_lock:
        if task_id not in _task_store:
            _task_store[task_id] = {}
        _task_store[task_id].update(kwargs)
        _task_store[task_id]['updated_at'] = datetime.utcnow().isoformat()


def delete_task(task_id):
    """Remove task from store (thread-safe)."""
    with _task_lock:
        _task_store.pop(task_id, None)


def submit_conversion(task_id, file_list, target_format, app_config):
    """
    Submit a batch conversion job to the thread pool.
    Returns immediately; work happens in background.
    """
    update_task(
        task_id,
        state='PENDING',
        progress=0,
        status='Queued for processing...',
        created_at=datetime.utcnow().isoformat(),
    )

    _executor.submit(_run_batch_conversion, task_id, file_list, target_format, app_config)


def _run_batch_conversion(task_id, file_list, target_format, app_config):
    """
    Execute batch image conversion in a background thread.
    Updates task state with progress as it runs.
    """
    from app.utils.image_converter import convert_image, ImageConversionError, calculate_file_sizes

    total = len(file_list)
    results = []

    try:
        for idx, file_info in enumerate(file_list):
            # Update progress
            progress = int((idx / total) * 100)
            update_task(
                task_id,
                state='PROGRESS',
                progress=progress,
                current=idx,
                total=total,
                status=f'Converting file {idx + 1} of {total}: {file_info["original_filename"]}',
            )

            try:
                input_path = file_info['input_path']
                output_path = file_info['output_path']
                original_filename = file_info['original_filename']

                conversion_result = convert_image(input_path, output_path, target_format)
                size_info = calculate_file_sizes(input_path, output_path)

                # Cleanup input file
                if os.path.exists(input_path):
                    os.remove(input_path)

                results.append({
                    'success': True,
                    'original_filename': original_filename,
                    'converted_filename': os.path.basename(output_path),
                    'source_format': conversion_result['source_format'],
                    'target_format': conversion_result['target_format'],
                    'input_size': size_info['input_size_mb'],
                    'output_size': size_info['output_size_mb'],
                    'compression_ratio': size_info['compression_ratio'],
                })

            except Exception as e:
                logger.error(f"Error converting {file_info.get('original_filename', 'unknown')}: {e}")
                if os.path.exists(file_info['input_path']):
                    os.remove(file_info['input_path'])
                results.append({
                    'success': False,
                    'original_filename': file_info.get('original_filename', 'unknown'),
                    'error': str(e),
                })

        successful_count = sum(1 for r in results if r['success'])

        # Mark task as complete
        update_task(
            task_id,
            state='SUCCESS',
            progress=100,
            status='Complete!',
            result={
                'success': True,
                'task_id': task_id,
                'total_files': total,
                'successful': successful_count,
                'failed': total - successful_count,
                'results': results,
            },
        )

        logger.info(f"Task {task_id} completed: {successful_count}/{total} successful")

    except Exception as e:
        logger.error(f"Task {task_id} failed: {e}")
        update_task(
            task_id,
            state='FAILURE',
            progress=0,
            status='Task failed',
            error=str(e),
        )


def cleanup_old_files(upload_folder, converted_folder, max_age_minutes=60):
    """Remove files older than max_age_minutes from temp directories."""
    removed = 0
    for folder in [upload_folder, converted_folder]:
        if not os.path.exists(folder):
            continue
        for filename in os.listdir(folder):
            if filename == '.gitkeep':
                continue
            file_path = os.path.join(folder, filename)
            if not os.path.isfile(file_path):
                continue
            try:
                age_min = (time.time() - os.path.getmtime(file_path)) / 60
                if age_min > max_age_minutes:
                    os.remove(file_path)
                    removed += 1
            except Exception:
                pass

    # Also prune old task entries from memory
    with _task_lock:
        cutoff = (datetime.utcnow() - timedelta(minutes=max_age_minutes)).isoformat()
        stale = [tid for tid, t in _task_store.items()
                 if t.get('created_at', '') < cutoff]
        for tid in stale:
            del _task_store[tid]

    if removed:
        logger.info(f"Cleanup: removed {removed} old files, pruned {len(stale) if 'stale' in dir() else 0} tasks")
    return removed


def start_cleanup_scheduler(app):
    """Start a background thread that runs cleanup every 15 minutes."""
    global _cleanup_thread

    if _cleanup_thread and _cleanup_thread.is_alive():
        return  # Already running

    def _cleanup_loop():
        while True:
            time.sleep(900)  # 15 minutes
            try:
                with app.app_context():
                    cleanup_old_files(
                        app.config['UPLOAD_FOLDER'],
                        app.config['CONVERTED_FOLDER'],
                        app.config.get('FILE_RETENTION_MINUTES', 60),
                    )
            except Exception as e:
                logger.error(f"Cleanup error: {e}")

    _cleanup_thread = threading.Thread(target=_cleanup_loop, daemon=True)
    _cleanup_thread.start()
    logger.info("Started background cleanup scheduler (every 15 minutes)")
