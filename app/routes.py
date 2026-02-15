"""
Routes for image conversion application.
Phase 1: Synchronous conversion
Phase 2: Celery async processing
Phase 3: Real-time SSE progress + ZIP downloads
"""
from flask import Blueprint, render_template, request, jsonify, send_file, session, current_app, Response
import os
import uuid
import logging
import json
from datetime import datetime

from app.forms import UploadForm
from app.utils.file_validator import (
    validate_file_comprehensive,
    FileValidationError,
    sanitize_filename,
    get_supported_formats,
    get_format_info
)
from app.utils.image_converter import (
    convert_image,
    ImageConversionError,
    calculate_file_sizes
)
# Import Celery tasks (Phase 2)
try:
    from app.tasks.conversion_tasks import convert_batch_images
    CELERY_AVAILABLE = True
except ImportError:
    CELERY_AVAILABLE = False

# Create blueprint
bp = Blueprint('main', __name__)

# Configure logging
logger = logging.getLogger(__name__)


@bp.route('/')
def index():
    """Home page with upload form."""
    form = UploadForm()
    supported_formats = get_supported_formats()
    format_info = get_format_info()

    return render_template(
        'index.html',
        form=form,
        supported_formats=supported_formats,
        format_info=format_info
    )


@bp.route('/upload', methods=['POST'])
# Rate limiting applied in __init__.py
def upload():
    """
    Handle file upload and conversion.
    Phase 2: Uses Celery for asynchronous processing if available.
    Falls back to synchronous processing if Celery/Redis not available.
    """
    form = UploadForm()

    if not form.validate_on_submit():
        return jsonify({
            'success': False,
            'error': 'Form validation failed',
            'errors': form.errors
        }), 400

    try:
        files = request.files.getlist('files')
        target_format = form.target_format.data

        if not files or len(files) == 0:
            return jsonify({
                'success': False,
                'error': 'No files uploaded'
            }), 400

        # Generate task ID
        task_id = str(uuid.uuid4())

        # Prepare file list for processing
        file_list = []

        for file in files:
            if not file or file.filename == '':
                continue

            try:
                # Validate file
                validation_result = validate_file_comprehensive(
                    file,
                    file.filename,
                    current_app.config['MAX_CONTENT_LENGTH'],
                    current_app.config['ALLOWED_EXTENSIONS']
                )

                # Generate unique filename
                sanitized_name = sanitize_filename(file.filename, task_id)
                input_path = os.path.join(current_app.config['UPLOAD_FOLDER'], sanitized_name)

                # Save uploaded file
                file.save(input_path)

                # Generate output filename
                name_without_ext = os.path.splitext(sanitized_name)[0]
                output_filename = f"{name_without_ext}.{target_format.lower()}"
                output_path = os.path.join(current_app.config['CONVERTED_FOLDER'], output_filename)

                # Add to processing list
                file_list.append({
                    'input_path': input_path,
                    'output_path': output_path,
                    'original_filename': file.filename,
                })

            except FileValidationError as e:
                logger.error(f"Validation error for {file.filename}: {str(e)}")
                return jsonify({
                    'success': False,
                    'error': f'Validation failed for {file.filename}: {str(e)}'
                }), 400

        if not file_list:
            return jsonify({
                'success': False,
                'error': 'No valid files to process'
            }), 400

        # Phase 2: Use Celery if available, otherwise fall back to synchronous
        if CELERY_AVAILABLE:
            # Asynchronous processing with Celery
            celery_task = convert_batch_images.delay(file_list, target_format, task_id)

            return jsonify({
                'success': True,
                'task_id': celery_task.id,
                'status': 'processing',
                'message': 'Conversion started. Use /status/<task_id> to check progress.',
                'total_files': len(file_list),
                'async': True,
            })
        else:
            # Fallback to synchronous processing (Phase 1 behavior)
            conversion_results = []
            converted_files = []

            for file_info in file_list:
                try:
                    conversion_result = convert_image(
                        file_info['input_path'],
                        file_info['output_path'],
                        target_format
                    )

                    size_info = calculate_file_sizes(file_info['input_path'], file_info['output_path'])

                    # Cleanup input file
                    if os.path.exists(file_info['input_path']):
                        os.remove(file_info['input_path'])

                    conversion_results.append({
                        'original_filename': file_info['original_filename'],
                        'converted_filename': os.path.basename(file_info['output_path']),
                        'source_format': conversion_result['source_format'],
                        'target_format': conversion_result['target_format'],
                        'input_size': size_info['input_size_mb'],
                        'output_size': size_info['output_size_mb'],
                        'compression_ratio': size_info['compression_ratio'],
                        'success': True
                    })

                    converted_files.append({
                        'filename': os.path.basename(file_info['output_path']),
                        'path': file_info['output_path']
                    })

                except (ImageConversionError, Exception) as e:
                    logger.error(f"Error converting {file_info['original_filename']}: {str(e)}")
                    if os.path.exists(file_info['input_path']):
                        os.remove(file_info['input_path'])

                    conversion_results.append({
                        'original_filename': file_info['original_filename'],
                        'success': False,
                        'error': str(e)
                    })

            # Store task information in session (for synchronous fallback)
            session[task_id] = {
                'task_id': task_id,
                'files': converted_files,
                'results': conversion_results,
                'created_at': datetime.utcnow().isoformat()
            }

            successful_count = sum(1 for r in conversion_results if r['success'])

            return jsonify({
                'success': True,
                'task_id': task_id,
                'total_files': len(conversion_results),
                'successful': successful_count,
                'failed': len(conversion_results) - successful_count,
                'results': conversion_results,
                'async': False,
            })

    except Exception as e:
        logger.error(f"Error in upload endpoint: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'An error occurred during upload'
        }), 500


