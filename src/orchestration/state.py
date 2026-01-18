"""
Orchestration Module - State schema and types for LangGraph multi-agent system

Defines the state schema, message types, and data structures for
coordinating multiple financial agents.
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Literal
from enum import Enum
from datetime import datetime
from src.core.conversation_manager import ConversationSummary


class AgentType(str, Enum):
    """Enumeration of available agents"""
    FINANCE_QA = "finance_qa"
    PORTFOLIO_ANALYSIS = "portfolio_analysis"
    MARKET_ANALYSIS = "market_analysis"
    GOAL_PLANNING = "goal_planning"
    TAX_EDUCATION = "tax_education"
    NEWS_SYNTHESIZER = "news_synthesizer"


class Intent(str, Enum):
    """User intent classifications"""
    # Educational intents
    EDUCATION_QUESTION = "education_question"           # General finance education
    TAX_QUESTION = "tax_question"                       # Tax-specific questions
    
    # Analysis intents
    PORTFOLIO_ANALYSIS = "portfolio_analysis"           # Analyze current portfolio
    MARKET_ANALYSIS = "market_analysis"                 # Get market data/quotes
    NEWS_ANALYSIS = "news_analysis"                     # Market news & sentiment
    
    # Planning intents
    GOAL_PLANNING = "goal_planning"                     # Financial goal projection
    INVESTMENT_PLAN = "investment_plan"                # Multi-agent portfolio planning
    
    # Ambiguous/unknown
    UNKNOWN = "unknown"


@dataclass
class Message:
    """Message in conversation history"""
    role: Literal["user", "assistant"]
    content: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    agent: Optional[str] = None                         # Which agent generated (if assistant)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentExecution:
    """Record of a single agent execution"""
    agent_type: AgentType
    user_input: str
    output: Dict[str, Any]
    status: Literal["success", "error", "skipped"]
    execution_time_ms: float
    error: Optional[str] = None


@dataclass
class OrchestrationState:
    """
    State schema for LangGraph orchestration workflow
    
    Maintains complete context for multi-agent coordination:
    - User input and conversation history
    - Detected intents and routing decisions
    - Agent execution results
    - Final synthesized response
    """
    
    # ===== INPUT & CONTEXT =====
    user_input: str                              # Current user message
    conversation_history: List[Message] = field(default_factory=list)
    conversation_summary: Optional[ConversationSummary] = None  # Rolling summary of old messages
    session_id: str = field(default_factory=lambda: "default")
    
    # ===== INTENT & ROUTING =====
    detected_intents: List[Intent] = field(default_factory=list)
    primary_intent: Optional[Intent] = None
    confidence_score: float = 0.0                # Intent confidence (0-1)
    selected_agents: List[AgentType] = field(default_factory=list)
    routing_rationale: str = ""
    
    # ===== EXTRACTED DATA =====
    extracted_tickers: List[str] = field(default_factory=list)
    extracted_portfolio_data: Optional[Dict[str, Any]] = None
    extracted_goal_data: Optional[Dict[str, Any]] = None
    extracted_tax_context: Optional[str] = None
    market_context: Optional[str] = None
    
    # ===== AGENT EXECUTIONS =====
    agent_executions: List[AgentExecution] = field(default_factory=list)
    execution_times: Dict[str, float] = field(default_factory=dict)
    
    # ===== OUTPUTS =====
    agent_outputs: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    citations: List[Dict[str, str]] = field(default_factory=list)
    tool_calls_made: List[str] = field(default_factory=list)
    
    # ===== SYNTHESIS =====
    synthesized_response: str = ""
    response_structure: Dict[str, str] = field(default_factory=dict)  # Sections
    
    # ===== METADATA =====
    workflow_state: Literal["input", "intent_detection", "routing", "execution", "synthesis", "complete"] = "input"
    error_messages: List[str] = field(default_factory=list)
    debug_info: Dict[str, Any] = field(default_factory=dict)
    
    def add_error(self, error: str) -> None:
        """Add error message to state"""
        self.error_messages.append(error)
    
    def has_errors(self) -> bool:
        """Check if any errors occurred"""
        return len(self.error_messages) > 0
    
    def add_agent_execution(self, execution: AgentExecution) -> None:
        """Record agent execution"""
        self.agent_executions.append(execution)
        self.execution_times[execution.agent_type.value] = execution.execution_time_ms
    
    def get_execution_by_agent(self, agent_type: AgentType) -> Optional[AgentExecution]:
        """Get execution record for specific agent"""
        for exe in self.agent_executions:
            if exe.agent_type == agent_type:
                return exe
        return None
    
    def add_message(self, role: Literal["user", "assistant"], content: str, agent: Optional[str] = None) -> None:
        """Add message to conversation history"""
        self.conversation_history.append(Message(
            role=role,
            content=content,
            agent=agent
        ))
    
    def get_conversation_context(self) -> str:
        """
        Get conversation context for LLM prompts
        
        Includes conversation summary (if trimmed) + recent messages
        """
        from src.core.conversation_manager import get_conversation_manager
        
        manager = get_conversation_manager()
        
        # Convert messages to dicts for manager
        msg_dicts = [
            {"role": m.role, "content": m.content}
            for m in self.conversation_history
        ]
        
        # Get context with summary if needed
        context = manager.apply_summary_to_prompt(msg_dicts, self.conversation_summary)
        return context if context else ""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert state to dictionary for serialization"""
        return {
            "user_input": self.user_input,
            "session_id": self.session_id,
            "detected_intents": [i.value for i in self.detected_intents],
            "primary_intent": self.primary_intent.value if self.primary_intent else None,
            "confidence_score": self.confidence_score,
            "selected_agents": [a.value for a in self.selected_agents],
            "extracted_tickers": self.extracted_tickers,
            "agent_outputs": self.agent_outputs,
            "synthesized_response": self.synthesized_response,
            "workflow_state": self.workflow_state,
            "error_messages": self.error_messages
        }


