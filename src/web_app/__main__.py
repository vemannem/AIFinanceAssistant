"""Module entry point for src.web_app - executes when running: python -m src.web_app"""

import sys
import os
import uvicorn

# Ensure the project root is in the path for module imports
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.web_app import app
from src.core.config import Config
from src.core.logger import get_logger

logger = get_logger(__name__)

def main():
    """Main entry point for the application."""
    # Validate config (non-blocking - log warnings but don't fail startup)
    try:
        Config.validate()
        logger.info("✓ Configuration validated successfully")
    except Exception as e:
        logger.warning(f"⚠ Configuration warning: {str(e)}")
        logger.info("Server will start with limited functionality")
    
    # Run server
    try:
        logger.info(f"Starting FastAPI server on {Config.API_HOST}:{Config.API_PORT}")
        uvicorn.run(
            app,
            host=Config.API_HOST,
            port=Config.API_PORT,
            workers=Config.API_WORKERS,
            log_level=Config.LOG_LEVEL.lower(),
        )
    except KeyboardInterrupt:
        logger.info("Server shutdown requested")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Failed to start server: {str(e)}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()

