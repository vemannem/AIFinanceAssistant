"""Application entry point."""

import uvicorn
from src.web_app import app
from src.core.config import Config

if __name__ == "__main__":
    # Validate config
    Config.validate()
    
    # Run server
    uvicorn.run(
        app,
        host=Config.API_HOST,
        port=Config.API_PORT,
        workers=Config.API_WORKERS,
    )