@dataclass
class RouterDecision:
    """Decision output from intent detector/router"""
    intents: List[Intent]
    primary_intent: Intent
    agents: List[AgentType]
    confidence: float
    reasoning: str
    extracted_data: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SynthesisResult:
    """Result from response synthesizer"""
    final_response: str
    structure: Dict[str, str]
    key_insights: List[str]
    citations: List[Dict[str, str]]
    recommendations: List[str]


# Intent to Agent Mapping (priority order)
INTENT_TO_AGENTS = {
    Intent.EDUCATION_QUESTION: [AgentType.FINANCE_QA],
    Intent.TAX_QUESTION: [AgentType.TAX_EDUCATION],
    Intent.PORTFOLIO_ANALYSIS: [AgentType.PORTFOLIO_ANALYSIS],
    Intent.MARKET_ANALYSIS: [AgentType.MARKET_ANALYSIS],
    Intent.NEWS_ANALYSIS: [AgentType.NEWS_SYNTHESIZER],
    Intent.GOAL_PLANNING: [AgentType.GOAL_PLANNING],
    Intent.INVESTMENT_PLAN: [
        AgentType.PORTFOLIO_ANALYSIS,
        AgentType.GOAL_PLANNING,
        AgentType.TAX_EDUCATION
    ],
    Intent.UNKNOWN: [AgentType.FINANCE_QA],  # Fallback to Q&A
}

# Keywords for intent detection
INTENT_KEYWORDS = {
    Intent.EDUCATION_QUESTION: [
        "what is", "how does", "explain", "define", "understand",
        "tell me about", "describe", "difference between", "concept",
        "meaning of", "why is"
    ],
    Intent.TAX_QUESTION: [
        "tax", "capital gains", "ira", "401k", "roth",
        "deductible", "harvesting", "dividend tax", "tax strategy",
        "tax loss", "tax efficient"
    ],
    Intent.PORTFOLIO_ANALYSIS: [
        "analyze portfolio", "portfolio allocation", "diversification",
        "my holdings", "my portfolio", "concentration", "rebalance", "position",
        "allocation percentage", "analyze", "my stocks", "my shares"
    ],
    Intent.MARKET_ANALYSIS: [
        "price of", "quote", "stock price", "market data",
        "historical", "trend", "fundamentals", "compare",
        "current price", "trading at", "what is the price",
        "market analysis", "stock analysis", "ticker", "symbol"
    ],
    Intent.NEWS_ANALYSIS: [
        "news", "sentiment", "headlines", "market condition",
        "what's happening", "latest", "recent", "market movement",
        "events affecting", "market outlook"
    ],
    Intent.GOAL_PLANNING: [
        "goal", "reach", "save", "monthly contribution", "timeline",
        "projection", "when will i", "how much do i need",
        "years to goal", "financial plan", "achieve", "target",
        "path to", "years until"
    ],
    Intent.INVESTMENT_PLAN: [
        "plan", "strategy", "comprehensive", "full analysis",
        "complete picture", "what should i do", "recommendation",
        "overall strategy", "investment approach"
    ],
}
