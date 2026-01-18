"""Configuration management and validation."""

import os
from pathlib import Path
from dotenv import load_dotenv
from src.core import ConfigError


# Load .env file
ENV_PATH = Path(__file__).parent.parent.parent / ".env"
if ENV_PATH.exists():
    load_dotenv(ENV_PATH)


class Config:
    """Configuration singleton."""
    
    # LLM Provider Selection
    LLM_PROVIDER = os.getenv("LLM_PROVIDER", "openai")  # "anthropic" or "openai"
    
    # OpenAI
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    OPENAI_EMBEDDING_MODEL = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")
    OPENAI_TEMPERATURE = float(os.getenv("OPENAI_TEMPERATURE", "0.7"))
    OPENAI_MAX_TOKENS = int(os.getenv("OPENAI_MAX_TOKENS", "2000"))
    
    # Anthropic (Claude) - Optional
    ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
    ANTHROPIC_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-3-5-sonnet-20241022")
    ANTHROPIC_TEMPERATURE = float(os.getenv("ANTHROPIC_TEMPERATURE", "0.7"))
    ANTHROPIC_MAX_TOKENS = int(os.getenv("ANTHROPIC_MAX_TOKENS", "2000"))
    
    # Pinecone
    PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
    PINECONE_INDEX_NAME = os.getenv("PINECONE_INDEX_NAME", "ai-finance-knowledge-base")
    
    # RAG
    RAG_RETRIEVAL_TOP_K = int(os.getenv("RAG_RETRIEVAL_TOP_K", "5"))
    RAG_MIN_RELEVANCE_THRESHOLD = float(os.getenv("RAG_MIN_RELEVANCE_THRESHOLD", "0.50"))
    
    # FastAPI
    API_HOST = os.getenv("API_HOST", "0.0.0.0")
    API_PORT = int(os.getenv("API_PORT", "8000"))
    API_WORKERS = int(os.getenv("API_WORKERS", "4"))
    
    # Logging
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    
    # Conversation Management
    CONVERSATION_MAX_HISTORY = int(os.getenv("CONVERSATION_MAX_HISTORY", "20"))
    CONVERSATION_SUMMARY_LENGTH = int(os.getenv("CONVERSATION_SUMMARY_LENGTH", "500"))
    CONVERSATION_SUMMARY_THRESHOLD = int(os.getenv("CONVERSATION_SUMMARY_THRESHOLD", "10"))
    
    @classmethod
    def validate(cls):
        """Validate required configuration."""
        errors = []
        
        if cls.LLM_PROVIDER == "anthropic":
            if not cls.ANTHROPIC_API_KEY:
                errors.append("ANTHROPIC_API_KEY not set")
        elif cls.LLM_PROVIDER == "openai":
            if not cls.OPENAI_API_KEY:
                errors.append("OPENAI_API_KEY not set")
        
        if not cls.PINECONE_API_KEY:
            errors.append("PINECONE_API_KEY not set")
        
        if errors:
            raise ConfigError(f"Configuration errors: {', '.join(errors)}")
    
    @classmethod
    def to_dict(cls) -> dict:
        """Return config as dictionary."""
        return {
            "openai_model": cls.OPENAI_MODEL,
            "openai_temperature": cls.OPENAI_TEMPERATURE,
            "pinecone_index": cls.PINECONE_INDEX_NAME,
            "rag_top_k": cls.RAG_RETRIEVAL_TOP_K,
            "api_host": cls.API_HOST,
            "api_port": cls.API_PORT,
        }
