"""Finance Q&A Agent - RAG-powered financial education."""

from typing import Optional
from src.agents import BaseAgent, AgentOutput
from src.rag import get_rag_retriever
from src.core.llm_provider import get_llm_provider
from src.core.config import Config
from src.core.logger import get_logger

logger = get_logger(__name__, Config.LOG_LEVEL)


class FinanceQAAgent(BaseAgent):
    """
    Answers financial education questions using RAG.
    Uses Pinecone to retrieve relevant articles and generates informed responses.
    """
    
    def __init__(self):
        super().__init__("finance_qa")
        self.retriever = get_rag_retriever()
        self.llm = get_llm_provider()
    
    async def execute(
        self,
        user_message: str,
        conversation_context: Optional[str] = None,
        category_filter: Optional[str] = None
    ) -> AgentOutput:
        """
        Answer a financial question using RAG.
        
        Args:
            user_message: User's question
            conversation_context: Optional context from conversation history
            category_filter: Optional category to filter articles
        
        Returns:
            AgentOutput with answer and citations
        """
        self._log_execution("START", f"Processing: {user_message[:50]}")
        
        try:
            # 1. Retrieve relevant articles from Pinecone
            chunks = await self.retriever.retrieve(
                query=user_message,
                category_filter=category_filter
            )
            self._log_execution("RETRIEVE", f"Found {len(chunks)} relevant chunks")
            
            # 2. Format chunks as context
            context = self._format_context(chunks)
            citations = self.retriever.format_citations(chunks)
            
            # 3. Generate answer using LLM
            answer = await self._generate_answer(user_message, context, conversation_context)
            self._log_execution("GENERATE", f"Generated {len(answer)} char response")
            
            # 4. Return structured output
            output = AgentOutput(
                answer_text=answer,
                citations=citations,
                tool_calls_made=["pinecone_retrieval", "openai_chat"],
                structured_data={"chunks_retrieved": len(chunks)}
            )
            
            self._log_execution("END", "Success")
            return output
            
        except Exception as e:
            self._log_execution("ERROR", str(e))
            # Fallback: answer without RAG
            answer = await self._generate_answer(user_message, "", conversation_context)
            return AgentOutput(
                answer_text=answer,
                citations=[],
                tool_calls_made=["openai_chat"],
                structured_data={"rag_failed": True}
            )
    
    async def _generate_answer(
        self,
        user_message: str,
        context: str,
        conversation_context: Optional[str] = None
    ) -> str:
        """Generate answer using LLM."""
        
        # Build system prompt
        system_prompt = """You are a knowledgeable financial education assistant. 
Your job is to answer questions about finance, investing, and personal finance topics.

You have access to a knowledge base of financial education articles.
Use the provided context to inform your answer, and cite sources when relevant.

Be accurate, educational, and always include appropriate disclaimers about financial advice.
Format your response clearly with bullet points or sections where appropriate."""
        
        # Add RAG context if available
        if context:
            system_prompt += f"\n\nKNOWLEDGE BASE:\n{context}"
        
        # Add conversation context if available
        conversation_msg = ""
        if conversation_context:
            conversation_msg = f"\n\nPrevious conversation context:\n{conversation_context}"
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"{user_message}{conversation_msg}"}
        ]
        
        answer = await self.llm.generate(messages)
        return answer
    
    def _format_context(self, chunks) -> str:
        """Format retrieved chunks as readable context."""
        if not chunks:
            return ""
        
        context_parts = []
        for i, chunk in enumerate(chunks, 1):
            metadata = chunk.get("metadata", {})
            title = metadata.get("article_title", "Unknown")
            category = metadata.get("category", "General")
            content = chunk.get("content", "")[:300]  # Limit length
            
            part = f"\n[Source {i}] {title} (Category: {category})\n{content}..."
            context_parts.append(part)
        
        return "\n".join(context_parts)


# Singleton instance
_finance_qa_agent: Optional[FinanceQAAgent] = None


def get_finance_qa_agent() -> FinanceQAAgent:
    """Get or create Finance Q&A Agent singleton"""
    global _finance_qa_agent
    if _finance_qa_agent is None:
        _finance_qa_agent = FinanceQAAgent()
    return _finance_qa_agent
