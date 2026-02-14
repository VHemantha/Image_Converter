"""
File validation utilities with security-focused checks.
Implements magic number verification, file size limits, and sanitization.
"""
import os
import magic
from PIL import Image
from werkzeug.utils import secure_filename
import uuid


# Allowed MIME types mapped to extensions
ALLOWED_MIME_TYPES = {
    'image/jpeg': ['jpg', 'jpeg'],
    'image/png': ['png'],
    'image/webp': ['webp'],
    'image/avif': ['avif'],
    'image/tiff': ['tiff', 'tif'],
    'image/bmp': ['bmp'],
    'image/gif': ['gif'],
    'image/x-icon': ['ico'],
    'image/vnd.microsoft.icon': ['ico'],
    'image/heic': ['heic', 'heif'],
    'image/heif': ['heic', 'heif'],
}

# Magic number signatures for additional validation
MAGIC_NUMBERS = {
    'jpg': [b'\xFF\xD8\xFF'],
    'png': [b'\x89PNG\r\n\x1a\n'],
    'gif': [b'GIF87a', b'GIF89a'],
    'bmp': [b'BM'],
    'tiff': [b'II*\x00', b'MM\x00*'],
    'webp': [b'RIFF', b'WEBP'],
    'ico': [b'\x00\x00\x01\x00'],
}


class FileValidationError(Exception):
    """Custom exception for file validation errors."""
    pass


def validate_file_magic(file, max_bytes=2048):
    """
    Validate file type using magic number (file signature).

    Args:
        file: File object to validate
        max_bytes: Number of bytes to read for magic number detection

    Returns:
        tuple: (mime_type, is_valid)

    Raises:
        FileValidationError: If file type is not allowed
    """
    try:
        # Read initial bytes for magic number detection
        file_header = file.read(max_bytes)
        file.seek(0)  # Reset file pointer

        if not file_header:
            raise FileValidationError("Empty file or unable to read file")

        # Detect MIME type using python-magic
        mime = magic.Magic(mime=True)
        detected_mime = mime.from_buffer(file_header)

        # Check if MIME type is allowed
        if detected_mime not in ALLOWED_MIME_TYPES:
            raise FileValidationError(
                f"File type '{detected_mime}' is not allowed. "
                f"Allowed types: {', '.join(ALLOWED_MIME_TYPES.keys())}"
            )

        return detected_mime, True

    except Exception as e:
        if isinstance(e, FileValidationError):
            raise
        raise FileValidationError(f"Error detecting file type: {str(e)}")


def validate_file_size(file, max_size_bytes):
    """
    Validate that file size is within allowed limit.

    Args:
        file: File object to validate
        max_size_bytes: Maximum allowed file size in bytes

    Returns:
        int: File size in bytes

    Raises:
        FileValidationError: If file exceeds size limit
    """
    try:
        # Get file size
        file.seek(0, os.SEEK_END)
        file_size = file.tell()
        file.seek(0)  # Reset file pointer

        if file_size == 0:
            raise FileValidationError("File is empty")

        if file_size > max_size_bytes:
            max_size_mb = max_size_bytes / (1024 * 1024)
            file_size_mb = file_size / (1024 * 1024)
            raise FileValidationError(
                f"File size ({file_size_mb:.2f} MB) exceeds maximum allowed size ({max_size_mb:.2f} MB)"
            )

        return file_size

    except Exception as e:
        if isinstance(e, FileValidationError):
            raise
        raise FileValidationError(f"Error checking file size: {str(e)}")


def validate_image_with_pillow(file):
    """
    Validate that file is a valid image using Pillow.
    This provides an additional layer of security by attempting to open and verify the image.

    Args:
        file: File object to validate

    Returns:
        tuple: (format, size_tuple)

    Raises:
        FileValidationError: If file is not a valid image
    """
    try:
        # Attempt to open image with Pillow
        img = Image.open(file)

        # Verify image integrity
        img.verify()

        # Get format and size
        file.seek(0)  # Reset after verify()
        img = Image.open(file)  # Reopen after verify()
        img_format = img.format
        img_size = img.size

        file.seek(0)  # Reset file pointer

        return img_format, img_size

    except Exception as e:
        raise FileValidationError(f"File is not a valid image: {str(e)}")


def sanitize_filename(filename, task_id=None):
    """
    Sanitize filename to prevent path traversal and other security issues.
    Generates a unique filename with UUID prefix.

    Args:
        filename: Original filename
        task_id: Optional task ID to include in filename

    Returns:
        str: Sanitized filename with UUID prefix
    """
    # Use werkzeug's secure_filename as base
    safe_name = secure_filename(filename)

    # Additional sanitization
    safe_name = safe_name.replace('..', '')
    safe_name = os.path.basename(safe_name)

    # Remove any remaining path separators
    safe_name = safe_name.replace(os.sep, '_')
    safe_name = safe_name.replace(os.altsep or '', '_')

    # If filename is empty after sanitization, use default
    if not safe_name or safe_name == '':
        safe_name = 'image.jpg'

    # Generate unique filename with UUID
    name, ext = os.path.splitext(safe_name)

    if task_id:
        unique_name = f"{task_id}_{name}{ext}"
    else:
        unique_name = f"{uuid.uuid4().hex}_{name}{ext}"

    return unique_name


