"""
Flask-WTF forms for file upload and conversion.
Includes custom validators for security and file validation.
"""
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired, FileAllowed
from wtforms import SelectField, MultipleFileField
from wtforms.validators import DataRequired, ValidationError
from werkzeug.datastructures import FileStorage


class UploadForm(FlaskForm):
    """Form for uploading and converting images."""

    # Multiple file upload field
    files = MultipleFileField(
        'Image Files',
        validators=[FileRequired(message='Please select at least one file to upload')]
    )

    # Target format selection
    target_format = SelectField(
        'Convert To',
        choices=[
            ('JPEG', 'JPEG - Best for photographs'),
            ('PNG', 'PNG - Lossless with transparency'),
            ('WEBP', 'WebP - Modern web format'),
            ('AVIF', 'AVIF - Next-gen compression'),
            ('TIFF', 'TIFF - Professional quality'),
            ('BMP', 'BMP - Uncompressed bitmap'),
            ('GIF', 'GIF - Animation support'),
            ('ICO', 'ICO - Icon format'),
            ('HEIC', 'HEIC - High efficiency'),
        ],
        validators=[DataRequired(message='Please select a target format')]
    )

    def validate_files(self, field):
        """
        Custom validator for uploaded files.
        Validates file extensions and basic checks.
        """
        if not field.data:
            raise ValidationError('Please select at least one file')

        allowed_extensions = {'jpg', 'jpeg', 'png', 'webp', 'avif', 'tiff', 'tif', 'bmp', 'gif', 'ico', 'heic', 'heif'}

        for file in field.data:
            if not isinstance(file, FileStorage):
                continue

            # Check if file has a filename
            if not file.filename:
                raise ValidationError('One or more files have no filename')

            # Check file extension
            if '.' not in file.filename:
                raise ValidationError(f'File "{file.filename}" has no extension')

            ext = file.filename.rsplit('.', 1)[1].lower()
            if ext not in allowed_extensions:
                raise ValidationError(
                    f'File "{file.filename}" has invalid extension. '
                    f'Allowed: {", ".join(sorted(allowed_extensions))}'
                )


class SingleUploadForm(FlaskForm):
    """Form for uploading a single image file."""

    file = FileField(
        'Image File',
        validators=[
            FileRequired(message='Please select a file to upload'),
            FileAllowed(
                ['jpg', 'jpeg', 'png', 'webp', 'avif', 'tiff', 'tif', 'bmp', 'gif', 'ico', 'heic', 'heif'],
                message='Invalid file type. Please upload an image file.'
            )
        ]
    )

    target_format = SelectField(
        'Convert To',
        choices=[
            ('JPEG', 'JPEG'),
            ('PNG', 'PNG'),
            ('WEBP', 'WebP'),
            ('AVIF', 'AVIF'),
            ('TIFF', 'TIFF'),
            ('BMP', 'BMP'),
            ('GIF', 'GIF'),
            ('ICO', 'ICO'),
            ('HEIC', 'HEIC'),
        ],
        validators=[DataRequired()]
    )
