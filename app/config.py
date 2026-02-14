"""
Configuration classes for the Image Converter application.
Loads settings from environment variables with sensible defaults.
"""
import os
from datetime import timedelta
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class BaseConfig:
    """Base configuration with common settings."""

    # Flask Core
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')

    # File Upload Settings
    MAX_CONTENT_LENGTH = int(os.getenv('MAX_CONTENT_LENGTH', 52428800))  # 50MB default

    # Get project root directory (parent of app directory)
    PROJECT_ROOT = os.path.dirname(os.path.dirname(__file__))

    # Ensure upload and converted folders are absolute paths
    upload_folder_env = os.getenv('UPLOAD_FOLDER', 'temp/uploads')
    converted_folder_env = os.getenv('CONVERTED_FOLDER', 'temp/converted')

    UPLOAD_FOLDER = upload_folder_env if os.path.isabs(upload_folder_env) else os.path.join(PROJECT_ROOT, upload_folder_env)
    CONVERTED_FOLDER = converted_folder_env if os.path.isabs(converted_folder_env) else os.path.join(PROJECT_ROOT, converted_folder_env)

    ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'webp', 'avif', 'tiff', 'tif', 'bmp', 'gif', 'ico', 'heic', 'heif'}
    FILE_RETENTION_MINUTES = int(os.getenv('FILE_RETENTION_MINUTES', 60))

    # Redis Configuration
    REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
    CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0')
    CELERY_RESULT_BACKEND = os.getenv('CELERY_RESULT_BACKEND', 'redis://localhost:6379/1')

    # Rate Limiting
    RATELIMIT_STORAGE_URL = os.getenv('RATE_LIMIT_STORAGE_URL', 'redis://localhost:6379/2')
    RATELIMIT_ENABLED = True
    RATELIMIT_DEFAULT = os.getenv('RATE_LIMIT_PER_HOUR', '500 per hour')
    RATELIMIT_PER_MINUTE = os.getenv('RATE_LIMIT_PER_MINUTE', '30 per minute')

    # Session Configuration
    SESSION_COOKIE_SECURE = False  # Set to True in production with HTTPS
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    PERMANENT_SESSION_LIFETIME = timedelta(hours=2)

    # CSRF Protection
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = None  # No time limit for CSRF tokens

    # Application Settings
    APP_NAME = os.getenv('APP_NAME', 'Image Converter Pro')
    APP_URL = os.getenv('APP_URL', 'http://localhost:5000')

    # Logging
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE_ERRORS = os.getenv('LOG_FILE_ERRORS', 'logs/errors.log')
    LOG_FILE_ACCESS = os.getenv('LOG_FILE_ACCESS', 'logs/access.log')
    LOG_FILE_CONVERSIONS = os.getenv('LOG_FILE_CONVERSIONS', 'logs/conversions.log')


class DevelopmentConfig(BaseConfig):
    """Development environment configuration."""

    DEBUG = True
    TESTING = False
    ENV = 'development'

    # Relaxed security for development
    SESSION_COOKIE_SECURE = False
    WTF_CSRF_ENABLED = True  # Still enable CSRF in development

    # Verbose logging
    LOG_LEVEL = 'DEBUG'


class ProductionConfig(BaseConfig):
    """Production environment configuration."""

    DEBUG = False
    TESTING = False
    ENV = 'production'

    # Strict security for production
    SESSION_COOKIE_SECURE = True  # Requires HTTPS
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Strict'

    # Security headers (Flask-Talisman)
    FORCE_HTTPS = True
    STRICT_TRANSPORT_SECURITY = True
    STRICT_TRANSPORT_SECURITY_MAX_AGE = 31536000  # 1 year

    # Production logging
    LOG_LEVEL = 'WARNING'


class TestingConfig(BaseConfig):
    """Testing environment configuration."""

    TESTING = True
    DEBUG = True
    ENV = 'testing'

    # Use separate Redis DB for testing
    REDIS_URL = 'redis://localhost:6379/10'
    CELERY_BROKER_URL = 'redis://localhost:6379/10'
    CELERY_RESULT_BACKEND = 'redis://localhost:6379/11'
    RATELIMIT_STORAGE_URL = 'redis://localhost:6379/12'

    # Disable rate limiting in tests
    RATELIMIT_ENABLED = False

    # Use temporary directories for testing
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'temp', 'test_uploads')
    CONVERTED_FOLDER = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'temp', 'test_converted')

    # CSRF enabled but not enforced in tests
    WTF_CSRF_ENABLED = False


# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}


def get_config(env=None):
    """Get configuration based on environment."""
    if env is None:
        env = os.getenv('FLASK_ENV', 'development')
    return config.get(env, config['default'])
