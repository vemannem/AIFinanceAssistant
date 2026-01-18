"""Base agent class."""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from src.core.logger import get_logger
from src.core.config import Config

logger = get_logger(__name__, Config.LOG_LEVEL)


@dataclass
class AgentOutput:
    """Standard output from all agents."""
    answer_text: str
    structured_data: Optional[Dict[str, Any]] = None
    citations: List[Dict[str, str]] = field(default_factory=list)
    tool_calls_made: List[str] = field(default_factory=list)


class BaseAgent:
    """Abstract base class for all agents."""
    
    def __init__(self, name: str):
        self.name = name
        self.logger = get_logger(f"agent.{name}", Config.LOG_LEVEL)
    
    async def execute(self, user_message: str, conversation_context: Optional[str] = None) -> AgentOutput:
        """
        Execute the agent.
        
        Args:
            user_message: User query
            conversation_context: Optional conversation history context
        
        Returns:
            AgentOutput with answer, citations, etc.
        """
        raise NotImplementedError("Subclasses must implement execute()")
    
    def _log_execution(self, status: str, message: str):
        """Log agent execution."""
        self.logger.info(f"[{self.name}] {status}: {message}")
