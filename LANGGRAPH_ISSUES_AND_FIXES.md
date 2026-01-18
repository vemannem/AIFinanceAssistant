# LangGraph Orchestration: Current Issues & Solutions

## ⚠️ ISSUE 1: Not Using Individual Agent Nodes

### Current Implementation (Broadcast Pattern)
```python
# In _build_graph():
graph.add_node("agent_execution", self._node_agent_execution)

# In agent_execution node:
await self.agent_executor.execute_agents_parallel(
    agents=[finance_qa, portfolio, market, goal, tax, news],
    ...
)
```

**Problem**: 
- ❌ All 6 agents are called inside ONE node
- ❌ No conditional routing between agents
- ❌ Can't selectively execute single agents
- ❌ Doesn't scale well (all agents always run)
- ❌ Not a true LangGraph pattern

### Correct Implementation (Router Pattern)
```python
# Should be:
def _build_graph(self) -> StateGraph:
    graph = StateGraph(LangGraphState)
    
    # 1. INPUT node
    graph.add_node("input", self._node_input)
    
    # 2. INTENT DETECTION node (calls LLM)
    graph.add_node("intent_detection", self._node_intent_detection)
    
    # 3. ROUTER node (calls LLM to decide which agent is BEST)
    graph.add_node("router", self._node_router)
    
    # 4. INDIVIDUAL AGENT NODES (one per agent!)
    graph.add_node("agent_finance_qa", self._node_agent_finance_qa)
    graph.add_node("agent_portfolio", self._node_agent_portfolio)
    graph.add_node("agent_market", self._node_agent_market)
    graph.add_node("agent_goal", self._node_agent_goal)
    graph.add_node("agent_tax", self._node_agent_tax)
    graph.add_node("agent_news", self._node_agent_news)
    
    # 5. SYNTHESIS node
    graph.add_node("synthesis", self._node_synthesis)
    
    # EDGES with CONDITIONAL ROUTING
    graph.set_entry_point("input")
    graph.add_edge("input", "intent_detection")
    graph.add_edge("intent_detection", "router")
    
    # Router decides which agent to call
    graph.add_conditional_edges(
        "router",
        self._route_to_agent,  # Function returns agent name
        {
            "finance_qa": "agent_finance_qa",
            "portfolio": "agent_portfolio",
            "market": "agent_market",
            "goal": "agent_goal",
            "tax": "agent_tax",
            "news": "agent_news",
        }
    )
    
    # All agents → synthesis
    graph.add_edge("agent_finance_qa", "synthesis")
    graph.add_edge("agent_portfolio", "synthesis")
    graph.add_edge("agent_market", "synthesis")
    graph.add_edge("agent_goal", "synthesis")
    graph.add_edge("agent_tax", "synthesis")
    graph.add_edge("agent_news", "synthesis")
    
    graph.add_edge("synthesis", END)
    return graph.compile()

# Router node implementation
async def _node_router(self, state: LangGraphState) -> LangGraphState:
    """Router agent: Uses LLM to decide BEST agent for this intent"""
    
    # Create router prompt
    router_prompt = f"""
    Given this user question and detected intent, which agent is BEST suited?
    
    User: {state['user_input']}
    Intent: {state['primary_intent']}
    Extracted Tickers: {state['extracted_tickers']}
    
    Options:
    - finance_qa: General finance education questions
    - portfolio: Portfolio analysis & allocation
    - market: Real-time stock data & market analysis
    - goal: Financial goal planning & projections
    - tax: Tax planning & education
    - news: Financial news synthesis
    
    Choose ONE agent. Return ONLY the agent name.
    """
    
    # Call LLM for routing decision
    from openai import AsyncOpenAI
    client = AsyncOpenAI()
    
    response = await client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": router_prompt}],
        temperature=0.3,
        max_tokens=50
    )
    
    chosen_agent = response.choices[0].message.content.strip().lower()
    state["selected_agent"] = chosen_agent
    state["routing_rationale"] = f"LLM router selected: {chosen_agent}"
    
    return state

def _route_to_agent(self, state: LangGraphState) -> str:
    """Conditional edge function - returns which agent node to execute"""
    agent = state.get("selected_agent", "finance_qa")
    
    # Validate agent
    valid_agents = ["finance_qa", "portfolio", "market", "goal", "tax", "news"]
    if agent not in valid_agents:
        agent = "finance_qa"  # Fallback
    
    return agent
```

---

## ⚠️ ISSUE 2: Guardrails NOT Integrated into Orchestration

### Current State
- ✅ Guardrails implemented in `src/core/guardrails.py`
- ❌ NOT called in the orchestration workflow
- ❌ No input validation applied
- ❌ No output safety checks
- ❌ No rate limiting enforced