@bp.route('/download/<task_id>/<filename>')
def download(task_id, filename):
    """
    Download converted file.

    Args:
        task_id: Task identifier
        filename: Filename to download

    Returns:
        File download response
    """
    try:
        # Sanitize filename to prevent path traversal
        safe_filename = os.path.basename(filename)

        # Verify filename starts with task_id for security
        if not safe_filename.startswith(task_id):
            return jsonify({
                'success': False,
                'error': 'Invalid file request'
            }), 403

        # Construct file path
        file_path = os.path.join(current_app.config['CONVERTED_FOLDER'], safe_filename)

        if not os.path.exists(file_path):
            return jsonify({
                'success': False,
                'error': 'File not found on server'
            }), 404

        # Send file with proper mimetype detection
        return send_file(
            file_path,
            as_attachment=True,
            download_name=safe_filename,
            mimetype='application/octet-stream'
        )

    except Exception as e:
        logger.error(f"Error downloading file: {str(e)}")
        logger.exception(e)  # Log full traceback
        return jsonify({
            'success': False,
            'error': f'Error downloading file: {str(e)}'
        }), 500


@bp.route('/download-all/<task_id>')
def download_all(task_id):
    """
    Download all converted files as ZIP archive.
    Phase 3: Implemented ZIP download functionality.
    """
    try:
        import zipfile
        from datetime import datetime
        import tempfile

        # Get list of files for this task
        converted_folder = current_app.config['CONVERTED_FOLDER']

        # Find all files matching the task_id
        task_files = []
        for filename in os.listdir(converted_folder):
            if filename.startswith(task_id):
                file_path = os.path.join(converted_folder, filename)
                if os.path.exists(file_path):
                    task_files.append((filename, file_path))

        if not task_files:
            return jsonify({
                'success': False,
                'error': 'No converted files found for this task'
            }), 404

        # Create temporary ZIP file
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        zip_filename = f'converted_images_{timestamp}.zip'
        zip_path = os.path.join(tempfile.gettempdir(), zip_filename)

        # Create ZIP archive
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for filename, file_path in task_files:
                # Add file to ZIP with original name (remove task_id prefix)
                archive_name = filename.replace(f'{task_id}_', '')
                zipf.write(file_path, archive_name)

        # Send ZIP file
        return send_file(
            zip_path,
            as_attachment=True,
            download_name=zip_filename,
            mimetype='application/zip'
        )

    except Exception as e:
        logger.error(f"Error creating ZIP archive: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Error creating ZIP: {str(e)}'
        }), 500


