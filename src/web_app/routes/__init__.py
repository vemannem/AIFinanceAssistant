"""Chat endpoints."""

from typing import Optional, List
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import uuid
from datetime import datetime
from src.agents.finance_qa import FinanceQAAgent
from src.core.logger import get_logger
from src.core.config import Config

logger = get_logger(__name__, Config.LOG_LEVEL)
router = APIRouter()


class ChatMessage(BaseModel):
    """Chat message."""
    role: str  # "user" or "assistant"
    content: str


class ChatRequest(BaseModel):
    """Chat request."""
    message: str
    session_id: Optional[str] = None
    category_filter: Optional[str] = None
    conversation_history: Optional[List[ChatMessage]] = None


class Citation(BaseModel):
    """Citation."""
    title: str
    source_url: str
    category: str


class ChatResponse(BaseModel):
    """Chat response."""
    session_id: str
    message: str
    citations: List[Citation]
    timestamp: str
    metadata: dict


@router.post("/chat/finance-qa")
async def finance_qa_chat(request: ChatRequest) -> ChatResponse:
    """
    Finance Q&A endpoint.
    
    Uses RAG to answer financial education questions.
    """
    try:
        # Generate session ID if not provided
        session_id = request.session_id or str(uuid.uuid4())
        
        # Extract conversation context if provided
        context = None
        if request.conversation_history:
            context = "\n".join([f"{msg.role}: {msg.content}" for msg in request.conversation_history])
        
        # Execute agent
        agent = FinanceQAAgent()
        output = await agent.execute(
            user_message=request.message,
            conversation_context=context,
            category_filter=request.category_filter
        )
        
        # Format response
        citations = [
            Citation(
                title=c["title"],
                source_url=c["source_url"],
                category=c["category"]
            )
            for c in output.citations
        ]
        
        response = ChatResponse(
            session_id=session_id,
            message=output.answer_text,
            citations=citations,
            timestamp=datetime.utcnow().isoformat(),
            metadata={
                "agent": "finance_qa",
                "tools_used": output.tool_calls_made,
                "chunks_retrieved": output.structured_data.get("chunks_retrieved", 0) if output.structured_data else 0,
            }
        )
        
        logger.info(f"[{session_id}] Chat response generated with {len(citations)} citations")
        return response
        
    except Exception as e:
        logger.error(f"Chat endpoint error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
