"""LLM provider abstraction (OpenAI and Anthropic wrapper)."""

from typing import Optional, List, Dict, Any
import openai
from src.core.config import Config
from src.core.logger import get_logger
from src.core import LLMError

logger = get_logger(__name__, Config.LOG_LEVEL)

# Optional anthropic import
try:
    import anthropic
    HAS_ANTHROPIC = True
except ImportError:
    HAS_ANTHROPIC = False


class LLMProvider:
    """Wrapper around LLM APIs (OpenAI or Anthropic)."""
    
    def __init__(self):
        self.provider = Config.LLM_PROVIDER
        
        if self.provider == "anthropic":
            if not HAS_ANTHROPIC:
                logger.warning("Anthropic not installed, falling back to OpenAI")
                self.provider = "openai"
            else:
                self.client = anthropic.Anthropic(api_key=Config.ANTHROPIC_API_KEY)
                self.model = Config.ANTHROPIC_MODEL
                self.temperature = Config.ANTHROPIC_TEMPERATURE
                self.max_tokens = Config.ANTHROPIC_MAX_TOKENS
        
        if self.provider == "openai":
            self.client = openai.OpenAI(api_key=Config.OPENAI_API_KEY)
            self.model = Config.OPENAI_MODEL
            self.temperature = Config.OPENAI_TEMPERATURE
            self.max_tokens = Config.OPENAI_MAX_TOKENS
    
    async def generate(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> str:
        """
        Generate text response from LLM (OpenAI or Anthropic).
        
        Args:
            messages: List of dicts with 'role' and 'content'
            temperature: Override temperature
            max_tokens: Override max_tokens
        
        Returns:
            Generated text response
        """
        try:
            if self.provider == "anthropic":
                response = self.client.messages.create(
                    model=self.model,
                    messages=messages,
                    temperature=temperature or self.temperature,
                    max_tokens=max_tokens or self.max_tokens,
                )
                return response.content[0].text
            else:  # openai
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=temperature or self.temperature,
                    max_tokens=max_tokens or self.max_tokens,
                )
                return response.choices[0].message.content
        except Exception as e:
            logger.error(f"LLM generation failed: {str(e)}")
            raise LLMError(f"Failed to generate response: {str(e)}")
    
    async def embed(self, texts: List[str]) -> List[List[float]]:
        """
        Embed texts using OpenAI.
        
        Args:
            texts: List of strings to embed
        
        Returns:
            List of embedding vectors
        """
        try:
            response = self.client.embeddings.create(
                model=Config.OPENAI_EMBEDDING_MODEL,
                input=texts,
                encoding_format="float"
            )
            return [item.embedding for item in response.data]
        except Exception as e:
            logger.error(f"Embedding failed: {str(e)}")
            raise LLMError(f"Failed to embed text: {str(e)}")


# Singleton instance
_llm_provider = None


def get_llm_provider() -> LLMProvider:
    """Get singleton LLM provider instance."""
    global _llm_provider
    if _llm_provider is None:
        _llm_provider = LLMProvider()
    return _llm_provider
