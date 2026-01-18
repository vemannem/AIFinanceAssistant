# Phase 2C: Multi-Agent Orchestration System

Complete LangGraph-style orchestration layer for coordinating 6 specialized financial agents.

## Quick Start

### Basic Usage

```python
from src.orchestration import get_orchestrator_workflow
import asyncio

async def main():
    workflow = get_orchestrator_workflow()
    
    # Execute query
    state = await workflow.execute_workflow(
        user_input="Analyze my AAPL and BND portfolio",
        session_id="user_123"
    )
    
    # Get response
    print(state.synthesized_response)
    
    # Check what agents were selected
    print(f"Agents used: {[a.value for a in state.selected_agents]}")
    
    # Get conversation history
    for msg in state.conversation_history:
        print(f"{msg.role}: {msg.content[:100]}...")

asyncio.run(main())
```

### Output Structure

```python
state = await workflow.execute_workflow("What is diversification?")

state.synthesized_response  # Full text response
state.detected_intents      # [Intent.EDUCATION_QUESTION]
state.selected_agents       # [AgentType.FINANCE_QA]
state.agent_executions      # Execution records with timing
state.workflow_state        # "complete"
state.error_messages        # [] if successful
```

## Components

### Intent Detection
Automatically classifies user queries into intent types:
- Education questions
- Tax questions  
- Portfolio analysis
- Market analysis
- Goal planning
- News/sentiment analysis
- Investment planning

### Agents Coordinated
1. **Finance Q&A** - Educational content (RAG-powered)
2. **Portfolio Analysis** - Portfolio metrics & diversification
3. **Market Analysis** - Stock quotes & fundamentals
4. **Goal Planning** - Financial projections
5. **Tax Education** - Tax strategy & planning
6. **News Synthesizer** - Market news & sentiment

### Data Extraction
Automatically extracts from user input:
- Stock tickers (AAPL, BND, VTI, etc.)
- Dollar amounts ($50k, $100,000, etc.)
- Timeframes (5 years, 10 months, etc.)

## Test Results

**23/23 Tests Passing (100%)**

```
✅ Intent Detection (5/5)
✅ Data Extraction (3/3)
✅ Agent Routing (4/4)
✅ Confidence Scoring (3/3)
✅ Orchestration State (4/4)
✅ End-to-End Workflow (3/3)
✅ Multi-Agent Coordination (1/1)
```

Run tests:
```bash
python3 test_phase2c.py
```

## Architecture

```
User Input
   ↓
Intent Detection → Extract intents + context
   ↓
Routing → Map to appropriate agents
   ↓
Execution → Run agents (parallel or sequential)
   ↓
Synthesis → Combine outputs into coherent response
   ↓
Output
```

## Examples

### Example 1: Single Agent
```python
# Input: "What is portfolio diversification?"
# Intent: EDUCATION_QUESTION
# Agents: [FINANCE_QA]
# Response: Educational explanation from Finance Q&A agent
```

### Example 2: Multiple Agents
```python
# Input: "Analyze my $80k portfolio (60% AAPL, 40% BND) 
#         and project to reach $100k in 5 years"
# Intents: [PORTFOLIO_ANALYSIS, GOAL_PLANNING]
# Agents: [PORTFOLIO_ANALYSIS, GOAL_PLANNING]
# Execution: Parallel (both run at same time)
# Response: Combined portfolio analysis + financial projections
```

### Example 3: Complex Planning
```python
# Input: "Comprehensive investment plan, tax-efficient, $500k goal"
# Intents: [INVESTMENT_PLAN]
# Agents: [PORTFOLIO_ANALYSIS, GOAL_PLANNING, TAX_EDUCATION]
# Execution: Parallel (all 3 coordinated)
# Response: Integrated multi-agent response
```

## API Reference

### Main Entry Point

```python
from src.orchestration import get_orchestrator_workflow

workflow = get_orchestrator_workflow()
state = await workflow.execute_workflow(user_input, session_id="default")
```

### State Access

```python
# Input & History
state.user_input                  # Original query
state.conversation_history        # List of Message objects

# Intent & Routing
state.detected_intents           # List of Intent enums
state.primary_intent             # Main intent
state.confidence_score           # 0.0 to 1.0
state.selected_agents            # Agents to execute

# Execution Results
state.agent_executions           # List of AgentExecution records
state.agent_outputs              # Dict of agent results
state.extracted_tickers          # Extracted stock symbols
state.extracted_amounts          # Extracted dollar values

# Final Output
state.synthesized_response       # Text response for user
state.response_structure         # Organized sections
state.workflow_state             # "complete" when done

# Errors
state.error_messages             # Error list
state.has_errors()               # Boolean check
```

### Components

```python
from src.orchestration import (
    # State & Types
    OrchestrationState,
    Intent,
    AgentType,
    
    # Components
    get_intent_detector,
    get_agent_executor,
    get_response_synthesizer,
    get_orchestrator_workflow,
)

# Intent detection
detector = get_intent_detector()
intents = detector.detect_intents("user query")
tickers = detector.extract_tickers("query text")
amounts = detector.extract_dollar_amounts("query text")

# Agent execution
executor = get_agent_executor()
state = await executor.execute(state)

# Response synthesis
synthesizer = get_response_synthesizer()
state = await synthesizer.synthesize(state)
```

## Performance

| Operation | Time |
|---|---|
| Intent Detection | 1-2ms |
| Data Extraction | 1-2ms |
| Routing | 1ms |
| Agent Execution | 0-15s (depends on LLM calls) |
| Synthesis | 1-2ms |
| **Total** | **~13s for LLM agents** |

Parallel execution means 2 agents ≈ time of 1 agent (max of execution times).

## Files

- `src/orchestration/state.py` - State schema & enums
- `src/orchestration/intent_detector.py` - Intent classification
- `src/orchestration/agent_executor.py` - Agent execution
- `src/orchestration/response_synthesizer.py` - Output synthesis
- `src/orchestration/workflow.py` - Main orchestration workflow
- `src/orchestration/__init__.py` - Module exports
- `test_phase2c.py` - Comprehensive test suite

## Status

✅ Complete - 23/23 tests passing  
✅ Production ready  
✅ LangGraph compatible  
✅ Ready for Phase 3 frontend integration
