"""Chat endpoints."""

from typing import Optional, List
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import uuid
import time
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
    # LangGraph execution metrics
    confidence: float = 0.8
    intent: str = "unknown"
    agents_used: List[str] = []
    execution_times: dict = {}
    total_time_ms: float = 0.0


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


class OrchestrationRequest(BaseModel):
    """Multi-agent orchestration request."""
    message: str
    session_id: Optional[str] = None
    conversation_history: Optional[List[ChatMessage]] = None


@router.post("/chat/orchestration")
async def orchestration_chat(request: OrchestrationRequest) -> ChatResponse:
    """
    Multi-agent orchestration endpoint with LangGraph integration.
    
    Uses LangGraph StateGraph for robust multi-agent coordination.
    Returns execution metrics for frontend display.
    """
    from src.orchestration.langgraph_workflow import get_langgraph_orchestrator
    
    try:
        session_id = request.session_id or str(uuid.uuid4())
        start_time = time.time()
        
        # Extract conversation context if provided
        context = None
        if request.conversation_history:
            context = "\n".join([f"{msg.role}: {msg.content}" for msg in request.conversation_history])
        
        # Try to use LangGraph orchestrator first
        try:
            orchestrator = get_langgraph_orchestrator()
            
            # Execute with LangGraph (now using ainvoke for async)
            result = await orchestrator.execute(
                user_input=request.message,
                session_id=session_id,
                conversation_history=request.conversation_history or [],
            )
            
            # Extract execution metrics from LangGraph result
            message = result.get("response", "")
            intent = result.get("intent", "unknown")
            confidence = result.get("confidence", 0.8)
            agents_used = result.get("agents_used", [])
            execution_times = result.get("execution_times", {})
            citations = result.get("citations", [])
            
            # Format citations if available
            if citations and not isinstance(citations[0], Citation):
                citations = [
                    Citation(
                        title=c.get("title", "") if isinstance(c, dict) else str(c),
                        source_url=c.get("source_url", "") if isinstance(c, dict) else "",
                        category=c.get("category", "") if isinstance(c, dict) else ""
                    )
                    for c in citations
                ]
            
            metadata = {
                "agent": "langgraph_orchestrator",
                "tools_used": result.get("metadata", {}).get("tools_used", []),
                "workflow_state": "complete",
            }
            
            logger.info(f"[{session_id}] LangGraph orchestrator executed successfully | Agents: {agents_used}")
            
        except Exception as lg_error:
            # Fallback to FinanceQAAgent if LangGraph fails
            logger.warning(f"LangGraph orchestrator failed, falling back to FinanceQA: {str(lg_error)}")
            
            agent = FinanceQAAgent()
            output = await agent.execute(
                user_message=request.message,
                conversation_context=context,
            )
            
            message = output.answer_text
            intent = "finance_qa"
            confidence = 0.85
            agents_used = ["finance_qa"]
            execution_times = {"finance_qa": (time.time() - start_time) * 1000}
            
            # Format citations
            citations = [
                Citation(
                    title=c["title"],
                    source_url=c["source_url"],
                    category=c["category"]
                )
                for c in output.citations
            ]
            
            metadata = {
                "agent": "finance_qa",
                "tools_used": output.tool_calls_made,
                "chunks_retrieved": output.structured_data.get("chunks_retrieved", 0) if output.structured_data else 0,
            }
        
        # Calculate total execution time
        total_time_ms = (time.time() - start_time) * 1000
        
        response = ChatResponse(
            session_id=session_id,
            message=message,
            citations=citations,
            timestamp=datetime.utcnow().isoformat(),
            metadata=metadata,
            confidence=confidence,
            intent=intent,
            agents_used=agents_used,
            execution_times=execution_times,
            total_time_ms=total_time_ms,
        )
        
        logger.info(f"[{session_id}] Orchestration chat response generated | Agents: {agents_used} | Time: {total_time_ms:.0f}ms")
        return response
        
        
    except Exception as e:
        logger.error(f"Orchestration chat endpoint error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
