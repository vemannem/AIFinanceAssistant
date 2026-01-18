"""Agent-specific endpoints for portfolio, market, goals, etc."""

from typing import Optional, List, Dict, Any
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import uuid
import time
from datetime import datetime
from src.agents.portfolio_analysis import PortfolioAnalysisAgent
from src.agents.market_analysis import MarketAnalysisAgent
from src.agents.goal_planning import GoalPlanningAgent
from src.agents.tax_education import TaxEducationAgent
from src.agents.news_synthesizer import NewsSynthesizerAgent
from src.core.logger import get_logger
from src.core.config import Config
from src.orchestration.langgraph_workflow import get_langgraph_orchestrator

logger = get_logger(__name__, Config.LOG_LEVEL)
router = APIRouter()


class Citation(BaseModel):
    """Citation."""
    title: str
    source_url: str
    category: str


class AgentResponse(BaseModel):
    """Generic agent response."""
    session_id: str
    message: str
    citations: List[Citation]
    structured_data: Optional[Dict[str, Any]] = None
    timestamp: str
    metadata: dict
    # LangGraph execution metrics (for frontend StateGraph display)
    confidence: float = 0.8
    intent: str = "unknown"
    agents_used: List[str] = []
    execution_times: dict = {}
    total_time_ms: float = 0.0


# ============================================================================
# PORTFOLIO ANALYSIS ENDPOINT
# ============================================================================

class Holding(BaseModel):
    """Portfolio holding."""
    ticker: str
    quantity: float
    current_price: float
    cost_basis: Optional[float] = None


class PortfolioAnalysisRequest(BaseModel):
    """Portfolio analysis request."""
    holdings: List[Holding]
    session_id: Optional[str] = None
    analysis_type: Optional[str] = "full"  # allocation, diversification, rebalance, full


