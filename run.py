"""
Application entry point for Image Converter Pro.
Run this file to start the development server.
"""
import os
from app import create_app

# Create the Flask application
app = create_app()

if __name__ == '__main__':
    # Get configuration from environment or use defaults
    host = os.getenv('FLASK_RUN_HOST', '0.0.0.0')
    port = int(os.getenv('FLASK_RUN_PORT', 5000))
    debug = os.getenv('FLASK_ENV', 'development') == 'development'

    # Run the application
    print(f"Starting Image Converter Pro on http://{host}:{port}")
    print(f"Environment: {os.getenv('FLASK_ENV', 'development')}")
    print(f"Debug mode: {debug}")
    print("\nPress CTRL+C to quit\n")

    app.run(
        host=host,
        port=port,
        debug=debug
    )
