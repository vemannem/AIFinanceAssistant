"""
Orchestration Module - Multi-Agent Coordination

Provides LangGraph-based orchestration for coordinating multiple financial agents.

Components:
- state: State schema and data structures
- intent_detector: Intent classification and data extraction
- agent_executor: Agent execution and result collection
- response_synthesizer: Output synthesis and formatting
- workflow: Main orchestration workflow
"""

from src.orchestration.state import (
    OrchestrationState,
    Intent,
    AgentType,
    Message,
    AgentExecution,
    RouterDecision,
    SynthesisResult,
    INTENT_TO_AGENTS,
    INTENT_KEYWORDS,
)

from src.orchestration.intent_detector import (
    IntentDetector,
    get_intent_detector,
)

from src.orchestration.agent_executor import (
    AgentExecutor,
    get_agent_executor,
)

from src.orchestration.response_synthesizer import (
    ResponseSynthesizer,
    get_response_synthesizer,
)

from src.orchestration.workflow import (
    OrchestratorWorkflow,
    get_orchestrator_workflow,
)

__all__ = [
    # State
    "OrchestrationState",
    "Intent",
    "AgentType",
    "Message",
    "AgentExecution",
    "RouterDecision",
    "SynthesisResult",
    "INTENT_TO_AGENTS",
    "INTENT_KEYWORDS",
    # Components
    "IntentDetector",
    "get_intent_detector",
    "AgentExecutor",
    "get_agent_executor",
    "ResponseSynthesizer",
    "get_response_synthesizer",
    "OrchestratorWorkflow",
    "get_orchestrator_workflow",
]
