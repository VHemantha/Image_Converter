# Image Converter Pro

A production-ready web application for converting images between multiple formats with high quality preservation, security, and modern user interface.

## Features

- **9+ Supported Formats**: JPG, PNG, WebP, AVIF, TIFF, BMP, GIF, ICO, HEIC
- **High Quality**: Lossless compression where possible, 95+ quality for lossy formats
- **Batch Conversion**: Convert multiple files simultaneously
- **Security First**: CSRF protection, rate limiting, file validation with magic numbers
- **Modern UI**: Responsive design with dark mode, drag-and-drop upload
- **Fast Processing**: Optimized conversion engine with format-specific settings
- **Privacy**: Files automatically deleted after download, no permanent storage

## Screenshots

*Coming soon*

## Table of Contents

- [Installation](#installation)
- [Quick Start](#quick-start)
- [Configuration](#configuration)
- [Usage](#usage)
- [Development](#development)
- [Testing](#testing)
- [Deployment](#deployment)
- [Project Structure](#project-structure)
- [License](#license)

## Installation

### Prerequisites

- Python 3.10 or higher
- pip (Python package installer)
- Virtual environment (recommended)

### Setup

1. **Clone the repository**
   ```bash
   cd Image_Converter
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   ```

3. **Activate the virtual environment**
   - Windows:
     ```bash
     venv\Scripts\activate
     ```
   - macOS/Linux:
     ```bash
     source venv/bin/activate
     ```

4. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

5. **Create environment file**
   ```bash
   copy .env.example .env
   ```

   Edit `.env` and set your configuration (especially `SECRET_KEY`)

## Quick Start

1. **Activate your virtual environment** (if not already activated)

2. **Run the development server**
   ```bash
   python run.py
   ```

3. **Open your browser**
   Navigate to: http://localhost:5000

4. **Start converting!**
   - Drag and drop images or click to browse
   - Select target format
   - Click "Convert Images"
   - Download your converted files

## Configuration

### Environment Variables

Key configuration variables in `.env`:

```env
# Flask
SECRET_KEY=your-secret-key-here
FLASK_ENV=development
MAX_CONTENT_LENGTH=52428800  # 50MB

# File Storage
UPLOAD_FOLDER=temp/uploads
CONVERTED_FOLDER=temp/converted
FILE_RETENTION_MINUTES=60

# Rate Limiting
RATE_LIMIT_PER_MINUTE=30
RATE_LIMIT_PER_HOUR=500
```

### Supported Formats

| Format | Extensions | Description | Transparency | Animation |
|--------|-----------|-------------|--------------|-----------|
| JPEG | .jpg, .jpeg | Lossy compression, ideal for photos | ❌ | ❌ |
| PNG | .png | Lossless with transparency | ✅ | ❌ |
| WebP | .webp | Modern format with excellent compression | ✅ | ✅ |
| AVIF | .avif | Next-gen format with superior compression | ✅ | ❌ |
| TIFF | .tiff, .tif | Lossless for professional use | ✅ | ❌ |
| BMP | .bmp | Uncompressed bitmap | ❌ | ❌ |
| GIF | .gif | Animation support with limited colors | ✅ | ✅ |
| ICO | .ico | Icon format for favicons | ✅ | ❌ |
| HEIC | .heic, .heif | High-efficiency format (Apple devices) | ✅ | ❌ |

## Usage

### Basic Conversion

1. Upload one or more image files
2. Select target format from dropdown
3. Click "Convert Images"
4. Download converted files individually

### Supported Operations

- **Single File**: Upload and convert one image
- **Batch Upload**: Upload multiple images at once
- **Format Selection**: Choose from 9 supported formats
- **Quality Preservation**: Automatic optimal settings per format

### File Size Limits

- Maximum file size: 50MB per image
- Rate limits: 30 requests/minute, 500 requests/hour

## Development

### Project Structure

```
Image_Converter/
├── app/
│   ├── __init__.py              # Flask app factory
│   ├── routes.py                # Application routes (Blueprint)
│   ├── config.py                # Configuration classes
│   ├── forms.py                 # Flask-WTF forms
│   ├── static/
│   │   ├── css/
│   │   │   └── styles.css       # Custom CSS
│   │   └── js/
│   │       └── main.js          # Frontend JavaScript
│   ├── templates/
│   │   ├── base.html            # Base template
│   │   └── index.html           # Main page
│   └── utils/
│       ├── file_validator.py    # Security validation
│       ├── image_converter.py   # Core conversion logic
│       └── file_manager.py      # File management
├── tests/                       # Unit and integration tests
├── run.py                       # Application entry point
├── requirements.txt             # Python dependencies
├── .env.example                # Environment variables template
└── README.md                   # This file
```

### Running in Development Mode

```bash
# Set development environment
$env:FLASK_ENV="development"  # Windows PowerShell
# export FLASK_ENV=development  # macOS/Linux

# Run with Flask development server
python run.py

# Or with Flask CLI
flask --app run run --debug
```

### Code Quality

```bash
# Run linter
bandit -r app/

# Check for security vulnerabilities
safety check

# Format code (if using black)
black app/
```

## Testing

### Running Tests

```bash
# Install testing dependencies
pip install pytest pytest-cov pytest-flask

# Run all tests
pytest

# Run with coverage report
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_file_validator.py
```

### Test Coverage Goals

- Unit tests: 80%+ coverage
- Integration tests for all routes
- Security tests for validation and CSRF
- End-to-end tests for user flows

## Deployment

### Production Checklist

- [ ] Set `SECRET_KEY` to a secure random value
- [ ] Set `FLASK_ENV=production`
- [ ] Configure `SESSION_COOKIE_SECURE=True` (requires HTTPS)
- [ ] Update `APP_URL` to production domain
- [ ] Set up Redis for Celery (Phase 2)
- [ ] Configure SSL/TLS certificates
- [ ] Set up monitoring and logging
- [ ] Configure automated backups
- [ ] Test rate limiting
- [ ] Run security scans

### Docker Deployment (Phase 4)

*Coming in Phase 4: Full Docker Compose setup with Flask, Celery, Redis, and Nginx*

### Environment Setup

```bash
# Generate secure secret key
python -c "import secrets; print(secrets.token_hex(32))"

# Set in .env
SECRET_KEY=<generated-key>
```

## Troubleshooting

### Common Issues

**Issue**: `ModuleNotFoundError: No module named 'pillow_heif'`
- **Solution**: Install pillow-heif: `pip install pillow-heif`

**Issue**: HEIC images not converting
- **Solution**: Ensure pillow-heif is installed and libheif system library is available

**Issue**: File validation errors
- **Solution**: Check that uploaded files are valid images, not corrupted or renamed

**Issue**: Rate limit errors
- **Solution**: Wait a few minutes or adjust rate limits in `.env`

## Roadmap

### Phase 1: Foundation ✅ (Completed)
- [x] Core image conversion
- [x] File validation and security
- [x] Basic Flask routes
- [x] Modern UI with Tailwind CSS
- [x] Drag-and-drop upload

### Phase 2: Asynchronous Processing (Next)
- [ ] Celery integration for background tasks
- [ ] Redis message broker setup
- [ ] Task queue management
- [ ] Progress tracking

### Phase 3: Real-time Progress
- [ ] Server-Sent Events (SSE) implementation
- [ ] Live progress updates
- [ ] Download all as ZIP
- [ ] Enhanced UI with progress bars

### Phase 4: Production Deployment
- [ ] Docker Compose setup
- [ ] Nginx reverse proxy
- [ ] SSL/TLS configuration
- [ ] Health check endpoints
- [ ] Centralized logging

### Phase 5: SEO Optimization
- [ ] Dynamic sitemap.xml
- [ ] Schema.org structured data
- [ ] Meta tags optimization
- [ ] Performance optimization

## Contributing

Contributions are welcome! Please follow these guidelines:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## Security

If you discover a security vulnerability, please email security@example.com instead of using the issue tracker.

## License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Built with [Flask](https://flask.palletsprojects.com/)
- Image processing by [Pillow](https://python-pillow.org/)
- UI styled with [Tailwind CSS](https://tailwindcss.com/)
- HEIC support via [pillow-heif](https://github.com/bigcat88/pillow_heif)

## Support

For issues, questions, or suggestions:
- Open an issue on GitHub
- Email: support@example.com
- Documentation: *Coming soon*

---

**Built with ❤️ for the open-source community**