### Correct Implementation
```python
async def _node_input(self, state: LangGraphState) -> LangGraphState:
    """Input node with guardrails enforcement"""
    
    # APPLY GUARDRAILS BEFORE PROCESSING
    from src.core.guardrails import InputGuardrails, PII_Guardrails
    
    input_guardrails = InputGuardrails()
    pii_guardrails = PII_Guardrails()
    
    # Validate input
    is_valid, error = input_guardrails.validate_query(state["user_input"])
    if not is_valid:
        state["execution_errors"] = [f"Input validation failed: {error}"]
        state["final_response"] = "Your question doesn't meet safety requirements."
        state["confidence"] = 0.0
        return state
    
    # Check for PII
    pii_detected, pii_list = pii_guardrails.detect_pii(state["user_input"])
    if pii_detected:
        state["execution_errors"] = [f"PII detected: {pii_list}"]
        state["final_response"] = "Please don't include personal information."
        return state
    
    # Continue with normal flow
    state["conversation_history"].append({
        "role": "user",
        "content": state["user_input"],
        "timestamp": datetime.now().isoformat()
    })
    
    return state

async def _node_synthesis(self, state: LangGraphState) -> LangGraphState:
    """Synthesis node with OUTPUT guardrails"""
    
    from src.core.guardrails import OutputGuardrails, ComplianceGuardrails
    
    output_guardrails = OutputGuardrails()
    compliance_guardrails = ComplianceGuardrails()
    
    # Generate initial response
    from src.agents.finance_qa import FinanceQAAgent
    agent = FinanceQAAgent()
    output = await agent.execute(state["user_input"], None)
    
    # APPLY OUTPUT GUARDRAILS
    # 1. Safety check
    is_safe = output_guardrails.validate_response(output.answer_text)
    if not is_safe:
        state["final_response"] = "Response failed safety validation."
        state["confidence"] = 0.0
        return state
    
    # 2. Compliance check
    is_compliant = compliance_guardrails.check_financial_advice(
        output.answer_text,
        user_intent=state.get("primary_intent")
    )
    if not is_compliant:
        state["final_response"] += "\n⚠️ Disclaimer: This is not financial advice."
    
    # 3. PII in response
    pii_guardrails = PII_Guardrails()
    pii_detected, _ = pii_guardrails.detect_pii(output.answer_text)
    if pii_detected:
        state["final_response"] = "Generated response contained PII - redacted."
        return state
    
    state["final_response"] = output.answer_text
    state["citations"] = output.citations
    state["confidence"] = 0.85
    
    return state
```

---

## 📋 Summary of Issues

| Issue | Current | Should Be | Impact |
|-------|---------|-----------|--------|
| **Agent Nodes** | 1 node (broadcasts to all agents) | 6 individual nodes | No selective routing |
| **Router Logic** | Hardcoded intent→agent mapping | LLM-based routing | Inflexible, doesn't scale |
| **Guardrails** | Exist but unused | Applied at input/output | No safety enforcement |
| **Input Validation** | None | Applied before processing | ❌ Unsafe |
| **Output Safety** | None | Applied after synthesis | ❌ Unsafe responses |
| **PII Detection** | Exists but unused | Applied at input/output | ❌ Data leakage risk |
| **Rate Limiting** | Configured but unused | Applied per agent | ❌ No DoS protection |

---

## 🔧 How to Fix (Priority Order)

### Priority 1: Integrate Guardrails (Fast, High Impact)
```python
# In _node_input():
- Call InputGuardrails.validate_query()
- Call PII_Guardrails.detect_pii()

# In _node_synthesis():
- Call OutputGuardrails.validate_response()
- Call ComplianceGuardrails.check_financial_advice()
```

### Priority 2: Implement Router Agent (Medium, Proper Pattern)
- Add `_node_router()` that calls LLM
- Add individual agent nodes
- Update graph edges for conditional routing
- Remove broadcast pattern

### Priority 3: Add Rate Limiting (Low, Performance)
- Track requests per session
- Enforce AGENT_TIMEOUT_MS
- Enforce TOTAL_WORKFLOW_TIMEOUT_MS

---

## Files to Modify

1. **src/orchestration/langgraph_workflow.py**
   - Add router node
   - Add 6 individual agent nodes
   - Update graph edges
   - Integrate guardrails in _node_input() and _node_synthesis()

2. **src/orchestration/state.py**
   - Add "selected_agent": str (single agent, not list)

3. **src/core/guardrails.py**
   - Already complete, just needs to be called

---

## Why This Matters

✅ **Proper Router Pattern**: Classic LangGraph + LLM router pattern
✅ **True Conditional Routing**: Route to ONE best agent, not all agents  
✅ **Safety Enforcement**: Guardrails prevent unsafe input/output
✅ **PII Protection**: Detect and block personal information
✅ **Compliance**: Add disclaimers for financial advice
✅ **Scalable**: Easy to add more agents
