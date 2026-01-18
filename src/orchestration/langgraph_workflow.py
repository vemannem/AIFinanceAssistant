"""
LangGraph StateGraph Implementation for Multi-Agent Orchestration

Full LangGraph integration with StateGraph for robust,
production-grade multi-agent coordination with:
- LLM-based router agent for intelligent routing
- Individual agent nodes (6 agents)
- Integrated safety guardrails
- Input/output validation
- PII detection and compliance checks
"""

import logging
from typing import Any, TypedDict, List, Optional, Dict
from datetime import datetime
import uuid
import asyncio

from langgraph.graph import StateGraph, END
from openai import AsyncOpenAI

from src.orchestration.state import (
    OrchestrationState, Intent, AgentType, AgentExecution, Message
)
from src.orchestration.intent_detector import get_intent_detector
from src.orchestration.agent_executor import get_agent_executor
from src.orchestration.response_synthesizer import get_response_synthesizer
from src.core.logger import get_logger
from src.core.conversation_manager import get_conversation_manager
from src.core.guardrails import (
    InputValidator,
    PIIDetector,
    DisclaimerManager,
)
from src.core.config import Config


logger = get_logger(__name__)


class LangGraphState(TypedDict, total=False):
    """LangGraph-compatible state definition with guardrails"""
    # Input & Context
    user_input: str
    session_id: str
    conversation_history: List[Dict[str, str]]
    conversation_summary: Optional[Dict[str, Any]]
    
    # Guardrails validation
    input_validated: bool
    guardrail_errors: List[str]
    pii_detected: bool
    
    # Intent & Routing
    detected_intents: List[str]
    primary_intent: str
    confidence_score: float
    selected_agent: str  # SINGLE agent selected by router (not a list!)
    selected_agents: List[str]  # For backward compatibility with frontend
    routing_rationale: str
    
    # Extracted Data
    extracted_tickers: List[str]
    extracted_portfolio_data: Optional[Dict[str, Any]]
    extracted_goal_data: Optional[Dict[str, Any]]
    extracted_tax_context: Optional[str]
    market_context: Optional[str]
    
    # Agent Executions
    agent_executions: List[Dict[str, Any]]
    execution_errors: List[str]
    execution_times: Dict[str, float]
    
    # Response
    final_response: str
    citations: List[Dict[str, Any]]
    confidence: float
    metadata: Dict[str, Any]
    
    # Workflow tracking
    workflow_started_at: str
    workflow_completed_at: Optional[str]
    total_execution_time_ms: float


