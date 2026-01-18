# LangGraph Orchestration Architecture Explained

## 1. STATE SCHEMA (TypedDict)

Located in: `src/orchestration/langgraph_workflow.py` (lines 24-57)

```
LangGraphState = {
  # INPUT
  user_input: str                          # User's question
  session_id: str                          # Session tracking
  conversation_history: List[Dict]         # Previous messages
  
  # INTENT DETECTION
  detected_intents: List[str]             # Multiple possible intents
  primary_intent: str                     # Main intent (e.g., "education_question")
  confidence_score: float                 # 0.0-1.0 confidence
  
  # DATA EXTRACTION
  extracted_tickers: List[str]            # Stock symbols (AAPL, GOOGL, etc)
  extracted_portfolio_data: Dict          # Portfolio holdings
  extracted_goal_data: Dict               # Financial goals
  
  # ROUTING & AGENTS
  selected_agents: List[str]              # Which agents to call
  routing_rationale: str                  # Why these agents were selected
  
  # EXECUTION
  agent_executions: List[Dict]            # Results from each agent
  execution_errors: List[str]             # Any errors that occurred
  execution_times: Dict[str, float]       # How long each agent took
  
  # OUTPUT
  final_response: str                     # Final answer to user
  citations: List[Dict]                   # Sources for response
  confidence: float                       # Confidence in answer
}
```

## 2. WORKFLOW GRAPH (StateGraph)

```
┌──────────────────────────────────────────────────────────────┐
│                   LangGraph Workflow                         │
└──────────────────────────────────────────────────────────────┘

START
  ↓
┌─────────────────────────────────────────────────────────────┐
│ INPUT NODE                                                  │
│ - Validate user input                                       │
│ - Initialize session ID                                     │
│ - Load conversation history                                 │
│ - Add current message to history                            │
└─────────────────────────────────────────────────────────────┘
  ↓
┌─────────────────────────────────────────────────────────────┐
│ INTENT DETECTION NODE                                       │
│ - Classify user intent:                                     │
│   • education_question → Finance Q&A                        │
│   • tax_question → Tax Education                            │
│   • portfolio_analysis → Portfolio Agent                    │
│   • market_analysis → Market Analysis                       │
│   • news_analysis → News Synthesizer                        │
│   • goal_planning → Goal Planning                           │
│   • investment_plan → Portfolio + Goals (2 agents)          │
│ - Extract tickers (AAPL, GOOGL, etc)                       │
│ - Extract amounts ($1000, $5000, etc)                       │
│ - Calculate confidence score                                │
└─────────────────────────────────────────────────────────────┘
  ↓
┌─────────────────────────────────────────────────────────────┐
│ ROUTING NODE                                                │
│ - Map intent → Agent(s)                                     │
│ - Build intent_to_agents mapping:                           │
│   {                                                         │
│     "education_question": ["finance_qa"],                   │
│     "tax_question": ["tax_education"],                      │
│     "portfolio_analysis": ["portfolio_analysis"],           │
│     "market_analysis": ["market_analysis"],                 │
│     "investment_plan": ["portfolio_analysis",               │
│                         "goal_planning"]  ← Multi-agent!    │
│   }                                                         │
│ - Document routing decision                                 │
└─────────────────────────────────────────────────────────────┘
  ↓
  ┌─ CONDITIONAL EDGE ─┐
  │ Has agents?        │
  └────────┬──────┬────┘
           │      │
         YES    NO
           │      └──────────┐
           ↓                 ↓
    ┌──────────────┐   ┌──────────────┐
    │ EXECUTE      │   │ SKIP TO      │
    │ AGENTS       │   │ SYNTHESIS    │
    └──────┬───────┘   └──────┬───────┘
           └──────────┬───────┘
                      ↓
┌─────────────────────────────────────────────────────────────┐
│ AGENT EXECUTION NODE                                        │
│ - Convert agent names to AgentType enums                    │
│ - Execute agents IN PARALLEL using asyncio.gather():       │
│                                                             │
│   await asyncio.gather(                                     │
│     agent_executor.execute_agent(FINANCE_QA, input),       │
│     agent_executor.execute_agent(PORTFOLIO, input),        │
│     agent_executor.execute_agent(MARKET, input),           │
│     return_exceptions=False                                 │
│   )                                                         │
│                                                             │
│ - Collect results from all agents                          │
│ - Track execution time per agent                           │
│ - Log any errors                                           │
└─────────────────────────────────────────────────────────────┘
  ↓
┌─────────────────────────────────────────────────────────────┐
│ SYNTHESIS NODE                                              │
│ - Combine agent outputs into single response                │
│ - Generate citations                                        │
│ - Set final confidence score                                │
│ - Create metadata with:                                     │
│   • agents_used                                             │
│   • intent                                                  │
│   • execution_summary                                       │
└─────────────────────────────────────────────────────────────┘
  ↓
END

(Error Handler Node available if synthesis fails)
```

## 3. HOW AGENTS ARE CALLED

### Step 1: Agent Selection (Intent Detection)
```python
# User asks: "What stocks should I buy for a balanced portfolio?"

detected_intent = "investment_plan"  # ← Detected by intent detector
selected_agents = ["portfolio_analysis", "goal_planning"]
```

