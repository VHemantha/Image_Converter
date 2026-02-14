"""
Core image conversion logic with format-specific optimization.
Implements quality preservation, metadata handling, and lossless conversion where possible.
"""
import os
from PIL import Image, ImageFile
from pillow_heif import register_heif_opener

# Enable HEIC/HEIF support
register_heif_opener()

# Allow loading of truncated images (helpful for large files)
ImageFile.LOAD_TRUNCATED_IMAGES = True


# Quality settings for each format (optimized for quality preservation)
QUALITY_SETTINGS = {
    'JPEG': {
        'quality': 95,
        'optimize': True,
        'progressive': True,
    },
    'PNG': {
        'optimize': True,
        'compress_level': 9,  # Maximum compression (lossless)
    },
    'WEBP': {
        'quality': 95,
        'method': 6,  # Best compression method (0-6)
        'lossless': False,  # Set to True for lossless WebP
    },
    'AVIF': {
        'quality': 95,
        'speed': 4,  # Encoding speed (0-10, lower is slower but better quality)
    },
    'TIFF': {
        'compression': 'tiff_lzw',  # Lossless compression
    },
    'BMP': {
        # BMP is inherently lossless
    },
    'GIF': {
        'optimize': True,
    },
    'ICO': {
        'sizes': [(256, 256)],  # ICO sizes
    },
}

# Format mappings
FORMAT_ALIASES = {
    'JPG': 'JPEG',
    'TIF': 'TIFF',
    'HEIF': 'HEIC',
}


class ImageConversionError(Exception):
    """Custom exception for image conversion errors."""
    pass


def normalize_format(format_name):
    """
    Normalize format name to standard PIL format.

    Args:
        format_name: Format name to normalize

    Returns:
        str: Normalized format name
    """
    format_upper = format_name.upper()
    return FORMAT_ALIASES.get(format_upper, format_upper)


def get_optimal_settings(source_format, target_format):
    """
    Get optimal conversion settings based on source and target formats.

    Args:
        source_format: Source image format
        target_format: Target image format

    Returns:
        dict: Optimization settings for target format
    """
    target_format = normalize_format(target_format)
    return QUALITY_SETTINGS.get(target_format, {})


def prepare_image_for_format(img, target_format):
    """
    Prepare image for specific format (handle transparency, color modes, etc.).

    Args:
        img: PIL Image object
        target_format: Target format name

    Returns:
        PIL Image object: Prepared image
    """
    target_format = normalize_format(target_format)

    # Handle transparency for formats that don't support it
    if target_format in ['JPEG', 'BMP']:
        if img.mode in ('RGBA', 'LA', 'P'):
            # Create white background
            background = Image.new('RGB', img.size, (255, 255, 255))

            # Paste image with alpha channel as mask
            if img.mode == 'P':
                img = img.convert('RGBA')

            if img.mode in ('RGBA', 'LA'):
                background.paste(img, mask=img.split()[-1])  # Use alpha channel as mask
            else:
                background.paste(img)

            img = background
        elif img.mode != 'RGB':
            img = img.convert('RGB')

    # Handle palette mode for other formats
    elif img.mode == 'P':
        # Convert palette to RGBA if it has transparency
        if 'transparency' in img.info:
            img = img.convert('RGBA')
        else:
            img = img.convert('RGB')

    # Handle grayscale with alpha
    elif img.mode == 'LA':
        if target_format in ['PNG', 'WEBP', 'TIFF', 'ICO']:
            img = img.convert('RGBA')
        else:
            img = img.convert('L')

    # Handle CMYK mode
    elif img.mode == 'CMYK':
        img = img.convert('RGB')

    return img


def preserve_metadata(source_img, target_img):
    """
    Preserve EXIF and other metadata from source to target image.

    Args:
        source_img: Source PIL Image object
        target_img: Target PIL Image object

    Returns:
        dict: Metadata to include in save operation
    """
    metadata = {}

    # Preserve EXIF data if available
    if hasattr(source_img, '_getexif') and source_img._getexif():
        metadata['exif'] = source_img.info.get('exif', b'')

    # Preserve ICC profile for color accuracy
    if 'icc_profile' in source_img.info:
        metadata['icc_profile'] = source_img.info['icc_profile']

    # Preserve DPI information
    if 'dpi' in source_img.info:
        metadata['dpi'] = source_img.info['dpi']

    return metadata


def convert_animated_gif(img, output_path, target_format, quality_settings):
    """
    Special handling for animated GIFs.

    Args:
        img: PIL Image object (GIF)
        output_path: Output file path
        target_format: Target format
        quality_settings: Quality settings for target format

    Returns:
        bool: True if successful
    """
    # Check if GIF is animated
    if not hasattr(img, 'n_frames') or img.n_frames <= 1:
        # Not animated, use regular conversion
        return False

    # For animated GIFs to formats that support animation
    if target_format in ['WEBP', 'GIF']:
        frames = []
        durations = []

        try:
            for frame_num in range(img.n_frames):
                img.seek(frame_num)
                frame = img.copy()

                # Convert frame if necessary
                if target_format == 'WEBP' and frame.mode != 'RGBA':
                    frame = frame.convert('RGBA')

                frames.append(frame)

                # Get frame duration
                duration = img.info.get('duration', 100)
                durations.append(duration)

            # Save animated image
            frames[0].save(
                output_path,
                format=target_format,
                save_all=True,
                append_images=frames[1:],
                duration=durations,
                loop=img.info.get('loop', 0),
                **quality_settings
            )
            return True

        except Exception as e:
            raise ImageConversionError(f"Error converting animated GIF: {str(e)}")

    # For non-animated formats, return False to use first frame
    return False


