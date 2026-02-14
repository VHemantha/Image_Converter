"""
Celery tasks for image conversion.
Handles asynchronous image processing with progress tracking.
"""
import os
import logging
from celery import Task
from .celery_app import celery_app
from app.utils.image_converter import convert_image, ImageConversionError, calculate_file_sizes
from app.utils.file_validator import sanitize_filename

logger = logging.getLogger(__name__)


class ConversionTask(Task):
    """Base task with cleanup on failure."""

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """Clean up files on task failure."""
        logger.error(f"Task {task_id} failed: {exc}")
        # Cleanup will be handled by periodic cleanup task

    def on_success(self, retval, task_id, args, kwargs):
        """Log success."""
        logger.info(f"Task {task_id} completed successfully")


@celery_app.task(base=ConversionTask, bind=True, name='app.tasks.conversion_tasks.convert_single_image')
def convert_single_image(self, input_path, output_path, target_format, original_filename):
    """
    Convert a single image asynchronously.

    Args:
        self: Celery task instance
        input_path: Path to input image
        output_path: Path to save converted image
        target_format: Target image format
        original_filename: Original filename for reporting

    Returns:
        dict: Conversion result with metadata
    """
    try:
        # Update progress: Starting
        self.update_state(
            state='PROGRESS',
            meta={
                'current': 0,
                'total': 100,
                'progress': 0,
                'status': f'Starting conversion of {original_filename}...'
            }
        )

        # Update progress: Converting
        self.update_state(
            state='PROGRESS',
            meta={
                'current': 50,
                'total': 100,
                'progress': 50,
                'status': f'Converting {original_filename} to {target_format}...'
            }
        )

        # Perform conversion
        conversion_result = convert_image(input_path, output_path, target_format)

        # Calculate file sizes
        size_info = calculate_file_sizes(input_path, output_path)

        # Update progress: Cleaning up
        self.update_state(
            state='PROGRESS',
            meta={
                'current': 90,
                'total': 100,
                'progress': 90,
                'status': 'Finalizing...'
            }
        )

        # Cleanup input file
        if os.path.exists(input_path):
            os.remove(input_path)

        # Return result
        return {
            'success': True,
            'original_filename': original_filename,
            'converted_filename': os.path.basename(output_path),
            'source_format': conversion_result['source_format'],
            'target_format': conversion_result['target_format'],
            'input_size': size_info['input_size_mb'],
            'output_size': size_info['output_size_mb'],
            'compression_ratio': size_info['compression_ratio'],
            'output_path': output_path,
        }

    except (ImageConversionError, Exception) as e:
        logger.error(f"Error converting {original_filename}: {str(e)}")

        # Cleanup input file on error
        if os.path.exists(input_path):
            os.remove(input_path)

        return {
            'success': False,
            'original_filename': original_filename,
            'error': str(e),
        }


@celery_app.task(base=ConversionTask, bind=True, name='app.tasks.conversion_tasks.convert_batch_images')
def convert_batch_images(self, file_list, target_format, task_id):
    """
    Convert multiple images asynchronously.

    Args:
        self: Celery task instance
        file_list: List of dicts with input_path, output_path, original_filename
        target_format: Target image format
        task_id: Task identifier for organizing files

    Returns:
        dict: Batch conversion results
    """
    total = len(file_list)
    results = []

    for idx, file_info in enumerate(file_list):
        try:
            # Update overall progress
            progress = int((idx / total) * 100)
            self.update_state(
                state='PROGRESS',
                meta={
                    'current': idx,
                    'total': total,
                    'progress': progress,
                    'status': f'Converting file {idx + 1} of {total}: {file_info["original_filename"]}'
                }
            )

            # Convert single image
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
            logger.error(f"Error in batch conversion for {file_info.get('original_filename', 'unknown')}: {str(e)}")

            # Cleanup input file on error
            if os.path.exists(file_info['input_path']):
                os.remove(file_info['input_path'])

            results.append({
                'success': False,
                'original_filename': file_info.get('original_filename', 'unknown'),
                'error': str(e),
            })

    # Final progress update
    self.update_state(
        state='PROGRESS',
        meta={
            'current': total,
            'total': total,
            'progress': 100,
            'status': 'Batch conversion complete!'
        }
    )

    successful_count = sum(1 for r in results if r['success'])

    return {
        'success': True,
        'task_id': task_id,
        'total_files': total,
        'successful': successful_count,
        'failed': total - successful_count,
        'results': results,
    }


@celery_app.task(name='app.tasks.conversion_tasks.create_zip_archive')
def create_zip_archive(file_paths, output_zip_path):
    """
    Create a ZIP archive of converted files.

    Args:
        file_paths: List of file paths to include in ZIP
        output_zip_path: Path for output ZIP file

    Returns:
        dict: ZIP creation result
    """
    import zipfile

    try:
        with zipfile.ZipFile(output_zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for file_path in file_paths:
                if os.path.exists(file_path):
                    arcname = os.path.basename(file_path)
                    zipf.write(file_path, arcname=arcname)

        return {
            'success': True,
            'zip_path': output_zip_path,
            'file_count': len(file_paths),
            'zip_size': os.path.getsize(output_zip_path),
        }

    except Exception as e:
        logger.error(f"Error creating ZIP archive: {str(e)}")
        return {
            'success': False,
            'error': str(e),
        }
