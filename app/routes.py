"""
Routes for image conversion application.
Uses in-memory task manager with threading for async processing.
No external dependencies (Redis/Celery) required.
"""
from flask import Blueprint, render_template, request, jsonify, send_file, current_app, Response
import os
import uuid
import logging
import json
import time
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
from app.task_manager import submit_conversion, get_task

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
def upload():
    """Handle file upload and start async conversion."""
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
                validate_file_comprehensive(
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

        # Submit to background thread pool
        submit_conversion(task_id, file_list, target_format, current_app.config)

        return jsonify({
            'success': True,
            'task_id': task_id,
            'status': 'processing',
            'total_files': len(file_list),
            'async': True,
        })

    except Exception as e:
        logger.error(f"Error in upload endpoint: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'An error occurred during upload'
        }), 500


@bp.route('/download/<task_id>/<filename>')
def download(task_id, filename):
    """Download a single converted file."""
    try:
        safe_filename = os.path.basename(filename)

        if not safe_filename.startswith(task_id):
            return jsonify({
                'success': False,
                'error': 'Invalid file request'
            }), 403

        file_path = os.path.join(current_app.config['CONVERTED_FOLDER'], safe_filename)

        if not os.path.exists(file_path):
            return jsonify({
                'success': False,
                'error': 'File not found on server'
            }), 404

        return send_file(
            file_path,
            as_attachment=True,
            download_name=safe_filename,
            mimetype='application/octet-stream'
        )

    except Exception as e:
        logger.error(f"Error downloading file: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Error downloading file: {str(e)}'
        }), 500


@bp.route('/download-all/<task_id>')
def download_all(task_id):
    """Download all converted files as ZIP archive."""
    try:
        import zipfile
        import tempfile

        converted_folder = current_app.config['CONVERTED_FOLDER']

        task_files = []
        for filename in os.listdir(converted_folder):
            if filename.startswith(task_id):
                file_path = os.path.join(converted_folder, filename)
                if os.path.isfile(file_path):
                    task_files.append((filename, file_path))

        if not task_files:
            return jsonify({
                'success': False,
                'error': 'No converted files found for this task'
            }), 404

        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        zip_filename = f'converted_images_{timestamp}.zip'
        zip_path = os.path.join(tempfile.gettempdir(), zip_filename)

        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for filename, file_path in task_files:
                archive_name = filename.replace(f'{task_id}_', '')
                zipf.write(file_path, archive_name)

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


@bp.route('/stream/<task_id>')
def stream_progress(task_id):
    """SSE endpoint for real-time progress streaming."""
    def generate():
        max_iterations = 240  # 2 minutes at 500ms
        iteration = 0

        while iteration < max_iterations:
            task = get_task(task_id)

            if not task:
                yield f"data: {json.dumps({'state': 'PENDING', 'progress': 0, 'status': 'Waiting...'})}\n\n"
                time.sleep(0.5)
                iteration += 1
                continue

            state = task.get('state', 'PENDING')

            if state == 'SUCCESS':
                data = {
                    'state': 'SUCCESS',
                    'progress': 100,
                    'result': task.get('result', {}),
                    'status': 'Complete!'
                }
                yield f"data: {json.dumps(data)}\n\n"
                break

            elif state == 'FAILURE':
                data = {
                    'state': 'FAILURE',
                    'progress': 0,
                    'error': task.get('error', 'Unknown error'),
                    'status': 'Task failed'
                }
                yield f"data: {json.dumps(data)}\n\n"
                break

            else:
                data = {
                    'state': state,
                    'progress': task.get('progress', 0),
                    'current': task.get('current', 0),
                    'total': task.get('total', 0),
                    'status': task.get('status', 'Processing...')
                }
                yield f"data: {json.dumps(data)}\n\n"

            time.sleep(0.5)
            iteration += 1

        if iteration >= max_iterations:
            yield f"data: {json.dumps({'state': 'TIMEOUT', 'error': 'Task timeout'})}\n\n"

    return Response(generate(), mimetype='text/event-stream')


@bp.route('/status/<task_id>')
def task_status(task_id):
    """Polling endpoint for task status (fallback for SSE)."""
    task = get_task(task_id)

    if not task:
        return jsonify({
            'state': 'PENDING',
            'status': 'Task not found or still queued',
            'progress': 0,
        }), 200

    state = task.get('state', 'PENDING')

    if state == 'SUCCESS':
        return jsonify({
            'state': 'SUCCESS',
            'status': 'complete',
            'result': task.get('result', {}),
            'progress': 100,
        })
    elif state == 'FAILURE':
        return jsonify({
            'state': 'FAILURE',
            'status': 'Task failed',
            'error': task.get('error', 'Unknown error'),
            'progress': 0,
        })
    else:
        return jsonify({
            'state': state,
            'progress': task.get('progress', 0),
            'current': task.get('current', 0),
            'total': task.get('total', 0),
            'status': task.get('status', 'Processing...'),
        })


@bp.route('/health')
def health():
    """Health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat()
    })


@bp.route('/ready')
def ready():
    """Readiness probe."""
    try:
        upload_folder = current_app.config['UPLOAD_FOLDER']
        converted_folder = current_app.config['CONVERTED_FOLDER']

        if not os.path.exists(upload_folder) or not os.access(upload_folder, os.W_OK):
            return jsonify({'status': 'not ready', 'error': 'Upload folder not accessible'}), 503

        if not os.path.exists(converted_folder) or not os.access(converted_folder, os.W_OK):
            return jsonify({'status': 'not ready', 'error': 'Converted folder not accessible'}), 503

        return jsonify({'status': 'ready', 'timestamp': datetime.utcnow().isoformat()})

    except Exception as e:
        return jsonify({'status': 'not ready', 'error': str(e)}), 503


@bp.route('/formats')
def formats():
    """Get supported format information."""
    return jsonify({
        'formats': get_supported_formats(),
        'format_info': get_format_info()
    })


@bp.app_errorhandler(413)
def request_entity_too_large(error):
    return jsonify({'success': False, 'error': 'File too large. Maximum file size is 50MB.'}), 413


@bp.app_errorhandler(429)
def ratelimit_handler(error):
    return jsonify({'success': False, 'error': 'Rate limit exceeded. Please try again later.'}), 429


@bp.app_errorhandler(500)
def internal_server_error(error):
    logger.error(f"Internal server error: {str(error)}")
    return jsonify({'success': False, 'error': 'An internal server error occurred'}), 500