def validate_extension(filename, allowed_extensions):
    """
    Validate file extension.

    Args:
        filename: Filename to check
        allowed_extensions: Set of allowed extensions

    Returns:
        bool: True if extension is allowed

    Raises:
        FileValidationError: If extension is not allowed
    """
    if '.' not in filename:
        raise FileValidationError("File has no extension")

    ext = filename.rsplit('.', 1)[1].lower()

    if ext not in allowed_extensions:
        raise FileValidationError(
            f"File extension '.{ext}' is not allowed. "
            f"Allowed extensions: {', '.join(allowed_extensions)}"
        )

    return True


def validate_file_comprehensive(file, filename, max_size_bytes, allowed_extensions):
    """
    Comprehensive file validation combining all checks.

    Security checks performed:
    1. File extension validation
    2. Magic number verification
    3. File size check
    4. Pillow image validation
    5. Filename sanitization

    Args:
        file: File object to validate
        filename: Original filename
        max_size_bytes: Maximum allowed file size
        allowed_extensions: Set of allowed file extensions

    Returns:
        dict: Validation results with sanitized filename, mime type, size, etc.

    Raises:
        FileValidationError: If any validation check fails
    """
    validation_result = {}

    # 1. Validate extension
    validate_extension(filename, allowed_extensions)
    validation_result['original_filename'] = filename

    # 2. Sanitize filename
    sanitized_name = sanitize_filename(filename)
    validation_result['sanitized_filename'] = sanitized_name

    # 3. Validate file size
    file_size = validate_file_size(file, max_size_bytes)
    validation_result['file_size'] = file_size

    # 4. Validate magic number
    mime_type, _ = validate_file_magic(file)
    validation_result['mime_type'] = mime_type

    # 5. Validate with Pillow
    img_format, img_size = validate_image_with_pillow(file)
    validation_result['image_format'] = img_format
    validation_result['image_size'] = img_size
    validation_result['width'] = img_size[0]
    validation_result['height'] = img_size[1]

    # 6. Verify MIME type matches extension
    ext = filename.rsplit('.', 1)[1].lower()
    if ext not in ALLOWED_MIME_TYPES.get(mime_type, []):
        # Special case: HEIC/HEIF extensions are interchangeable
        if not (ext in ['heic', 'heif'] and mime_type in ['image/heic', 'image/heif']):
            raise FileValidationError(
                f"File extension '.{ext}' does not match detected file type '{mime_type}'"
            )

    validation_result['is_valid'] = True

    return validation_result


def get_supported_formats():
    """
    Get list of supported image formats.

    Returns:
        list: List of supported format names
    """
    return ['JPEG', 'PNG', 'WebP', 'AVIF', 'TIFF', 'BMP', 'GIF', 'ICO', 'HEIC']


def get_format_info():
    """
    Get detailed information about supported formats.

    Returns:
        dict: Format information including description and use cases
    """
    return {
        'JPEG': {
            'name': 'JPEG',
            'extensions': ['.jpg', '.jpeg'],
            'description': 'Lossy compression, ideal for photographs',
            'supports_transparency': False,
            'supports_animation': False,
        },
        'PNG': {
            'name': 'PNG',
            'extensions': ['.png'],
            'description': 'Lossless compression with transparency support',
            'supports_transparency': True,
            'supports_animation': False,
        },
        'WebP': {
            'name': 'WebP',
            'extensions': ['.webp'],
            'description': 'Modern format with excellent compression',
            'supports_transparency': True,
            'supports_animation': True,
        },
        'AVIF': {
            'name': 'AVIF',
            'extensions': ['.avif'],
            'description': 'Next-gen format with superior compression',
            'supports_transparency': True,
            'supports_animation': False,
        },
        'TIFF': {
            'name': 'TIFF',
            'extensions': ['.tiff', '.tif'],
            'description': 'Lossless format for professional use',
            'supports_transparency': True,
            'supports_animation': False,
        },
        'BMP': {
            'name': 'BMP',
            'extensions': ['.bmp'],
            'description': 'Uncompressed bitmap format',
            'supports_transparency': False,
            'supports_animation': False,
        },
        'GIF': {
            'name': 'GIF',
            'extensions': ['.gif'],
            'description': 'Animation support with limited colors',
            'supports_transparency': True,
            'supports_animation': True,
        },
        'ICO': {
            'name': 'ICO',
            'extensions': ['.ico'],
            'description': 'Icon format for favicons',
            'supports_transparency': True,
            'supports_animation': False,
        },
        'HEIC': {
            'name': 'HEIC',
            'extensions': ['.heic', '.heif'],
            'description': 'High-efficiency format used by Apple devices',
            'supports_transparency': True,
            'supports_animation': False,
        },
    }
