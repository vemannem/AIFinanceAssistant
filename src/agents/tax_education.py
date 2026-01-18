"""
Tax Education Agent - Answers tax-related questions using RAG

This agent provides tax education using the knowledge base, focused on
investment-related tax topics like capital gains, retirement accounts, etc.
"""

from typing import Optional, Dict, Any, List

from src.agents import BaseAgent, AgentOutput
from src.rag import RAGRetriever
from src.core.llm_provider import get_llm_provider
from src.core.logger import get_logger

logger = get_logger(__name__)

# Tax-specific keywords for filtering
TAX_KEYWORDS = {
    "capital_gains", "capital gains", "short-term", "long-term",
    "tax loss", "harvesting", "401k", "401(k)", "ira", "roth",
    "traditional ira", "roth ira", "tax deduction", "deductible",
    "capital loss", "wash sale", "quarterly estimated",
    "estimated tax", "dividend tax", "qualified dividend",
    "unqualified dividend", "marginal tax", "tax bracket",
    "alternative minimum tax", "amt", "nqdc", "nso", "stock option",
    "tax planning", "tax strategy", "tax-advantaged"
}


class TaxEducationAgent(BaseAgent):
    """
    Provides tax education and information using RAG.
    
    Specializes in investment tax topics like:
    - Capital gains and losses
    - Retirement account types and rules
    - Tax-advantaged strategies
    - Tax deductions and credits
    - Quarterly estimated taxes
    """

    def __init__(self):
        """Initialize Tax Education Agent"""
        super().__init__("tax_education")
        self.rag_retriever = RAGRetriever()
        self.llm_provider = get_llm_provider()

    async def execute(
        self,
        user_message: str,
        tax_data: Optional[Dict[str, Any]] = None
    ) -> AgentOutput:
        """
        Execute tax education query
        
        Args:
            user_message: User's tax-related question
            tax_data: Optional dict with:
                - category_filter: Optional[str] (focus area)
                - context: Optional[str] (additional context)
        
        Returns:
            AgentOutput with answer, citations, and educational content
        """
        self._log_execution("START", f"tax_education - {user_message[:50]}")

        try:
            # Parse tax data
            if not tax_data:
                tax_data = {}

            category_filter = tax_data.get("category_filter", "tax")
            context = tax_data.get("context", "")

            # Retrieve relevant articles from knowledge base
            retrieved_chunks = await self.rag_retriever.retrieve(
                query=user_message,
                top_k=5
            )

            # Extract citations
            citations = self._extract_citations(retrieved_chunks)

            # Build context for LLM
            context_text = self._format_context(retrieved_chunks)

            # Generate answer using LLM
            system_prompt = self._get_system_prompt()
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"{user_message}\n\n{context_text}"}
            ]
            answer = await self.llm_provider.generate(messages=messages)

            self._log_execution(
                "SUCCESS",
                f"tax_education - Generated answer with {len(citations)} citations"
            )

            return AgentOutput(
                answer_text=answer,
                structured_data={
                    "chunks_retrieved": len(retrieved_chunks),
                    "citations_count": len(citations),
                    "category": category_filter
                },
                citations=citations,
                tool_calls_made=["pinecone_retrieval", "openai_chat"]
            )

        except Exception as e:
            self._log_execution("ERROR", f"tax_education error: {str(e)}")
            return AgentOutput(
                answer_text=f"Error in tax education: {str(e)}",
                structured_data={},
                citations=[],
                tool_calls_made=[]
            )

    def _get_system_prompt(self) -> str:
        """Get system prompt for tax education"""
        return """You are a tax education specialist with expertise in investment taxation.

Your role is to:
1. Explain tax concepts clearly and accurately
2. Discuss capital gains, losses, and tax reporting
3. Explain retirement accounts (401k, IRA, Roth)
4. Discuss tax-advantaged investment strategies
5. Provide tax timeline and deadline information

Guidelines:
- Use retrieved articles to support your answers
- Break down complex concepts into understandable parts
- Provide specific examples when helpful
- Always include important disclaimers

IMPORTANT DISCLAIMERS:
- This is educational information, NOT tax advice
- Tax situations are complex and individual
- Strongly recommend consulting a CPA or tax professional
- Tax laws vary by location and change frequently
- Your specific situation may have unique tax implications

When answering:
1. Provide clear explanations
2. Give practical examples
3. Reference the educational materials
4. Include appropriate disclaimers
5. Suggest consulting a tax professional for personal situations"""

    def _format_context(self, chunks: List[Dict[str, Any]]) -> str:
        """Format retrieved chunks as context for LLM"""
        if not chunks:
            return "No relevant articles found in knowledge base."

        context_parts = ["### Educational Materials:\n"]
        for i, chunk in enumerate(chunks, 1):
            context_parts.append(
                f"\n**Source {i}:** {chunk.get('title', 'Unknown')}\n"
                f"{chunk.get('text', '')[:500]}...\n"
            )

        return "\n".join(context_parts)

    @staticmethod
    def _extract_citations(chunks: List[Dict[str, Any]]) -> List[Dict[str, str]]:
        """Extract citation information from chunks"""
        citations = []
        seen_urls = set()

        for chunk in chunks:
            url = chunk.get("source_url")
            if url and url not in seen_urls:
                citations.append({
                    "title": chunk.get("title", "Financial Education Article"),
                    "source_url": url,
                    "category": chunk.get("category", "tax")
                })
                seen_urls.add(url)

        return citations


# Singleton instance
_tax_education_agent: Optional[TaxEducationAgent] = None


def get_tax_education_agent() -> TaxEducationAgent:
    """Get or create Tax Education Agent singleton"""
    global _tax_education_agent
    if _tax_education_agent is None:
        _tax_education_agent = TaxEducationAgent()
    return _tax_education_agent
