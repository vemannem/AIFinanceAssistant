"""FastAPI application setup and routes."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.core.config import Config
from src.core.logger import get_logger

logger = get_logger(__name__, Config.LOG_LEVEL)


def create_app() -> FastAPI:
    """Create and configure FastAPI application."""
    
    app = FastAPI(
        title="AI Finance Assistant",
        description="Multi-agent finance assistant with RAG",
        version="0.1.0"
    )
    
    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Health check
    @app.get("/health")
    async def health():
        return {"status": "ok", "version": "0.1.0"}
    
    # Config endpoint
    @app.get("/config")
    async def get_config():
        return Config.to_dict()
    
    # Import routes
    from src.web_app.routes.chat import router as chat_router
    from src.web_app.routes.market import router as market_router
    from src.web_app.routes.agents import router as agents_router
    
    app.include_router(chat_router, prefix="/api", tags=["chat"])
    app.include_router(market_router, prefix="/api", tags=["market"])
    app.include_router(agents_router, prefix="/api", tags=["agents"])
    
    logger.info(f"FastAPI app created on {Config.API_HOST}:{Config.API_PORT}")
    return app


app = create_app()