@router.post("/agents/portfolio-analysis")
async def analyze_portfolio(request: PortfolioAnalysisRequest) -> AgentResponse:
    """
    Analyze investment portfolio via LangGraph orchestrator.
    
    Routes to portfolio analysis agent through LangGraph StateGraph.
    Returns allocation, diversification, risk assessment, and recommendations.
    """
    try:
        session_id = request.session_id or str(uuid.uuid4())
        start_time = time.time()
        
        # Create user message with portfolio context
        holdings_summary = ", ".join([f"{h.ticker} ({h.quantity} shares @ ${h.current_price})" for h in request.holdings])
        user_message = f"Analyze portfolio: {holdings_summary}. Analysis type: {request.analysis_type or 'full'}"
        
        # Route through LangGraph orchestrator
        try:
            orchestrator = get_langgraph_orchestrator()
            result = await orchestrator.execute(
                user_input=user_message,
                session_id=session_id,
                conversation_history=[],
            )
            
            message = result.get("response", "")
            agents_used = result.get("agents_used", ["portfolio_analysis"])
            
        except Exception as lg_error:
            logger.warning(f"LangGraph failed, falling back to direct agent: {str(lg_error)}")
            
            # Fallback to direct agent
            holdings_data = {
                "holdings": [
                    {
                        "ticker": h.ticker,
                        "quantity": h.quantity,
                        "current_price": h.current_price,
                    }
                    for h in request.holdings
                ],
                "analysis_type": request.analysis_type or "full"
            }
            
            agent = PortfolioAnalysisAgent()
            output = await agent.execute(
                user_message="Analyze my portfolio",
                holdings_data=holdings_data
            )
            
            message = output.answer_text
            agents_used = ["portfolio_analysis"]
        
        # Calculate execution time
        total_time_ms = (time.time() - start_time) * 1000
        
        # Format response with execution metrics
        response = AgentResponse(
            session_id=session_id,
            message=message,
            citations=[],
            structured_data={
                "agents_used": agents_used,
                "execution_time_ms": total_time_ms,
                "analysis_type": request.analysis_type or "full"
            },
            timestamp=datetime.utcnow().isoformat(),
            metadata={
                "agent": "portfolio_analysis",
                "agents_used": agents_used,
                "route": "langgraph_orchestrator"
            }
        )
        
        logger.info(f"[{session_id}] Portfolio analysis | Agents: {agents_used} | Time: {total_time_ms:.0f}ms")
        return response
        
    except Exception as e:
        logger.error(f"Portfolio analysis error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# MARKET ANALYSIS ENDPOINT
# ============================================================================

class MarketAnalysisRequest(BaseModel):
    """Market analysis request."""
    tickers: List[str]
    session_id: Optional[str] = None
    analysis_type: Optional[str] = "quote"  # quote, historical, fundamentals, comparison


@router.post("/agents/market-analysis")
async def analyze_market(request: MarketAnalysisRequest) -> AgentResponse:
    """
    Analyze market data and stock quotes via LangGraph orchestrator.
    
    Routes to market analysis agent through LangGraph StateGraph.
    Returns quotes, trends, fundamentals, and comparisons.
    """
    try:
        session_id = request.session_id or str(uuid.uuid4())
        start_time = time.time()
        
        # Create user message with market analysis context
        user_message = f"Analyze market data for {', '.join(request.tickers)}. Analysis type: {request.analysis_type or 'quote'}"
        
        # Route through LangGraph orchestrator
        try:
            orchestrator = get_langgraph_orchestrator()
            result = await orchestrator.execute(
                user_input=user_message,
                session_id=session_id,
                conversation_history=[],
            )
            
            message = result.get("response", "")
            agents_used = result.get("agents_used", ["market_analysis"])
            
        except Exception as lg_error:
            logger.warning(f"LangGraph failed, falling back to direct agent: {str(lg_error)}")
            
            # Fallback to direct agent
            query_data = {
                "tickers": request.tickers,
                "analysis_type": request.analysis_type or "quote"
            }
            
            agent = MarketAnalysisAgent()
            output = await agent.execute(
                user_message=f"Analyze {', '.join(request.tickers)}",
                query_data=query_data
            )
            
            message = output.answer_text
            agents_used = ["market_analysis"]
        
        # Calculate execution time
        total_time_ms = (time.time() - start_time) * 1000
        
        # Format response with execution metrics
        response = AgentResponse(
            session_id=session_id,
            message=message,
            citations=[],
            structured_data={
                "agents_used": agents_used,
                "execution_time_ms": total_time_ms,
                "tickers": request.tickers,
                "analysis_type": request.analysis_type or "quote"
            },
            timestamp=datetime.utcnow().isoformat(),
            metadata={
                "agent": "market_analysis",
                "agents_used": agents_used,
                "route": "langgraph_orchestrator"
            }
        )
        
        logger.info(f"[{session_id}] Market analysis | Agents: {agents_used} | Time: {total_time_ms:.0f}ms")
        return response
        
    except Exception as e:
        logger.error(f"Market analysis error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# GOAL PLANNING ENDPOINT
# ============================================================================

class GoalPlanningRequest(BaseModel):
    """Goal planning request."""
    current_value: float
    goal_amount: float
    time_horizon_years: float
    risk_appetite: Optional[str] = "moderate"  # low, moderate, high
    current_return: Optional[float] = 6.0
    session_id: Optional[str] = None


@router.post("/agents/goal-planning")
async def plan_goals(request: GoalPlanningRequest) -> AgentResponse:
    """
    Plan financial goals and projections via LangGraph orchestrator.
    
    Routes to goal planning agent through LangGraph StateGraph.
    Returns monthly savings needed, timelines, and allocation recommendations.
    """
    try:
        session_id = request.session_id or str(uuid.uuid4())
        start_time = time.time()
        
        # Create user message with goal planning context
        user_message = f"Plan financial goal: ${request.current_value} → ${request.goal_amount} in {request.time_horizon_years} years. Risk appetite: {request.risk_appetite}"
        
        # Route through LangGraph orchestrator
        try:
            orchestrator = get_langgraph_orchestrator()
            result = await orchestrator.execute(
                user_input=user_message,
                session_id=session_id,
                conversation_history=[],
            )
            
            message = result.get("response", "")
            agents_used = result.get("agents_used", ["goal_planning"])
            
        except Exception as lg_error:
            logger.warning(f"LangGraph failed, falling back to direct agent: {str(lg_error)}")
            
            # Fallback to direct agent
            goal_data = {
                "current_value": request.current_value,
                "goal_amount": request.goal_amount,
                "time_horizon_years": request.time_horizon_years,
                "risk_appetite": request.risk_appetite,
                "current_return": request.current_return,
            }
            
            agent = GoalPlanningAgent()
            output = await agent.execute(
                user_message="Plan my financial goal",
                goal_data=goal_data
            )
            
            message = output.answer_text
            agents_used = ["goal_planning"]
        
        # Calculate execution time
        total_time_ms = (time.time() - start_time) * 1000
        
        # Format response with execution metrics
        response = AgentResponse(
            session_id=session_id,
            message=message,
            citations=[],
            structured_data={
                "agents_used": agents_used,
                "execution_time_ms": total_time_ms,
                "goal_amount": request.goal_amount,
                "time_horizon_years": request.time_horizon_years
            },
            timestamp=datetime.utcnow().isoformat(),
            metadata={
                "agent": "goal_planning",
                "agents_used": agents_used,
                "route": "langgraph_orchestrator"
            },
            confidence=result.get("confidence", 0.8) if agents_used != ["goal_planning"] else 0.8,
            intent=result.get("intent", "goal_planning") if agents_used != ["goal_planning"] else "goal_planning",
            agents_used=agents_used,
            execution_times=result.get("execution_times", {}) if agents_used != ["goal_planning"] else {},
            total_time_ms=total_time_ms
        )
        
        logger.info(f"[{session_id}] Goal planning | Agents: {agents_used} | Time: {total_time_ms:.0f}ms")
        return response
        
    except Exception as e:
        logger.error(f"Goal planning error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# TAX EDUCATION ENDPOINT
# ============================================================================

class TaxEducationRequest(BaseModel):
    """Tax education request."""
    question: str
    session_id: Optional[str] = None
    category_filter: Optional[str] = None


@router.post("/agents/tax-education")
async def answer_tax_question(request: TaxEducationRequest) -> AgentResponse:
    """
    Answer tax-related questions using RAG.
    
    Returns tax strategies, education, and disclaimers.
    """
    try:
        session_id = request.session_id or str(uuid.uuid4())
        
        start_time = time.time()
        
        # Create user message with tax education context
        user_message = f"Answer tax question: {request.question}"
        if request.category_filter:
            user_message += f" (Focus: {request.category_filter})"
        
        # Route through LangGraph orchestrator
        try:
            orchestrator = get_langgraph_orchestrator()
            result = await orchestrator.execute(
                user_input=user_message,
                session_id=session_id,
                conversation_history=[],
            )
            
            message = result.get("response", "")
            agents_used = result.get("agents_used", ["tax_education"])
            
        except Exception as lg_error:
            logger.warning(f"LangGraph failed, falling back to direct agent: {str(lg_error)}")
            
            # Fallback to direct agent
            agent = TaxEducationAgent()
            output = await agent.execute(
                user_message=request.question,
                category_filter=request.category_filter
            )
            
            message = output.answer_text
            agents_used = ["tax_education"]
        
        # Calculate execution time
        total_time_ms = (time.time() - start_time) * 1000
        
        # Format response with execution metrics
        response = AgentResponse(
            session_id=session_id,
            message=message,
            citations=[],
            structured_data={
                "agents_used": agents_used,
                "execution_time_ms": total_time_ms,
            },
            timestamp=datetime.utcnow().isoformat(),
            metadata={
                "agent": "tax_education",
                "agents_used": agents_used,
                "route": "langgraph_orchestrator"
            },
            confidence=result.get("confidence", 0.8) if agents_used != ["tax_education"] else 0.8,
            intent=result.get("intent", "tax_question") if agents_used != ["tax_education"] else "tax_question",
            agents_used=agents_used,
            execution_times=result.get("execution_times", {}) if agents_used != ["tax_education"] else {},
            total_time_ms=total_time_ms
        )
        
        logger.info(f"[{session_id}] Tax education | Agents: {agents_used} | Time: {total_time_ms:.0f}ms")
        return response
        
    except Exception as e:
        logger.error(f"Tax education error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# NEWS SYNTHESIS ENDPOINT
# ============================================================================

class NewsSynthesisRequest(BaseModel):
    """News synthesis request."""
    tickers: Optional[List[str]] = None
    sentiment_focus: Optional[str] = None
    session_id: Optional[str] = None


@router.post("/agents/news-synthesis")
async def synthesize_news(request: NewsSynthesisRequest) -> AgentResponse:
    """
    Synthesize market news and sentiment.
    
    Returns news summaries, sentiment analysis, and market movement interpretation.
    """
    try:
        session_id = request.session_id or str(uuid.uuid4())
        
        start_time = time.time()
        
        # Create user message with news synthesis context
        tickers_str = ", ".join(request.tickers) if request.tickers else "all watchlist"
        user_message = f"Synthesize market news for {tickers_str}"
        if request.sentiment_focus:
            user_message += f" (Sentiment focus: {request.sentiment_focus})"
        
        # Route through LangGraph orchestrator
        try:
            orchestrator = get_langgraph_orchestrator()
            result = await orchestrator.execute(
                user_input=user_message,
                session_id=session_id,
                conversation_history=[],
            )
            
            message = result.get("response", "")
            agents_used = result.get("agents_used", ["news_synthesizer"])
            
        except Exception as lg_error:
            logger.warning(f"LangGraph failed, falling back to direct agent: {str(lg_error)}")
            
            # Fallback to direct agent
            news_data = {
                "tickers": request.tickers or [],
                "sentiment_focus": request.sentiment_focus,
            }
            
            agent = NewsSynthesizerAgent()
            output = await agent.execute(
                user_message="Synthesize market news",
                news_data=news_data
            )
            
            message = output.answer_text
            agents_used = ["news_synthesizer"]
        
        # Calculate execution time
        total_time_ms = (time.time() - start_time) * 1000
        
        # Format response with execution metrics
        response = AgentResponse(
            session_id=session_id,
            message=message,
            citations=[],
            structured_data={
                "agents_used": agents_used,
                "execution_time_ms": total_time_ms,
                "tickers_analyzed": request.tickers or [],
            },
            timestamp=datetime.utcnow().isoformat(),
            metadata={
                "agent": "news_synthesizer",
                "agents_used": agents_used,
                "route": "langgraph_orchestrator"
            },
            confidence=result.get("confidence", 0.8) if agents_used != ["news_synthesizer"] else 0.8,
            intent=result.get("intent", "news_analysis") if agents_used != ["news_synthesizer"] else "news_analysis",
            agents_used=agents_used,
            execution_times=result.get("execution_times", {}) if agents_used != ["news_synthesizer"] else {},
            total_time_ms=total_time_ms
        )
        
        logger.info(f"[{session_id}] News synthesis | Agents: {agents_used} | Time: {total_time_ms:.0f}ms")
        return response
        
    except Exception as e:
        logger.error(f"News synthesis error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