def convert_image(input_path, output_path, target_format, quality=None):
    """
    Convert image from one format to another with quality preservation.

    Args:
        input_path: Path to input image
        output_path: Path to output image
        target_format: Target format name (JPEG, PNG, WebP, etc.)
        quality: Optional quality override (1-100)

    Returns:
        dict: Conversion result with metadata

    Raises:
        ImageConversionError: If conversion fails
    """
    try:
        # Normalize format name
        target_format = normalize_format(target_format)

        # Open source image
        with Image.open(input_path) as img:
            source_format = img.format
            source_size = img.size
            source_mode = img.mode

            # Get optimal settings for target format
            quality_settings = get_optimal_settings(source_format, target_format)

            # Override quality if specified
            if quality is not None and 'quality' in quality_settings:
                quality_settings = quality_settings.copy()
                quality_settings['quality'] = quality

            # Special handling for animated GIFs
            if source_format == 'GIF':
                if convert_animated_gif(img, output_path, target_format, quality_settings):
                    # Animated GIF successfully converted
                    return {
                        'success': True,
                        'source_format': source_format,
                        'target_format': target_format,
                        'source_size': source_size,
                        'is_animated': True,
                        'input_file_size': os.path.getsize(input_path),
                        'output_file_size': os.path.getsize(output_path),
                    }

            # Prepare image for target format
            converted_img = prepare_image_for_format(img.copy(), target_format)

            # Preserve metadata
            metadata = preserve_metadata(img, converted_img)

            # Merge quality settings with metadata
            save_kwargs = {**quality_settings, **metadata}

            # Save converted image
            if target_format == 'ICO':
                # ICO requires special handling for multiple sizes
                sizes = save_kwargs.pop('sizes', [(256, 256)])
                converted_img.save(output_path, format=target_format, sizes=sizes)
            else:
                converted_img.save(output_path, format=target_format, **save_kwargs)

        # Get file sizes
        input_size = os.path.getsize(input_path)
        output_size = os.path.getsize(output_path)

        return {
            'success': True,
            'source_format': source_format,
            'target_format': target_format,
            'source_size': source_size,
            'source_mode': source_mode,
            'input_file_size': input_size,
            'output_file_size': output_size,
            'compression_ratio': (1 - output_size / input_size) * 100 if input_size > 0 else 0,
            'is_animated': False,
        }

    except Exception as e:
        raise ImageConversionError(f"Failed to convert image: {str(e)}")


def calculate_file_sizes(input_path, output_path):
    """
    Calculate and compare file sizes.

    Args:
        input_path: Path to input file
        output_path: Path to output file

    Returns:
        dict: File size comparison
    """
    input_size = os.path.getsize(input_path)
    output_size = os.path.getsize(output_path)

    return {
        'input_size_bytes': input_size,
        'output_size_bytes': output_size,
        'input_size_mb': input_size / (1024 * 1024),
        'output_size_mb': output_size / (1024 * 1024),
        'size_difference_bytes': output_size - input_size,
        'size_difference_percent': ((output_size - input_size) / input_size * 100) if input_size > 0 else 0,
        'compression_ratio': (1 - output_size / input_size) * 100 if input_size > 0 else 0,
    }


def batch_convert_images(input_paths, output_dir, target_format, quality=None):
    """
    Convert multiple images to target format.

    Args:
        input_paths: List of input file paths
        output_dir: Output directory
        target_format: Target format name
        quality: Optional quality override

    Returns:
        list: List of conversion results
    """
    results = []

    for input_path in input_paths:
        try:
            # Generate output filename
            basename = os.path.basename(input_path)
            name_without_ext = os.path.splitext(basename)[0]
            output_filename = f"{name_without_ext}.{target_format.lower()}"
            output_path = os.path.join(output_dir, output_filename)

            # Convert image
            result = convert_image(input_path, output_path, target_format, quality)
            result['input_path'] = input_path
            result['output_path'] = output_path

            results.append(result)

        except Exception as e:
            results.append({
                'success': False,
                'input_path': input_path,
                'error': str(e),
            })

    return results


def get_image_info(image_path):
    """
    Get detailed information about an image.

    Args:
        image_path: Path to image file

    Returns:
        dict: Image information
    """
    try:
        with Image.open(image_path) as img:
            info = {
                'format': img.format,
                'mode': img.mode,
                'size': img.size,
                'width': img.size[0],
                'height': img.size[1],
                'file_size': os.path.getsize(image_path),
                'file_size_mb': os.path.getsize(image_path) / (1024 * 1024),
            }

            # Add animation info for GIFs
            if img.format == 'GIF':
                info['is_animated'] = hasattr(img, 'n_frames') and img.n_frames > 1
                info['n_frames'] = getattr(img, 'n_frames', 1)

            # Add EXIF data if available
            if hasattr(img, '_getexif') and img._getexif():
                info['has_exif'] = True

            # Add DPI if available
            if 'dpi' in img.info:
                info['dpi'] = img.info['dpi']

            return info

    except Exception as e:
        return {
            'error': str(e),
            'file_size': os.path.getsize(image_path) if os.path.exists(image_path) else 0,
        }