class LangGraphOrchestrator:
    """
    LangGraph-based multi-agent orchestrator
    
    Uses LangGraph StateGraph for robust workflow management:
    - State persistence across node executions
    - Conditional routing based on state
    - Error recovery and fallbacks
    - Complete audit trail
    """
    
    def __init__(self):
        """Initialize orchestrator with all components"""
        self.intent_detector = get_intent_detector()
        self.agent_executor = get_agent_executor()
        self.response_synthesizer = get_response_synthesizer()
        self.conversation_manager = get_conversation_manager()
        
        # Build the StateGraph
        self.graph = self._build_graph()
        
        logger.info("LangGraph Orchestrator initialized")
    
    def _build_graph(self) -> StateGraph:
        """
        Build the LangGraph StateGraph with router agent pattern
        
        Graph structure:
        START → input → intent_detection → router → [6 agent nodes] → synthesis → END
                                              ↓
                                        (conditional routing to agent)
        
        Returns:
            Compiled StateGraph
        """
        # Create the StateGraph
        graph = StateGraph(LangGraphState)
        
        # Add nodes
        graph.add_node("input", self._node_input)
        graph.add_node("intent_detection", self._node_intent_detection)
        graph.add_node("router", self._node_router)
        
        # Individual agent nodes
        graph.add_node("agent_finance_qa", self._node_agent_finance_qa)
        graph.add_node("agent_portfolio", self._node_agent_portfolio)
        graph.add_node("agent_market", self._node_agent_market)
        graph.add_node("agent_goal", self._node_agent_goal)
        graph.add_node("agent_tax", self._node_agent_tax)
        graph.add_node("agent_news", self._node_agent_news)
        
        # Synthesis and error handling
        graph.add_node("synthesis", self._node_synthesis)
        graph.add_node("error_handler", self._node_error_handler)
        
        # Add edges
        graph.set_entry_point("input")
        
        # Input → Intent Detection
        graph.add_edge("input", "intent_detection")
        
        # Intent Detection → Router
        graph.add_edge("intent_detection", "router")
        
        # Router → Individual Agents (conditional routing)
        graph.add_conditional_edges(
            "router",
            self._route_to_agent,
            {
                "finance_qa": "agent_finance_qa",
                "portfolio": "agent_portfolio",
                "market": "agent_market",
                "goal": "agent_goal",
                "tax": "agent_tax",
                "news": "agent_news",
            }
        )
        
        # All agents → Synthesis
        graph.add_edge("agent_finance_qa", "synthesis")
        graph.add_edge("agent_portfolio", "synthesis")
        graph.add_edge("agent_market", "synthesis")
        graph.add_edge("agent_goal", "synthesis")
        graph.add_edge("agent_tax", "synthesis")
        graph.add_edge("agent_news", "synthesis")
        
        # Synthesis → End
        graph.add_edge("synthesis", END)
        
        # Error handler → Synthesis
        graph.add_edge("error_handler", "synthesis")
        
        # Compile the graph
        compiled_graph = graph.compile()
        
        logger.info("LangGraph StateGraph compiled with router agent pattern")
        return compiled_graph
    
    async def _node_input(self, state: LangGraphState) -> LangGraphState:
        """
        Input node: Initialize state and apply input guardrails
        
        Responsibilities:
        - Apply input validation guardrails
        - Detect PII in input
        - Initialize session tracking
        - Prepare conversation history
        - Create audit trail
        """
        logger.info(f"[INPUT] Processing: '{state['user_input'][:50]}...'")
        
        # Initialize workflow timing (MUST be first)
        if not state.get("workflow_started_at"):
            state["workflow_started_at"] = datetime.now().isoformat()
        
        # Initialize guardrail tracking
        state["guardrail_errors"] = []
        state["input_validated"] = False
        state["pii_detected"] = False
        
        # GUARDRAILS: Input validation
        try:
            input_validator = InputValidator()
            is_valid, error = input_validator.validate_query(state["user_input"])
            
            if not is_valid:
                state["execution_errors"].append(f"Input validation failed: {error}")
                state["final_response"] = "Your question doesn't meet our safety requirements. Please try again."
                state["confidence"] = 0.0
                logger.warning(f"[INPUT] ✗ Input validation failed: {error}")
                return state
            
            state["input_validated"] = True
            logger.info("[INPUT] ✓ Input validation passed")
        except Exception as e:
            logger.error(f"[INPUT] Error during input validation: {str(e)}")
            state["guardrail_errors"].append(str(e))
        
        # GUARDRAILS: PII Detection
        try:
            pii_detector = PIIDetector()
            pii_detected, pii_types = pii_detector.detect(state["user_input"])
            
            if pii_detected:
                state["pii_detected"] = True
                warning = pii_detector.get_warning(pii_types)
                state["execution_errors"].append(f"PII detected: {pii_types}")
                state["final_response"] = warning
                state["confidence"] = 0.0
                logger.warning(f"[INPUT] ✗ PII detected: {pii_types}")
                return state
            
            logger.info("[INPUT] ✓ No PII detected")
        except Exception as e:
            logger.error(f"[INPUT] Error during PII detection: {str(e)}")
            state["guardrail_errors"].append(str(e))
        
        # Ensure session ID
        if not state.get("session_id"):
            state["session_id"] = str(uuid.uuid4())
        
        # Initialize empty lists if needed
        if not state.get("conversation_history"):
            state["conversation_history"] = []
        
        if not state.get("agent_executions"):
            state["agent_executions"] = []
        
        if not state.get("execution_errors"):
            state["execution_errors"] = []
        
        if not state.get("execution_times"):
            state["execution_times"] = {}
        
        if not state.get("metadata"):
            state["metadata"] = {}
        
        # Add user message to history
        state["conversation_history"].append({
            "role": "user",
            "content": state["user_input"],
            "timestamp": datetime.now().isoformat()
        })
        
        # Get conversation summary for context
        try:
            trimmed_history, summary = self.conversation_manager.trim_history(
                state["conversation_history"]
            )
            
            if summary:
                state["conversation_summary"] = {
                    "key_topics": summary.key_topics,
                    "summary_text": summary.summary_text,
                    "conversation_intent": summary.conversation_intent,
                    "messages_summarized": summary.messages_summarized
                }
                logger.info(f"[INPUT] Conversation summary: {len(summary.key_topics)} topics")
        except Exception as e:
            logger.warning(f"[INPUT] Could not generate conversation summary: {str(e)}")
        
        logger.info(f"[INPUT] ✓ State initialized | Session: {state['session_id']}")
        return state
    
    async def _node_intent_detection(self, state: LangGraphState) -> LangGraphState:
        """
        Intent Detection node: Classify user intent and extract data
        
        Responsibilities:
        - Detect primary and secondary intents
        - Extract structured data (tickers, amounts, etc.)
        - Calculate confidence scores
        - Prepare for routing
        """
        logger.info("[INTENT] Starting intent detection...")
        
        # Detect intents
        intents = self.intent_detector.detect_intents(state["user_input"])
        state["detected_intents"] = [intent.value for intent in intents]
        state["primary_intent"] = intents[0].value if intents else "unknown"
        
        # Extract structured data - only use methods that exist
        tickers = self.intent_detector.extract_tickers(state["user_input"])
        state["extracted_tickers"] = tickers
        
        # Extract dollar amounts if present
        amounts = self.intent_detector.extract_dollar_amounts(state["user_input"])
        if amounts:
            state["extracted_amounts"] = amounts
        
        # Extract timeframe if present
        timeframe = self.intent_detector.extract_timeframe(state["user_input"])
        if timeframe:
            state["extracted_timeframe"] = timeframe
        
        # Calculate confidence based on extracted data and intent detection
        confidence = 0.7  # Base confidence
        if tickers:
            confidence += 0.1  # Boost for detected tickers
        if amounts:
            confidence += 0.05  # Boost for dollar amounts
        if len(state["detected_intents"]) > 1:
            confidence += 0.05  # Boost for multiple intents
        
        state["confidence_score"] = min(0.99, confidence)  # Cap at 0.99
        
        logger.info(
            f"[INTENT] ✓ Detected: {state['detected_intents']} | "
            f"Confidence: {state['confidence_score']:.2f} | "
            f"Tickers: {tickers}"
        )
        
        return state
    
    async def _node_router(self, state: LangGraphState) -> LangGraphState:
        """
        Router node: Uses LLM to intelligently select the BEST agent
        
        This is the router agent pattern - calls OpenAI to decide which agent
        is most suitable for the user's intent, rather than using hardcoded rules.
        
        Responsibilities:
        - Call LLM to analyze intent and context
        - Select ONE best agent for this query
        - Provide routing rationale
        """
        logger.info("[ROUTER] Starting LLM-based routing...")
        
        try:
            # Skip if guardrails failed
            if not state.get("input_validated"):
                state["selected_agent"] = "finance_qa"  # Fallback
                state["routing_rationale"] = "Guardrail blocked input, using fallback agent"
                logger.warning("[ROUTER] ⚠ Input not validated, using fallback")
                return state
            
            # Build router prompt for LLM
            router_prompt = f"""You are a financial assistant router. Based on the user's question and detected intent, select the SINGLE BEST agent to handle this query.

User Question: {state['user_input']}
Detected Intents: {', '.join(state.get('detected_intents', ['unknown']))}
Primary Intent: {state.get('primary_intent', 'unknown')}
Extracted Tickers: {', '.join(state.get('extracted_tickers', [])) or 'None'}

Available Agents:
1. finance_qa - General finance education, explanations, advice
2. portfolio - Portfolio analysis, allocation, diversification, rebalancing
3. market - Real-time stock data, quotes, market analysis, trends
4. goal - Financial goal planning, retirement calculations, projections
5. tax - Tax planning, tax strategies, tax education
6. news - Financial news synthesis, market news, updates

Respond with ONLY the agent name (no explanation). Choose from: finance_qa, portfolio, market, goal, tax, or news."""

            # Call LLM router
            client = AsyncOpenAI(api_key=Config.OPENAI_API_KEY)
            
            response = await client.chat.completions.create(
                model=Config.OPENAI_MODEL,
                messages=[{"role": "user", "content": router_prompt}],
                temperature=0.2,  # Lower temperature for consistent routing
                max_tokens=20
            )
            
            selected = response.choices[0].message.content.strip().lower()
            
            # Validate agent name
            valid_agents = ["finance_qa", "portfolio", "market", "goal", "tax", "news"]
            if selected not in valid_agents:
                selected = "finance_qa"  # Fallback to finance_qa
                logger.warning(f"[ROUTER] Invalid agent '{selected}', using fallback")
            
            state["selected_agent"] = selected
            state["selected_agents"] = [selected]  # For backward compatibility
            state["routing_rationale"] = f"LLM router selected: {selected} | Intent: {state.get('primary_intent', 'unknown')}"
            
            logger.info(f"[ROUTER] ✓ Selected agent: {selected}")
            
        except Exception as e:
            logger.error(f"[ROUTER] ✗ Error during routing: {str(e)}")
            state["selected_agent"] = "finance_qa"  # Fallback
            state["selected_agents"] = ["finance_qa"]
            state["routing_rationale"] = f"Routing error, using fallback: {str(e)}"
            state["execution_errors"].append(f"Router error: {str(e)}")
        
        return state
    
    def _route_to_agent(self, state: LangGraphState) -> str:
        """
        Conditional edge function - determines which agent node to execute
        
        Returns:
            Agent name (finance_qa, portfolio, market, goal, tax, or news)
        """
        agent = state.get("selected_agent", "finance_qa")
        
        # Validate
        valid_agents = ["finance_qa", "portfolio", "market", "goal", "tax", "news"]
        if agent not in valid_agents:
            agent = "finance_qa"
        
        logger.info(f"[ROUTER] Routing to: {agent}")
        return agent
    
    async def _node_agent_finance_qa(self, state: LangGraphState) -> LangGraphState:
        """Execute Finance QA agent"""
        return await self._execute_single_agent(state, "finance_qa", AgentType.FINANCE_QA)
    
    async def _node_agent_portfolio(self, state: LangGraphState) -> LangGraphState:
        """Execute Portfolio Analysis agent"""
        return await self._execute_single_agent(state, "portfolio", AgentType.PORTFOLIO_ANALYSIS)
    
    async def _node_agent_market(self, state: LangGraphState) -> LangGraphState:
        """Execute Market Analysis agent"""
        return await self._execute_single_agent(state, "market", AgentType.MARKET_ANALYSIS)
    
    async def _node_agent_goal(self, state: LangGraphState) -> LangGraphState:
        """Execute Goal Planning agent"""
        return await self._execute_single_agent(state, "goal", AgentType.GOAL_PLANNING)
    
    async def _node_agent_tax(self, state: LangGraphState) -> LangGraphState:
        """Execute Tax Education agent"""
        return await self._execute_single_agent(state, "tax", AgentType.TAX_EDUCATION)
    
    async def _node_agent_news(self, state: LangGraphState) -> LangGraphState:
        """Execute News Synthesizer agent"""
        return await self._execute_single_agent(state, "news", AgentType.NEWS_SYNTHESIZER)
    
    async def _execute_single_agent(
        self, 
        state: LangGraphState, 
        agent_name: str, 
        agent_type: AgentType
    ) -> LangGraphState:
        """
        Execute a single agent and track results
        
        Args:
            state: Current workflow state
            agent_name: Human-readable agent name
            agent_type: AgentType enum
            
        Returns:
            Updated state with agent results
        """
        logger.info(f"[AGENT_{agent_name.upper()}] Starting execution...")
        
        try:
            execution_result = await self.agent_executor.execute_agent(
                agent_type=agent_type,
                user_input=state["user_input"],
                context={
                    "tickers": state.get("extracted_tickers", []),
                    "conversation_history": state.get("conversation_history", []),
                }
            )
            
            # Record execution
            execution_record = {
                "agent": agent_name,
                "status": execution_result.get("status", "error"),
                "output": execution_result.get("output", {}),
                "error": execution_result.get("error"),
                "execution_time_ms": execution_result.get("execution_time_ms", 0),
            }
            
            state["agent_executions"].append(execution_record)
            state["execution_times"][agent_name] = execution_result.get("execution_time_ms", 0)
            
            if execution_result.get("status") == "error":
                error_msg = f"{agent_name}: {execution_result.get('error', 'Unknown error')}"
                state["execution_errors"].append(error_msg)
                logger.error(f"[AGENT_{agent_name.upper()}] ✗ {error_msg}")
            else:
                logger.info(f"[AGENT_{agent_name.upper()}] ✓ Completed in {execution_result.get('execution_time_ms', 0):.1f}ms")
        
        except Exception as e:
            logger.error(f"[AGENT_{agent_name.upper()}] ✗ Exception: {str(e)}", exc_info=True)
            state["execution_errors"].append(f"{agent_name}: {str(e)}")
        
        return state
    
    async def _node_synthesis(self, state: LangGraphState) -> LangGraphState:
        """
        Synthesis node: Combine agent outputs and apply output guardrails
        
        Responsibilities:
        - Generate final response
        - Apply output safety guardrails
        - Check for PII in response
        - Add compliance warnings
        - Collect citations
        """
        logger.info("[SYNTHESIS] Synthesizing final response with guardrails...")
        
        try:
            # Use FinanceQA as primary synthesis
            from src.agents.finance_qa import FinanceQAAgent
            
            agent = FinanceQAAgent()
            output = await agent.execute(
                user_message=state["user_input"],
                conversation_context=None,
            )
            
            response_text = output.answer_text
            
            # GUARDRAILS: Output Safety Validation (PII in response)
            try:
                pii_detector = PIIDetector()
                pii_detected, pii_types = pii_detector.detect(response_text)
                
                if pii_detected:
                    logger.warning(f"[SYNTHESIS] ✗ PII detected in response: {pii_types}")
                    state["final_response"] = "Generated response contained sensitive data and was redacted for privacy."
                    state["confidence"] = 0.0
                    return state
                
                logger.info("[SYNTHESIS] ✓ No PII in response")
            except Exception as e:
                logger.warning(f"[SYNTHESIS] Error during PII detection: {str(e)}")
            
            # GUARDRAILS: Compliance Check (add disclaimer for financial advice)
            try:
                disclaimer_manager = DisclaimerManager()
                detected_intents = state.get("detected_intents", [])
                response_text = disclaimer_manager.add_disclaimers(response_text, detected_intents)
                logger.info("[SYNTHESIS] ✓ Disclaimers added as needed")
            except Exception as e:
                logger.warning(f"[SYNTHESIS] Error during disclaimer addition: {str(e)}")
            
            state["final_response"] = response_text
            state["citations"] = [
                {
                    "title": c.get("title", ""),
                    "source_url": c.get("source_url", ""),
                    "category": c.get("category", "")
                }
                for c in output.citations
            ]
            state["confidence"] = 0.85
            
            # Add metadata
            if "metadata" not in state:
                state["metadata"] = {}
            
            state["metadata"]["agents_used"] = state.get("selected_agents", [])
            state["metadata"]["intent"] = state.get("primary_intent")
            state["metadata"]["execution_summary"] = {
                "total_agents": len(state.get("selected_agents", [])),
                "errors": len(state.get("execution_errors", []))
            }
            
            logger.info("[SYNTHESIS] ✓ Response synthesized with guardrails applied")
        
        except Exception as e:
            logger.error(f"[SYNTHESIS] ✗ Error during synthesis: {str(e)}")
            state["final_response"] = f"Error generating response: {str(e)}"
            state["confidence"] = 0.0
        
        return state
    
    async def _node_error_handler(self, state: LangGraphState) -> LangGraphState:
        """
        Error handler node: Fallback response generation
        
        Responsibilities:
        - Generate fallback response on error
        - Log error details
        - Preserve error context
        """
        logger.warning("[ERROR_HANDLER] Generating fallback response...")
        
        if not state.get("final_response"):
            state["final_response"] = (
                "I encountered an error processing your request. "
                "Please try again or rephrase your question."
            )
        
        state["confidence"] = 0.0
        
        return state
    
    async def execute(
        self,
        user_input: str,
        session_id: Optional[str] = None,
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> Dict[str, Any]:
        """
        Execute the orchestration workflow
        
        Args:
            user_input: User's natural language query
            session_id: Optional session identifier
            conversation_history: Previous conversation messages
            
        Returns:
            Final response with metadata
        """
        # Prepare initial state
        initial_state: LangGraphState = {
            "user_input": user_input,
            "session_id": session_id or str(uuid.uuid4()),
            "conversation_history": conversation_history or [],
            "detected_intents": [],
            "primary_intent": "unknown",
            "confidence_score": 0.0,
            "selected_agents": [],
            "selected_agent": "",  # For router pattern (singular)
            "routing_rationale": "",
            "extracted_tickers": [],
            "agent_executions": [],
            "execution_errors": [],
            "execution_times": {},
            "final_response": "",
            "citations": [],
            "confidence": 0.0,
            "metadata": {},
            # Guardrail fields
            "input_validated": False,
            "guardrail_errors": [],
            "pii_detected": False
        }
        
        logger.info(f"[ORCHESTRATOR] Starting workflow for session: {initial_state['session_id']}")
        
        # Execute graph using async invoke
        final_state = await self.graph.ainvoke(initial_state)
        
        # Calculate total execution time
        workflow_started = datetime.fromisoformat(final_state.get("workflow_started_at"))
        final_state["workflow_completed_at"] = datetime.now().isoformat()
        total_time = (datetime.now() - workflow_started).total_seconds() * 1000
        final_state["total_execution_time_ms"] = total_time
        
        logger.info(
            f"[ORCHESTRATOR] ✓ Workflow completed in {total_time:.1f}ms | "
            f"Session: {final_state['session_id']}"
        )
        
        return {
            "response": final_state.get("final_response", ""),
            "citations": final_state.get("citations", []),
            "confidence": final_state.get("confidence", 0.0),
            "intent": final_state.get("primary_intent"),
            "agents_used": final_state.get("selected_agents", []),
            "execution_times": final_state.get("execution_times", {}),
            "total_time_ms": final_state.get("total_execution_time_ms", 0),
            "session_id": final_state.get("session_id"),
            "metadata": final_state.get("metadata", {})
        }


# Singleton instance
_orchestrator: Optional[LangGraphOrchestrator] = None


def get_langgraph_orchestrator() -> LangGraphOrchestrator:
    """Get or create LangGraph orchestrator instance"""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = LangGraphOrchestrator()
    return _orchestrator
