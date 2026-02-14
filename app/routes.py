"""
Routes for image conversion application.
Phase 1: Synchronous conversion (Celery integration in Phase 2)
"""
from flask import Blueprint, render_template, request, jsonify, send_file, session, current_app
import os
import uuid
import logging
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
    Download all converted files as ZIP.
    (To be implemented in Phase 3)
    """
    return jsonify({
        'success': False,
        'error': 'ZIP download not yet implemented'
    }), 501


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


@bp.route('/status/<task_id>')
def task_status(task_id):
    """
    Check the status of a Celery task.
    Returns progress information for async conversions.
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
