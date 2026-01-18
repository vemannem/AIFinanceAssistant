"""Custom exceptions for AI Finance Assistant."""


class AIFinanceException(Exception):
    """Base exception for all AI Finance errors."""
    pass


class ConfigError(AIFinanceException):
    """Configuration error (missing keys, invalid values)."""
    pass


class LLMError(AIFinanceException):
    """LLM API error (rate limit, invalid response, etc)."""
    pass


class RAGError(AIFinanceException):
    """RAG/Pinecone error (retrieval failure, embedding error)."""
    pass


class AgentError(AIFinanceException):
    """Agent execution error."""
    pass


class MarketDataError(AIFinanceException):
    """Market data provider error (yFinance down, invalid ticker)."""
    pass


class ValidationError(AIFinanceException):
    """Input validation error."""
    pass