@bp.route('/health')
def health():
    """Health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat()
    })


@bp.route('/ready')
def ready():
    """Readiness probe (checks dependencies)."""
    try:
        # Check if upload and converted folders are writable
        upload_folder = current_app.config['UPLOAD_FOLDER']
        converted_folder = current_app.config['CONVERTED_FOLDER']

        if not os.path.exists(upload_folder) or not os.access(upload_folder, os.W_OK):
            return jsonify({
                'status': 'not ready',
                'error': 'Upload folder not accessible'
            }), 503

        if not os.path.exists(converted_folder) or not os.access(converted_folder, os.W_OK):
            return jsonify({
                'status': 'not ready',
                'error': 'Converted folder not accessible'
            }), 503

        return jsonify({
            'status': 'ready',
            'timestamp': datetime.utcnow().isoformat()
        })

    except Exception as e:
        return jsonify({
            'status': 'not ready',
            'error': str(e)
        }), 503


@bp.route('/formats')
def formats():
    """Get supported format information."""
    return jsonify({
        'formats': get_supported_formats(),
        'format_info': get_format_info()
    })


@bp.route('/stream/<task_id>')
def stream_progress(task_id):
    """
    Server-Sent Events (SSE) endpoint for real-time progress streaming.
    Phase 3: Live progress updates pushed to client.
    """
    def generate():
        """Generator function for SSE stream."""
        import time
        from flask import Response

        if not CELERY_AVAILABLE:
            # Fallback: Check session for synchronous tasks
            if task_id in session:
                task_data = session[task_id]
                yield f"data: {json.dumps({'state': 'SUCCESS', 'progress': 100, 'result': task_data.get('results', [])})}\n\n"
            else:
                yield f"data: {json.dumps({'state': 'NOT_FOUND', 'error': 'Task not found'})}\n\n"
            return

        try:
            from app.tasks.celery_app import celery_app

            # Poll task status and stream updates
            max_iterations = 120  # 2 minutes max
            iteration = 0

            while iteration < max_iterations:
                task = celery_app.AsyncResult(task_id)

                if task.state == 'PENDING':
                    data = {
                        'state': task.state,
                        'progress': 0,
                        'status': 'Task is waiting to start...'
                    }
                elif task.state == 'PROGRESS':
                    data = {
                        'state': task.state,
                        'progress': task.info.get('progress', 0),
                        'current': task.info.get('current', 0),
                        'total': task.info.get('total', 100),
                        'status': task.info.get('status', 'Processing...')
                    }
                elif task.state == 'SUCCESS':
                    data = {
                        'state': task.state,
                        'progress': 100,
                        'result': task.result,
                        'status': 'Complete!'
                    }
                    yield f"data: {json.dumps(data)}\n\n"
                    break
                elif task.state == 'FAILURE':
                    data = {
                        'state': task.state,
                        'progress': 0,
                        'error': str(task.info),
                        'status': 'Task failed'
                    }
                    yield f"data: {json.dumps(data)}\n\n"
                    break
                else:
                    data = {
                        'state': task.state,
                        'progress': 0,
                        'status': str(task.info)
                    }

                yield f"data: {json.dumps(data)}\n\n"

                # Stop streaming after success or failure
                if task.state in ['SUCCESS', 'FAILURE']:
                    break

                time.sleep(0.5)  # Poll every 500ms
                iteration += 1

            # Timeout message if max iterations reached
            if iteration >= max_iterations:
                yield f"data: {json.dumps({'state': 'TIMEOUT', 'error': 'Task timeout'})}\n\n"

        except Exception as e:
            logger.error(f"Error streaming progress: {str(e)}")
            yield f"data: {json.dumps({'state': 'ERROR', 'error': str(e)})}\n\n"

    return Response(generate(), mimetype='text/event-stream')


@bp.route('/status/<task_id>')
def task_status(task_id):
    """
    Check the status of a Celery task.
    Returns progress information for async conversions.
    Phase 2: Polling endpoint (kept for backwards compatibility)
    Phase 3: Use /stream/<task_id> for real-time updates
    """
    if not CELERY_AVAILABLE:
        # Fallback: Check session for synchronous tasks
        if task_id in session:
            task_data = session[task_id]
            return jsonify({
                'state': 'SUCCESS',
                'status': 'complete',
                'results': task_data.get('results', []),
                'async': False,
            })
        else:
            return jsonify({
                'state': 'PENDING',
                'status': 'Task not found',
            }), 404

    try:
        from app.tasks.celery_app import celery_app

        # Get task result
        task = celery_app.AsyncResult(task_id)

        if task.state == 'PENDING':
            response = {
                'state': task.state,
                'status': 'Task is waiting to be processed...',
                'progress': 0,
            }
        elif task.state == 'PROGRESS':
            response = {
                'state': task.state,
                'current': task.info.get('current', 0),
                'total': task.info.get('total', 100),
                'progress': task.info.get('progress', 0),
                'status': task.info.get('status', 'Processing...'),
            }
        elif task.state == 'SUCCESS':
            response = {
                'state': task.state,
                'status': 'complete',
                'result': task.result,
                'progress': 100,
            }
        elif task.state == 'FAILURE':
            response = {
                'state': task.state,
                'status': 'Task failed',
                'error': str(task.info),
                'progress': 0,
            }
        else:
            response = {
                'state': task.state,
                'status': str(task.info),
            }

        return jsonify(response)

    except Exception as e:
        logger.error(f"Error checking task status: {str(e)}")
        return jsonify({
            'state': 'ERROR',
            'status': f'Error checking task: {str(e)}'
        }), 500


@bp.app_errorhandler(413)
def request_entity_too_large(error):
    """Handle file too large error."""
    return jsonify({
        'success': False,
        'error': 'File too large. Maximum file size is 50MB.'
    }), 413


@bp.app_errorhandler(429)
def ratelimit_handler(error):
    """Handle rate limit exceeded."""
    return jsonify({
        'success': False,
        'error': 'Rate limit exceeded. Please try again later.'
    }), 429


@bp.app_errorhandler(500)
def internal_server_error(error):
    """Handle internal server error."""
    logger.error(f"Internal server error: {str(error)}")
    return jsonify({
        'success': False,
        'error': 'An internal server error occurred'
    }), 500
