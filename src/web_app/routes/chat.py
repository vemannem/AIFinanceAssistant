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

# In-memory storage for conversation history (for MVP)
# In production, use database (PostgreSQL, MongoDB, etc.)
CONVERSATION_HISTORY_STORE = {}


class ChatMessage(BaseModel):
    """Chat message."""
    role: str  # "user" or "assistant"
    content: str


class ConversationEntry(BaseModel):
    """Single conversation entry in history."""
    sessionId: str
    summary: str
    messageCount: int
    timestamp: str
    tags: List[str] = []
    messages: List[ChatMessage] = []


class ConversationHistoryResponse(BaseModel):
    """Response containing all conversations for a session."""
    sessions: List[ConversationEntry]
    total_count: int


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
                # Include execution details
                "execution_details": result.get("execution_details", []),
                "workflow_analysis": result.get("workflow_state", {}),
                "detected_intents": result.get("workflow_state", {}).get("detected_intents", []),
                "extracted_tickers": result.get("workflow_state", {}).get("extracted_tickers", []),
                "execution_errors": result.get("workflow_state", {}).get("execution_errors", []),
            }
            
            logger.info(f"[{session_id}] LangGraph orchestrator executed successfully | Agents: {agents_used}")
            logger.info(f"[{session_id}] Metadata execution_details: {metadata.get('execution_details', [])}")
            logger.info(f"[{session_id}] Metadata workflow_analysis: {metadata.get('workflow_analysis', {})}")
            
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
        
        logger.info(f"[{session_id}] Building ChatResponse with metadata keys: {list(metadata.keys())}")
        logger.info(f"[{session_id}] Metadata execution_details: {metadata.get('execution_details', 'NOT FOUND')}")
        
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
        logger.info(f"[{session_id}] Response metadata in ChatResponse: {response.metadata}")
        return response
        
        
    except Exception as e:
        logger.error(f"Orchestration chat endpoint error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# ===== CONVERSATION HISTORY ENDPOINTS =====

@router.post("/chat/history/save")
async def save_conversation(conversation: ConversationEntry) -> dict:
    """
    Save a conversation to history.
    
    Stores chat conversation for later retrieval.
    """
    try:
        session_id = conversation.sessionId
        
        # Store in-memory (production: save to database)
        if session_id not in CONVERSATION_HISTORY_STORE:
            CONVERSATION_HISTORY_STORE[session_id] = []
        
        CONVERSATION_HISTORY_STORE[session_id].append(conversation.dict())
        
        logger.info(f"Saved conversation {session_id} with {conversation.messageCount} messages")
        
        return {
            "status": "success",
            "session_id": session_id,
            "message": "Conversation saved"
        }
    except Exception as e:
        logger.error(f"Error saving conversation: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/chat/history")
async def get_conversation_history(limit: int = 50) -> ConversationHistoryResponse:
    """
    Get all saved conversations.
    
    Retrieves conversation history for the current user.
    """
    try:
        all_conversations = []
        
        # Flatten history store (in-memory for MVP)
        for session_id, conversations in CONVERSATION_HISTORY_STORE.items():
            all_conversations.extend(conversations)
        
        # Sort by timestamp (newest first) and limit
        sorted_conversations = sorted(
            all_conversations,
            key=lambda x: x.get("timestamp", ""),
            reverse=True
        )[:limit]
        
        # Convert to ConversationEntry objects
        entries = [ConversationEntry(**conv) for conv in sorted_conversations]
        
        logger.info(f"Retrieved {len(entries)} conversations from history")
        
        return ConversationHistoryResponse(
            sessions=entries,
            total_count=len(all_conversations)
        )
    except Exception as e:
        logger.error(f"Error retrieving conversation history: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/chat/history/{session_id}")
async def get_session_conversations(session_id: str) -> ConversationHistoryResponse:
    """
    Get conversations for a specific session.
    """
    try:
        conversations = CONVERSATION_HISTORY_STORE.get(session_id, [])
        
        entries = [ConversationEntry(**conv) for conv in conversations]
        
        logger.info(f"Retrieved {len(entries)} conversations for session {session_id}")
        
        return ConversationHistoryResponse(
            sessions=entries,
            total_count=len(entries)
        )
    except Exception as e:
        logger.error(f"Error retrieving session history: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/chat/history/{session_id}")
async def delete_session_history(session_id: str) -> dict:
    """
    Delete all conversations for a session.
    """
    try:
        if session_id in CONVERSATION_HISTORY_STORE:
            count = len(CONVERSATION_HISTORY_STORE[session_id])
            del CONVERSATION_HISTORY_STORE[session_id]
            logger.info(f"Deleted {count} conversations for session {session_id}")
            return {
                "status": "success",
                "session_id": session_id,
                "deleted_count": count
            }
        else:
            return {
                "status": "success",
                "session_id": session_id,
                "deleted_count": 0,
                "message": "Session not found"
            }
    except Exception as e:
        logger.error(f"Error deleting session history: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))