"""
Conversation Management - Max history and rolling summary

Handles:
- Keeping conversation history within max size
- Creating rolling summaries when history exceeds threshold
- Extracting key context for prompt injection
"""

from typing import List, Optional, Dict, Any
from dataclasses import dataclass
from src.core.config import Config
from src.core.logger import get_logger
import json

logger = get_logger(__name__, Config.LOG_LEVEL)


@dataclass
class ConversationSummary:
    """Summary of conversation history"""
    summary_text: str
    messages_included: int
    key_topics: List[str]
    key_decisions: List[str]
    timestamp: str


class ConversationManager:
    """Manages conversation history with max size and rolling summaries"""
    
    def __init__(self, max_history: int = None, summary_threshold: int = None, summary_length: int = None):
        """
        Initialize conversation manager
        
        Args:
            max_history: Maximum messages to keep (default from config)
            summary_threshold: When to trigger summary (e.g., 10 messages)
            summary_length: Target length for summary in tokens (approx 3-4 chars per token)
        """
        self.max_history = max_history or Config.CONVERSATION_MAX_HISTORY
        self.summary_threshold = summary_threshold or Config.CONVERSATION_SUMMARY_THRESHOLD
        self.summary_length = summary_length or Config.CONVERSATION_SUMMARY_LENGTH
    
    def should_create_summary(self, num_messages: int) -> bool:
        """Check if conversation needs summary (exceeded threshold)"""
        return num_messages >= self.summary_threshold
    
    def create_summary(self, messages: List[Dict[str, str]]) -> ConversationSummary:
        """
        Create a summary of conversation messages
        
        Args:
            messages: List of message dicts with 'role' and 'content'
        
        Returns:
            ConversationSummary with summary text and metadata
        
        Logic:
        - Extract key financial topics mentioned
        - Extract key decisions/questions asked
        - Create brief narrative summary
        - Limit to summary_length characters (~500 chars = ~150 tokens)
        """
        
        from datetime import datetime
        
        if not messages:
            return ConversationSummary(
                summary_text="No conversation history",
                messages_included=0,
                key_topics=[],
                key_decisions=[],
                timestamp=datetime.now().isoformat()
            )
        
        # Extract key topics and decisions from user messages
        topics = set()
        decisions = []
        
        financial_keywords = {
            'portfolio': 'Portfolio Analysis',
            'stock': 'Stock Market',
            'bond': 'Bonds',
            'etf': 'ETFs',
            'diversification': 'Diversification',
            'rebalance': 'Rebalancing',
            'goal': 'Financial Goals',
            'retirement': 'Retirement Planning',
            'tax': 'Tax Planning',
            'risk': 'Risk Management',
            'allocation': 'Asset Allocation',
            'dividend': 'Dividends',
            'yield': 'Yield Analysis',
            'market': 'Market Analysis',
        }
        
        for msg in messages:
            content = msg.get('content', '').lower()
            
            # Find topics mentioned
            for keyword, topic_name in financial_keywords.items():
                if keyword in content:
                    topics.add(topic_name)
            
            # Track user questions/decisions
            if msg.get('role') == 'user' and len(msg.get('content', '')) > 20:
                # Store first 100 chars of user messages as decisions
                decisions.append(msg['content'][:100])
        
        # Build summary narrative
        num_msgs = len(messages)
        summary_parts = [
            f"Conversation with {num_msgs} messages.",
        ]
        
        if topics:
            topics_str = ", ".join(sorted(topics)[:5])  # Top 5 topics
            summary_parts.append(f"Main topics: {topics_str}.")
        
        # Get most recent user question as context
        recent_user_msg = None
        for msg in reversed(messages):
            if msg.get('role') == 'user':
                recent_user_msg = msg.get('content', '')[:150]
                break
        
        if recent_user_msg:
            summary_parts.append(f"Last question: {recent_user_msg}")
        
        summary_text = " ".join(summary_parts)
        
        # Truncate to summary_length if needed
        if len(summary_text) > self.summary_length:
            summary_text = summary_text[:self.summary_length] + "..."
        
        return ConversationSummary(
            summary_text=summary_text,
            messages_included=num_msgs,
            key_topics=list(topics)[:5],
            key_decisions=decisions[:3],
            timestamp=datetime.now().isoformat()
        )
    
    def trim_history(self, messages: List[Dict[str, str]]) -> tuple[List[Dict[str, str]], Optional[ConversationSummary]]:
        """
        Trim conversation history to max_history size
        
        Args:
            messages: Full conversation history
        
        Returns:
            (trimmed_messages, summary_if_created)
        
        Process:
        1. If messages <= max_history: return as-is
        2. If messages > max_history:
           a. Create summary of oldest messages
           b. Keep only last max_history messages
           c. Return trimmed messages + summary
        """
        
        if len(messages) <= self.max_history:
            return messages, None
        
        # Create summary before trimming
        summary = self.create_summary(messages[: len(messages) - self.max_history])
        
        # Keep only last max_history messages
        trimmed = messages[-self.max_history:]
        
        logger.info(
            f"Trimmed conversation history",
            extra={
                "original_count": len(messages),
                "trimmed_count": len(trimmed),
                "summary_created": True,
                "topics": summary.key_topics
            }
        )
        
        return trimmed, summary
    
    def apply_summary_to_prompt(
        self, 
        messages: List[Dict[str, str]], 
        summary: Optional[ConversationSummary]
    ) -> str:
        """
        Create a context string for LLM from messages and summary
        
        Format:
        ```
        [If summary exists]
        Previous conversation summary:
        {summary.summary_text}
        
        Recent messages:
        User: ...
        Assistant: ...
        
        [If no summary, just recent messages]
        ```
        
        Args:
            messages: Conversation history (should already be trimmed)
            summary: Optional summary of earlier messages
        
        Returns:
            Formatted context string for prompt
        """
        
        context_parts = []
        
        # Add summary if exists
        if summary:
            context_parts.append(f"Previous conversation summary:\n{summary.summary_text}\n")
            if summary.key_topics:
                topics_str = ", ".join(summary.key_topics)
                context_parts.append(f"Topics discussed: {topics_str}\n")
        
        # Add recent messages
        if messages:
            context_parts.append("Recent conversation:")
            for msg in messages[-5:]:  # Last 5 messages for brevity
                role = msg.get('role', 'unknown').capitalize()
                content = msg.get('content', '')[:200]  # Truncate long messages
                context_parts.append(f"{role}: {content}")
        
        return "\n".join(context_parts)
    
    def get_stats(self, messages: List[Dict[str, str]]) -> Dict[str, Any]:
        """Get statistics about conversation history"""
        
        user_msgs = [m for m in messages if m.get('role') == 'user']
        assistant_msgs = [m for m in messages if m.get('role') == 'assistant']
        
        total_chars = sum(len(m.get('content', '')) for m in messages)
        
        return {
            "total_messages": len(messages),
            "user_messages": len(user_msgs),
            "assistant_messages": len(assistant_msgs),
            "total_characters": total_chars,
            "avg_message_length": total_chars // len(messages) if messages else 0,
            "needs_summary": self.should_create_summary(len(messages)),
            "max_history": self.max_history,
            "summary_threshold": self.summary_threshold,
        }


# Singleton instance
_conversation_manager = None


def get_conversation_manager() -> ConversationManager:
    """Get or create singleton conversation manager"""
    global _conversation_manager
    if _conversation_manager is None:
        _conversation_manager = ConversationManager()
    return _conversation_manager
