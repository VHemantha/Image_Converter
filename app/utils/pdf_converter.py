"""
PDF conversion utility.
Converts images to a multi-page PDF using Pillow.
"""
import os
import logging
from PIL import Image

logger = logging.getLogger(__name__)


class PdfConversionError(Exception):
    """Raised when PDF conversion fails."""
    pass


def convert_images_to_pdf(image_paths, output_path):
    """
    Convert one or more images into a single multi-page PDF file.

    Args:
        image_paths (list[str]): Ordered list of absolute paths to input images.
        output_path (str): Absolute path for the output PDF file.

    Returns:
        dict: {'success': True, 'page_count': int, 'file_size': int}

    Raises:
        PdfConversionError: If conversion fails.
    """
    if not image_paths:
        raise PdfConversionError("No images provided for conversion.")

    rgb_images = []

    for img_path in image_paths:
        try:
            img = Image.open(img_path)
            img.load()

            # PDF requires RGB mode — flatten any transparency onto white background
            if img.mode in ('RGBA', 'LA'):
                background = Image.new('RGB', img.size, (255, 255, 255))
                background.paste(img, mask=img.split()[-1])
                img = background
            elif img.mode == 'P':
                # Palette mode (GIF etc.) — convert via RGBA to preserve transparency
                rgba = img.convert('RGBA')
                background = Image.new('RGB', rgba.size, (255, 255, 255))
                background.paste(rgba, mask=rgba.split()[-1])
                img = background
            elif img.mode != 'RGB':
                img = img.convert('RGB')

            rgb_images.append(img)

        except Exception as exc:
            raise PdfConversionError(
                f"Failed to process image '{os.path.basename(img_path)}': {exc}"
            ) from exc

    if not rgb_images:
        raise PdfConversionError("No valid images could be loaded.")

    try:
        rgb_images[0].save(
            output_path,
            format='PDF',
            save_all=True,
            append_images=rgb_images[1:],
            resolution=100.0,
        )
    except Exception as exc:
        raise PdfConversionError(f"Failed to write PDF: {exc}") from exc

    return {
        'success': True,
        'page_count': len(rgb_images),
        'file_size': os.path.getsize(output_path),
    }
