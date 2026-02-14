"""
Flask application factory.
"""
from flask import Flask
from flask_wtf.csrf import CSRFProtect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import os

csrf = CSRFProtect()
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["500 per hour", "30 per minute"]
)


def create_app(config_name=None):
    """
    Application factory pattern.

    Args:
        config_name: Configuration name (development, production, testing)

    Returns:
        Flask application instance
    """
    app = Flask(__name__)

    # Load configuration
    if config_name is None:
        config_name = os.getenv('FLASK_ENV', 'development')

    from .config import get_config
    app.config.from_object(get_config(config_name))

    # Initialize extensions
    csrf.init_app(app)

    if app.config.get('RATELIMIT_ENABLED', True):
        limiter.init_app(app)

    # Create necessary directories
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(app.config['CONVERTED_FOLDER'], exist_ok=True)
    os.makedirs('logs', exist_ok=True)

    # Register blueprints
    from .routes import bp as main_bp
    app.register_blueprint(main_bp)

    # Configure logging
    import logging
    logging.basicConfig(
        level=app.config.get('LOG_LEVEL', 'INFO'),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Context processors
    @app.context_processor
    def utility_processor():
        from datetime import datetime
        return dict(current_year=datetime.now().year)

    return app
