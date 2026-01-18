"""
LangGraph Orchestration Workflow

Defines the multi-agent orchestration graph using LangGraph.
Coordinates intent detection, agent routing, execution, and response synthesis.
"""

import logging
from typing import Optional
from src.orchestration.state import OrchestrationState, Intent, AgentType
from src.orchestration.intent_detector import get_intent_detector
from src.orchestration.agent_executor import get_agent_executor
from src.orchestration.response_synthesizer import get_response_synthesizer
from src.core.logger import get_logger
from src.core.conversation_manager import get_conversation_manager


logger = get_logger(__name__)


class OrchestratorWorkflow:
    """
    Main orchestrator workflow using LangGraph patterns
    
    Workflow:
    1. Input: Parse user query into OrchestrationState
    2. Intent Detection: Detect intents and extract data
    3. Routing: Map intents to agents
    4. Execution: Run selected agents
    5. Synthesis: Combine outputs
    6. Output: Return synthesized response
    """
    
    def __init__(self):
        """Initialize workflow with components"""
        self.intent_detector = get_intent_detector()
        self.agent_executor = get_agent_executor()
        self.response_synthesizer = get_response_synthesizer()
        self.conversation_manager = get_conversation_manager()
    
    async def node_input(self, state: OrchestrationState) -> OrchestrationState:
        """
        Input node - Initialize/validate state
        
        Args:
            state: Initial orchestration state
            
        Returns:
            Validated state with trimmed history
        """
        logger.info(f"Input node: Processing '{state.user_input[:50]}...'")
        
        state.workflow_state = "input"
        
        # Add user message to history
        state.add_message("user", state.user_input)
        
        # Trim conversation history and create summary if needed
        msg_dicts = [
            {"role": m.role, "content": m.content}
            for m in state.conversation_history
        ]
        
        trimmed_msgs, summary = self.conversation_manager.trim_history(msg_dicts)
        
        # Update history with trimmed version
        if summary:
            state.conversation_summary = summary
            logger.info(f"Created conversation summary: {len(summary.key_topics)} topics")
        
        # Only keep the Message objects for recent messages (to preserve metadata)
        # For older messages that were summarized, we don't need to keep them
        if len(state.conversation_history) > len(trimmed_msgs):
            state.conversation_history = state.conversation_history[-len(trimmed_msgs):]
        
        return state
    
    async def node_intent_detection(
        self,
        state: OrchestrationState
    ) -> OrchestrationState:
        """
        Intent Detection node
        
        Detects user intent and extracts relevant context
        
        Args:
            state: Current orchestration state
            
        Returns:
            State with detected intents
        """
        logger.info("Intent Detection node: Detecting intents...")
        
        state.workflow_state = "intent_detection"
        
        # Detect intents
        intents = self.intent_detector.detect_intents(state.user_input)
        state.detected_intents = intents
        state.primary_intent = self.intent_detector.get_primary_intent(intents)
        state.confidence_score = self.intent_detector.get_confidence_score(
            intents,
            state.user_input
        )
        
        # Extract context
        state.extracted_tickers = self.intent_detector.extract_tickers(
            state.user_input
        )
        
        amounts = self.intent_detector.extract_dollar_amounts(state.user_input)
        state.extracted_amounts = amounts  # Add as attribute
        
        timeframe = self.intent_detector.extract_timeframe(state.user_input)
        state.extracted_timeframe = timeframe  # Add as attribute
        
        logger.info(
            f"Intents: {[i.value for i in intents]}, "
            f"Confidence: {state.confidence_score:.2f}"
        )
        
        return state
    
    async def node_routing(self, state: OrchestrationState) -> OrchestrationState:
        """
        Routing node
        
        Maps detected intents to agents
        
        Args:
            state: State with detected intents
            
        Returns:
            State with selected agents
        """
        logger.info("Routing node: Mapping intents to agents...")
        
        state.workflow_state = "routing"
        
        # Get routing decision
        decision = self.intent_detector.make_routing_decision(state)
        
        state.selected_agents = decision.agents
        state.routing_rationale = decision.reasoning
        
        logger.info(
            f"Routing decision: {[a.value for a in decision.agents]}"
        )
        
        return state
    
    async def node_execution(
        self,
        state: OrchestrationState
    ) -> OrchestrationState:
        """
        Execution node
        
        Executes selected agents
        
        Args:
            state: State with selected agents
            
        Returns:
            State with agent outputs
        """
        logger.info(f"Execution node: Running {len(state.selected_agents)} agent(s)...")
        
        # Execute agents (parallel if multiple, sequential if one)
        state = await self.agent_executor.execute(
            state,
            parallel=len(state.selected_agents) > 1
        )
        
        logger.info(f"Execution complete: {len(state.agent_executions)} agent(s) executed")
        
        return state
    
    async def node_synthesis(
        self,
        state: OrchestrationState
    ) -> OrchestrationState:
        """
        Synthesis node
        
        Combines agent outputs into coherent response
        
        Args:
            state: State with agent execution results
            
        Returns:
            State with synthesized response
        """
        logger.info("Synthesis node: Synthesizing response...")
        
        state = await self.response_synthesizer.synthesize(state)
        
        # Add assistant message to history
        state.add_message("assistant", state.synthesized_response)
        
        logger.info(f"Response length: {len(state.synthesized_response)} chars")
        
        return state
    
    async def execute_workflow(
        self,
        user_input: str,
        session_id: str = "default"
    ) -> OrchestrationState:
        """
        Execute complete orchestration workflow
        
        Args:
            user_input: User's natural language query
            session_id: Session identifier for tracking
            
        Returns:
            Final orchestration state with response
        """
        logger.info(f"=== Starting Orchestration Workflow ===")
        logger.info(f"Session: {session_id}, Input: '{user_input[:50]}...'")
        
        # Initialize state
        state = OrchestrationState(
            user_input=user_input,
            session_id=session_id
        )
        
        try:
            # Execute workflow nodes in sequence
            state = await self.node_input(state)
            state = await self.node_intent_detection(state)
            state = await self.node_routing(state)
            state = await self.node_execution(state)
            state = await self.node_synthesis(state)
            
            logger.info(f"=== Workflow Complete ===")
            logger.info(f"Final state: {state.workflow_state}")
            
            return state
        
        except Exception as e:
            logger.error(f"Workflow error: {str(e)}", exc_info=True)
            state.add_error(f"Workflow error: {str(e)}")
            state.workflow_state = "error"
            return state


# Singleton instance
_workflow = None


def get_orchestrator_workflow() -> OrchestratorWorkflow:
    """Get singleton instance of orchestrator workflow"""
    global _workflow
    if _workflow is None:
        _workflow = OrchestratorWorkflow()
    return _workflow