### Step 2: Agent Mapping (Routing)
```python
intent_to_agents = {
    "investment_plan": ["portfolio_analysis", "goal_planning"],
}

selected_agents = intent_to_agents[detected_intent]
# Result: ["portfolio_analysis", "goal_planning"]
```

### Step 3: Agent Execution (Parallel)
```python
# In AgentExecutor.execute_agents_parallel()

agents = [AgentType.PORTFOLIO_ANALYSIS, AgentType.GOAL_PLANNING]

tasks = [
    self.execute_agent(AgentType.PORTFOLIO_ANALYSIS, user_input, context),
    self.execute_agent(AgentType.GOAL_PLANNING, user_input, context),
]

# ⚡ Run BOTH agents at the same time (parallel)!
results = await asyncio.gather(*tasks)
```

### Step 4: Individual Agent Execution
```python
async def execute_agent(agent_type, user_input, context):
    """
    Execute one agent
    
    1. Get agent instance from agents_map
    2. Build input with context (tickers, amounts, timeframe)
    3. Call: await agent.execute(input)
    4. Measure execution time
    5. Return result or error
    """
    
    agent = self.agents_map[agent_type]  # Get actual agent instance
    
    output = await agent.execute(
        user_input=user_input,
        conversation_context=None
    )
    
    return {
        "status": "success",
        "output": output,
        "execution_time_ms": 1234.5,
        "agent": "portfolio_analysis"
    }
```

## 4. AGENT TYPES & THEIR PURPOSES

| Agent | Intent | Purpose |
|-------|--------|---------|
| `finance_qa` | education_question | Answer general finance questions using RAG |
| `tax_education` | tax_question | Provide tax planning advice |
| `portfolio_analysis` | portfolio_analysis | Analyze portfolio allocation & diversification |
| `market_analysis` | market_analysis | Get real-time stock quotes & market data |
| `news_synthesizer` | news_analysis | Summarize financial news |
| `goal_planning` | goal_planning | Calculate retirement/savings goals |

## 5. STATE FLOW EXAMPLE

### User Input
```
"What should I invest in for retirement? I have $100k"
```

### State Updates Through Nodes

**1. INPUT Node**
```python
{
  "user_input": "What should I invest in for retirement? I have $100k",
  "session_id": "uuid-123",
  "conversation_history": [{role: "user", content: "..."}],
  "workflow_started_at": "2026-01-18T10:00:00"
}
```

**2. INTENT DETECTION Node**
```python
{
  "detected_intents": ["goal_planning", "investment_plan"],
  "primary_intent": "investment_plan",
  "confidence_score": 0.85,
  "extracted_tickers": [],
  "extracted_amounts": ["$100k"],
  ...
}
```

**3. ROUTING Node**
```python
{
  "selected_agents": ["portfolio_analysis", "goal_planning"],
  "routing_rationale": "Primary intent: investment_plan | 
                        Selected agents: [portfolio_analysis, goal_planning]",
  ...
}
```

**4. AGENT EXECUTION Node** (Parallel)
```
portfolio_analysis agent:     → 234ms → Returns portfolio allocation advice
goal_planning agent:          → 567ms → Returns retirement calculations
(Both running at same time!)

Result merged into state:
{
  "agent_executions": [
    {
      "agent": "portfolio_analysis",
      "status": "success",
      "output": {...},
      "execution_time_ms": 234
    },
    {
      "agent": "goal_planning", 
      "status": "success",
      "output": {...},
      "execution_time_ms": 567
    }
  ],
  "execution_times": {
    "portfolio_analysis": 234,
    "goal_planning": 567
  },
  "execution_errors": []
}
```

**5. SYNTHESIS Node**
```python
{
  "final_response": "Based on your $100k investment amount and retirement goals...",
  "citations": [
    {"title": "...", "source_url": "...", "category": "..."}
  ],
  "confidence": 0.88,
  "metadata": {
    "agents_used": ["portfolio_analysis", "goal_planning"],
    "intent": "investment_plan",
    "execution_summary": {
      "total_agents": 2,
      "errors": 0
    }
  },
  "workflow_completed_at": "2026-01-18T10:00:01.2",
  "total_execution_time_ms": 1234.5
}
```

## 6. KEY FEATURES

✅ **Conditional Routing**: Only execute agents if needed
✅ **Parallel Execution**: Multiple agents run simultaneously (faster!)
✅ **State Persistence**: Each node updates the shared state
✅ **Error Tracking**: Failed agents don't stop the workflow
✅ **Execution Metrics**: Track time and performance per agent
✅ **Fallback Handlers**: Error handler node provides backup response
✅ **Multi-Intent Support**: One user query can trigger multiple agents

## 7. FILE LOCATIONS

- **State Definition**: `src/orchestration/state.py`
- **Graph Definition**: `src/orchestration/langgraph_workflow.py`
- **Agent Executor**: `src/orchestration/agent_executor.py`
- **Intent Detector**: `src/orchestration/intent_detector.py`
- **Response Synthesizer**: `src/orchestration/response_synthesizer.py`
- **Actual Agents**: `src/agents/`
  - `finance_qa.py`
  - `portfolio_analysis.py`
  - `market_analysis.py`
  - `goal_planning.py`
  - `tax_education.py`
  - `news_synthesizer.py`
