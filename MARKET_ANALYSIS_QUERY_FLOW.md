# Market Analysis Query Flow - Complete Walkthrough

## Scenario: User asks "What is the current price of Apple (AAPL)?"

---

## **STEP 1: FRONTEND - User Sends Message**

### File: `frontend/src/hooks/useChat.ts`

```typescript
// User types in chat input and hits send
const sendMessage = async (text: string) => {
  // text = "What is the current price of Apple (AAPL)?"
  
  // 1. Prepare conversation history (WITHOUT current message)
  const conversationHistory = store.messages.map(msg => ({
    role: msg.sender as 'user' | 'assistant',
    content: msg.text,
  }))
  // This is the PREVIOUS conversation, not including the current question
  
  // 2. Add user message to display
  const userMessage: Message = {
    id: "msg-001",
    text: "What is the current price of Apple (AAPL)?",
    sender: 'user',
    timestamp: new Date(),
  }
  store.addMessage(userMessage)
  
  // 3. Call backend API
  const response = await orchestrationService.sendMessage(
    "What is the current price of Apple (AAPL)?",  // message
    "session-xyz",                                   // session_id
    conversationHistory                              // conversation history WITHOUT current message
  )
  
  // Response received from backend
  console.log('Full Response:', response)
}
```

**Network Request:**
```
POST /chat/orchestration HTTP/1.1
Content-Type: application/json

{
  "message": "What is the current price of Apple (AAPL)?",
  "session_id": "session-xyz",
  "conversation_history": []  // Empty if first message
}
```

---

## **STEP 2: BACKEND - Orchestration Endpoint**

### File: `src/web_app/routes/chat.py`

```python
@router.post("/chat/orchestration")
async def orchestration_chat(request: OrchestrationRequest) -> ChatResponse:
    session_id = "session-xyz"
    
    # Get LangGraph orchestrator
    orchestrator = get_langgraph_orchestrator()
    
    # Execute orchestration workflow
    result = await orchestrator.execute(
        user_input="What is the current price of Apple (AAPL)?",
        session_id="session-xyz",
        conversation_history=[]
    )
    
    # result contains ALL LangGraph state data
    print("Orchestrator result:", result)
    
    # Extract metrics from result
    message = result.get("response")
    intent = result.get("intent")
    confidence = result.get("confidence")
    agents_used = result.get("agents_used")
    execution_times = result.get("execution_times")
    
    # ... more extraction ...
```

---

## **STEP 3: LANGGRAPH EXECUTION - Complete State Flow**

### File: `src/orchestration/langgraph_workflow.py`

```python
class LangGraphOrchestrator:
    async def execute(self, user_input, session_id, conversation_history):
        """
        Executes: START → input → intent → router → market agent → synthesis → END
        """
        
        # Initialize state
        initial_state = {
            "user_input": "What is the current price of Apple (AAPL)?",
            "session_id": "session-xyz",
            "conversation_history": [],
            "detected_intents": [],
            "primary_intent": "unknown",
            "selected_agent": "",
            "selected_agents": [],
            "extracted_tickers": [],
            "agent_executions": [],
            "execution_errors": [],
            "execution_times": {},
            "final_response": "",
        }
        
        # ═══════════════════════════════════════════════════════════════
        # NODE 1: INPUT NODE
        # ═══════════════════════════════════════════════════════════════
        async def _node_input(state):
            logger.info("[INPUT] Processing: 'What is the current price of Apple (AAPL)?'")
            
            state["input_validated"] = True  # Passes guardrails
            state["pii_detected"] = False    # No PII detected
            state["workflow_started_at"] = datetime.now().isoformat()
            state["conversation_history"].append({
                "role": "user",
                "content": "What is the current price of Apple (AAPL)?",
                "timestamp": datetime.now().isoformat()
            })
            
            logger.info("[INPUT] ✓ State initialized | Session: session-xyz")
            return state
        
        state = await _node_input(initial_state)
        # OUTPUT STATE:
        # {
        #   "user_input": "What is the current price of Apple (AAPL)?",
        #   "input_validated": True,
        #   "pii_detected": False,
        #   "workflow_started_at": "2026-01-26T10:30:45.123456",
        #   ...
        # }
        
        # ═══════════════════════════════════════════════════════════════
        # NODE 2: INTENT DETECTION NODE
        # ═══════════════════════════════════════════════════════════════
        async def _node_intent_detection(state):
            logger.info("[INTENT] Starting intent detection...")
            
            # Intent detector analyzes the query
            intents_result = self.intent_detector.detect_intents(
                query="What is the current price of Apple (AAPL)?"
            )
            # Returns: {
            #   "primary_intent": "market_analysis",
            #   "detected_intents": ["market_analysis"],
            #   "confidence": 0.95,
            #   "tickers": ["AAPL"]
            # }
            
            state["primary_intent"] = "market_analysis"  ← INTENT DETECTED!
            state["detected_intents"] = ["market_analysis"]
            state["confidence_score"] = 0.95
            state["extracted_tickers"] = ["AAPL"]  ← TICKER EXTRACTED!
            
            logger.info("[INTENT] ✓ Intent: market_analysis | Tickers: ['AAPL'] | Confidence: 0.95")
            return state
        
        state = await _node_intent_detection(state)
        # OUTPUT STATE:
        # {
        #   "primary_intent": "market_analysis",  ← KEY!
        #   "detected_intents": ["market_analysis"],  ← KEY!
        #   "extracted_tickers": ["AAPL"],  ← KEY!
        #   "confidence_score": 0.95,
        #   ...
        # }
        
        # ═══════════════════════════════════════════════════════════════
        # NODE 3: ROUTER NODE - LLM SELECTS AGENT
        # ═══════════════════════════════════════════════════════════════
        async def _node_router(state):
            logger.info("[ROUTER] Starting router...")
            
            # Build router prompt with detected intent
            router_prompt = f"""
            Intent: {state.get('primary_intent')}  # "market_analysis"
            Tickers: {state.get('extracted_tickers')}  # ["AAPL"]
            
            Based on the intent, which agent should handle this?
            Options: finance_qa, portfolio, market, goal, tax, news
            
            Response: (just the agent name)
            """
            
            # Call OpenAI LLM router
            response = await client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": router_prompt}],
                temperature=0.2,
                max_tokens=20
            )
            
            selected = response.choices[0].message.content.strip().lower()
            # LLM returns: "market"  ← ROUTING DECISION!
            
            logger.info(f"[ROUTER] LLM response: '{selected}' | Intent: market_analysis | Tickers: ['AAPL']")
            
            state["selected_agent"] = "market"  ← SELECTED!
            state["selected_agents"] = ["market"]  ← SELECTED!
            state["routing_rationale"] = "LLM router selected: market | Intent: market_analysis"
            
            logger.info("[ROUTER] ✓ Selected agent: market")
            return state
        
        state = await _node_router(state)
        # OUTPUT STATE:
        # {
        #   "selected_agent": "market",  ← KEY!
        #   "selected_agents": ["market"],  ← KEY!
        #   "routing_rationale": "LLM router selected: market | Intent: market_analysis",
        #   ...
        # }
        
        # ═══════════════════════════════════════════════════════════════
        # CONDITIONAL ROUTING: router → agent_market
        # ═══════════════════════════════════════════════════════════════
        # The router node determined selected_agent = "market"
        # The conditional edge routes to the "market" agent node
        
        # ═══════════════════════════════════════════════════════════════
        # NODE 4: MARKET AGENT NODE
        # ═══════════════════════════════════════════════════════════════
        async def _node_agent_market(state):
            """Execute Market Analysis agent"""
            logger.info("[AGENT_MARKET] Starting execution...")
            
            try:
                # Execute market analysis agent
                execution_result = await self.agent_executor.execute_agent(
                    agent_type=AgentType.MARKET_ANALYSIS,
                    user_input="What is the current price of Apple (AAPL)?",
                    context={
                        "tickers": ["AAPL"],  ← PASSED TO AGENT!
                        "conversation_history": [],
                    }
                )
                # Agent executes and returns:
                # {
                #   "status": "success",
                #   "output": AgentOutput(
                #     answer_text="Apple (AAPL) is currently trading at $245.32...",
                #     citations=[...],
                #     tool_calls_made=[...]
                #   ),
                #   "error": None,
                #   "execution_time_ms": 450.25
                # }
                
                # Record execution in state
                execution_record = {
                    "agent": "market",
                    "status": "success",
                    "output": execution_result.get("output"),
                    "error": None,
                    "execution_time_ms": 450.25
                }
                
                state["agent_executions"].append(execution_record)  ← RECORDED!
                state["execution_times"]["market"] = 450.25  ← RECORDED!
                state["selected_agents"].append("market")
                
                logger.info("[AGENT_MARKET] ✓ Completed in 450.25ms")
                logger.debug(f"[AGENT_MARKET] Total agents executed: {len(state.get('agent_executions', []))}")
                
            except Exception as e:
                logger.error(f"[AGENT_MARKET] ✗ Exception: {str(e)}")
                state["execution_errors"].append(f"market: {str(e)}")
            
            return state
        
        state = await _node_agent_market(state)
        # OUTPUT STATE:
        # {
        #   "agent_executions": [
        #     {
        #       "agent": "market",
        #       "status": "success",
        #       "output": AgentOutput(...),  ← AGENT OUTPUT!
        #       "error": None,
        #       "execution_time_ms": 450.25
        #     }
        #   ],
        #   "execution_times": {"market": 450.25},  ← TIMING!
        #   "selected_agents": ["market"],  ← CONFIRMED!
        #   ...
        # }
        
        # ═══════════════════════════════════════════════════════════════
        # NODE 5: SYNTHESIS NODE
        # ═══════════════════════════════════════════════════════════════
        async def _node_synthesis(state):
            logger.info("[SYNTHESIS] Synthesizing final response with guardrails...")
            logger.debug(f"[SYNTHESIS] State received with {len(state.get('agent_executions', []))} agent executions")
            
            # We have agent executions
            agent_executions = state.get("agent_executions", [])
            
            if agent_executions and agent_executions[0].get("status") == "success":
                # Use the market agent's output
                agent_output = agent_executions[0].get("output")
                # agent_output is an AgentOutput object with answer_text
                response_text = agent_output.answer_text
                # "Apple (AAPL) is currently trading at $245.32..."
                
                citations = agent_output.citations
            
            # Apply guardrails
            pii_detector = PIIDetector()
            pii_detected, pii_types = pii_detector.detect(response_text)
            # No PII detected (just stock price, not sensitive)
            
            # Add disclaimers for financial content
            disclaimer_manager = DisclaimerManager()
            response_text = disclaimer_manager.add_disclaimers(
                response_text,
                state.get("detected_intents", [])
            )
            
            state["final_response"] = response_text  ← FINAL RESPONSE!
            state["citations"] = citations
            state["confidence"] = 0.85
            
            # Add metadata
            state["metadata"]["agents_used"] = state.get("selected_agents", [])
            state["metadata"]["intent"] = state.get("primary_intent")
            state["metadata"]["execution_summary"] = {
                "total_agents": len(state.get("selected_agents", [])),
                "errors": len(state.get("execution_errors", []))
            }
            
            logger.info("[SYNTHESIS] ✓ Response synthesized")
            logger.info(f"[SYNTHESIS] Agent executions in state: {len(state.get('agent_executions', []))}")
            
            return state
        
        state = await _node_synthesis(state)
        # OUTPUT STATE:
        # {
        #   "final_response": "Apple (AAPL) is currently trading at $245.32...",  ← KEY!
        #   "citations": [...],  ← KEY!
        #   "confidence": 0.85,  ← KEY!
        #   "agent_executions": [
        #     {
        #       "agent": "market",
        #       "status": "success",
        #       "execution_time_ms": 450.25
        #     }
        #   ],  ← STILL IN STATE!
        #   ...
        # }
        
        # ═══════════════════════════════════════════════════════════════
        # GRAPH REACHES END STATE
        # ═══════════════════════════════════════════════════════════════
        
        # ═══════════════════════════════════════════════════════════════
        # PREPARE RETURN OBJECT WITH ALL STATE DATA
        # ═══════════════════════════════════════════════════════════════
        
        # Calculate total execution time
        final_state = state  # The state after all nodes executed
        total_time = ... # Calculate from timestamps
        
        # Build execution report from state
        execution_report = []
        for execution in final_state.get("agent_executions", []):
            execution_report.append({
                "agent_name": execution.get("agent"),
                "status": execution.get("status"),
                "execution_time_ms": execution.get("execution_time_ms"),
                "error": execution.get("error"),
                "has_output": bool(execution.get("output"))
            })
        # execution_report = [
        #   {
        #     "agent_name": "market",
        #     "status": "success",
        #     "execution_time_ms": 450.25,
        #     "error": None,
        #     "has_output": True
        #   }
        # ]
        
        # Return comprehensive result
        return {
            "response": final_state.get("final_response"),
            # "Apple (AAPL) is currently trading at $245.32..."
            
            "citations": final_state.get("citations"),
            "confidence": final_state.get("confidence"),  # 0.85
            "intent": final_state.get("primary_intent"),  # "market_analysis"
            "agents_used": final_state.get("selected_agents"),  # ["market"]  ← FROM STATE!
            "execution_times": final_state.get("execution_times"),
            # {"market": 450.25}  ← FROM STATE!
            
            "total_time_ms": total_time,
            "session_id": final_state.get("session_id"),
            "metadata": final_state.get("metadata"),
            
            # ← KEY: Return execution details from state
            "execution_details": execution_report,
            # [
            #   {
            #     "agent_name": "market",
            #     "status": "success",
            #     "execution_time_ms": 450.25,
            #     "error": None,
            #     "has_output": True
            #   }
            # ]
            
            # ← KEY: Return workflow state details
            "workflow_state": {
                "detected_intents": final_state.get("detected_intents"),
                # ["market_analysis"]  ← FROM STATE!
                
                "primary_intent": final_state.get("primary_intent"),
                # "market_analysis"  ← FROM STATE!
                
                "extracted_tickers": final_state.get("extracted_tickers"),
                # ["AAPL"]  ← FROM STATE!
                
                "execution_errors": final_state.get("execution_errors")
                # []  ← FROM STATE!
            }
        }
```

---

## **STEP 4: BACKEND - Package Response for Frontend**

### File: `src/web_app/routes/chat.py`

```python
# The orchestrator.execute() returns the comprehensive result
result = await orchestrator.execute(
    user_input="What is the current price of Apple (AAPL)?",
    session_id="session-xyz",
    conversation_history=[]
)

# Extract all metrics
message = result.get("response")
# "Apple (AAPL) is currently trading at $245.32..."

intent = result.get("intent")
# "market_analysis"

confidence = result.get("confidence")
# 0.85

agents_used = result.get("agents_used")
# ["market"]  ← FROM LANGGRAPH STATE!

execution_times = result.get("execution_times")
# {"market": 450.25}  ← FROM LANGGRAPH STATE!

citations = result.get("citations")
# [...]

# ══════════════════════════════════════════════════════════════════
# BUILD METADATA WITH STATE DATA
# ══════════════════════════════════════════════════════════════════

metadata = {
    "agent": "langgraph_orchestrator",
    "tools_used": result.get("metadata", {}).get("tools_used", []),
    "workflow_state": "complete",
    
    # ← KEY: Include execution details from LangGraph state
    "execution_details": result.get("execution_details", []),
    # [
    #   {
    #     "agent_name": "market",
    #     "status": "success",
    #     "execution_time_ms": 450.25,
    #     "error": None,
    #     "has_output": True
    #   }
    # ]
    
    # ← KEY: Include workflow analysis from LangGraph state
    "workflow_analysis": result.get("workflow_state", {}),
    # {
    #   "detected_intents": ["market_analysis"],
    #   "primary_intent": "market_analysis",
    #   "extracted_tickers": ["AAPL"],
    #   "execution_errors": []
    # }
    
    "detected_intents": result.get("workflow_state", {}).get("detected_intents", []),
    # ["market_analysis"]  ← FROM STATE!
    
    "extracted_tickers": result.get("workflow_state", {}).get("extracted_tickers", []),
    # ["AAPL"]  ← FROM STATE!
    
    "execution_errors": result.get("workflow_state", {}).get("execution_errors", []),
    # []  ← FROM STATE!
}

logger.info(f"Metadata execution_details: {metadata.get('execution_details', [])}")
logger.info(f"Metadata workflow_analysis: {metadata.get('workflow_analysis', {})}")

# Build ChatResponse
response = ChatResponse(
    session_id="session-xyz",
    message=message,
    citations=citations,
    timestamp=datetime.utcnow().isoformat(),
    metadata=metadata,  ← CONTAINS ALL STATE DATA!
    confidence=confidence,
    intent=intent,
    agents_used=agents_used,  ← FROM STATE!
    execution_times=execution_times,  ← FROM STATE!
    total_time_ms=total_time,
)

return response
```

**HTTP Response to Frontend:**
```json
{
  "session_id": "session-xyz",
  "message": "Apple (AAPL) is currently trading at $245.32...",
  "citations": [...],
  "timestamp": "2026-01-26T10:30:50.123456",
  "confidence": 0.85,
  "intent": "market_analysis",
  "agents_used": ["market"],
  "execution_times": {"market": 450.25},
  "total_time_ms": 550.0,
  "metadata": {
    "agent": "langgraph_orchestrator",
    "workflow_state": "complete",
    "execution_details": [
      {
        "agent_name": "market",
        "status": "success",
        "execution_time_ms": 450.25,
        "error": null,
        "has_output": true
      }
    ],
    "workflow_analysis": {
      "detected_intents": ["market_analysis"],
      "primary_intent": "market_analysis",
      "extracted_tickers": ["AAPL"],
      "execution_errors": []
    },
    "detected_intents": ["market_analysis"],
    "extracted_tickers": ["AAPL"],
    "execution_errors": []
  }
}
```

---

## **STEP 5: FRONTEND - Receive and Display Response**

### File: `frontend/src/hooks/useChat.ts`

```typescript
// Receive response from backend
const response = await orchestrationService.sendMessage(
  "What is the current price of Apple (AAPL)?",
  "session-xyz",
  []
)

// Response object:
// {
//   "message": "Apple (AAPL) is currently trading at $245.32...",
//   "confidence": 0.85,
//   "intent": "market_analysis",
//   "agents_used": ["market"],  ← FROM LANGGRAPH STATE!
//   "execution_times": {"market": 450.25},  ← FROM LANGGRAPH STATE!
//   "total_time_ms": 550.0,
//   "metadata": {
//     "execution_details": [...],  ← FROM LANGGRAPH STATE!
//     "workflow_analysis": {...}  ← FROM LANGGRAPH STATE!
//   }
// }

console.log('Full Response:', response)
// Logs entire response including all state data

console.log('Metadata execution_details:', response.metadata?.execution_details)
// Logs: [
//   {
//     "agent_name": "market",
//     "status": "success",
//     "execution_time_ms": 450.25,
//     "error": null,
//     "has_output": true
//   }
// ]

// Create execution data object with all state information
const executionData = {
  confidence: response.confidence,  // 0.85
  intent: response.intent,  // "market_analysis"
  agentsUsed: response.agents_used,  // ["market"]  ← FROM STATE!
  executionTimes: response.execution_times,  // {"market": 450.25}  ← FROM STATE!
  totalTimeMs: response.total_time_ms,  // 550.0
  metadata: response.metadata,  // HAS execution_details and workflow_analysis ← STATE!
}

console.log('ExecutionData being set:', executionData)

// Create assistant message with execution data
const assistantMessage: Message = {
  id: "msg-002",
  text: "Apple (AAPL) is currently trading at $245.32...",
  sender: 'assistant',
  timestamp: new Date(),
  citations: response.citations,
  execution: executionData,  ← CONTAINS ALL STATE DATA!
  metadata: {
    workflow_state: 'complete',
    confidence_score: 0.85,
    agents_count: 1,  ← FROM STATE!
    error_messages: [],
  },
}

// Add to chat store
store.addMessage(assistantMessage)
```

---

## **STEP 6: FRONTEND - Render in Chat Component**

### File: `frontend/src/components/Chat/ChatMessage.tsx`

```tsx
// Render the assistant message
<div className="message assistant-message">
  <div className="message-content">
    {/* Display the response text */}
    <p>{message.text}</p>
    {/* "Apple (AAPL) is currently trading at $245.32..." */}
    
    {/* Display citations */}
    {message.citations && message.citations.length > 0 && (
      <div className="citations">
        {message.citations.map(c => (
          <a href={c.url} key={c.id}>{c.title}</a>
        ))}
      </div>
    )}
  </div>
  
  {/* ← KEY: Pass execution data to ExecutionDetails component */}
  {message.execution && (
    <ExecutionDetails
      confidence={message.execution.confidence}  // 0.85
      intent={message.execution.intent}  // "market_analysis"
      agentsUsed={message.execution.agentsUsed}  // ["market"]  ← FROM STATE!
      executionTimes={message.execution.executionTimes}  // {"market": 450.25}  ← FROM STATE!
      totalTimeMs={message.execution.totalTimeMs}  // 550.0
      metadata={message.execution.metadata}  // ← HAS STATE DATA!
    />
  )}
</div>
```

---

## **STEP 7: EXECUTION DETAILS COMPONENT - Display State Data**

### File: `frontend/src/components/Chat/ExecutionDetails.tsx`

```tsx
const ExecutionDetails: React.FC<ExecutionDetailsProps> = ({
  confidence = 0.85,
  intent = "market_analysis",
  agentsUsed = ["market"],  // ← FROM LANGGRAPH STATE!
  executionTimes = {"market": 450.25},  // ← FROM LANGGRAPH STATE!
  totalTimeMs = 550.0,
  metadata = {
    execution_details: [  // ← FROM LANGGRAPH STATE!
      {
        agent_name: "market",
        status: "success",
        execution_time_ms: 450.25,
        error: null,
        has_output: true
      }
    ],
    workflow_analysis: {  // ← FROM LANGGRAPH STATE!
      detected_intents: ["market_analysis"],
      primary_intent: "market_analysis",
      extracted_tickers: ["AAPL"],
      execution_errors: []
    }
  }
}) => {
  const [isExpanded, setIsExpanded] = useState(false)
  
  // Check if execution data exists
  const hasExecutionDetails = metadata?.execution_details?.length > 0
  const hasWorkflowAnalysis = metadata?.workflow_analysis && Object.keys(metadata.workflow_analysis).length > 0
  
  return (
    <div className="execution-details">
      {/* Header with Active Badge */}
      <button onClick={() => setIsExpanded(!isExpanded)}>
        <span>Execution Details</span>
        
        {/* ← Active badge shows when state data is present */}
        {(hasExecutionDetails || hasWorkflowAnalysis) && (
          <span className="badge active">Active</span>
        )}
        
        <div className="badges">
          <span className="confidence-badge">Confidence: 85%</span>
          <span className="intent-badge">market analysis</span>
        </div>
        
        {isExpanded ? <ChevronUp /> : <ChevronDown />}
      </button>
      
      {/* Expanded Content */}
      {isExpanded && (
        <div className="details-content">
          
          {/* Quick Stats */}
          <div className="quick-stats">
            <div className="stat">
              <Clock size={16} />
              <span>Total Time</span>
              <strong>550ms</strong>
            </div>
            <div className="stat">
              <CheckCircle size={16} />
              <span>Agents</span>
              <strong>1</strong>  {/* From agentsUsed.length ← FROM STATE */}
            </div>
            <div className="stat">
              <Zap size={16} />
              <span>Confidence</span>
              <strong>85%</strong>
            </div>
            <div className="stat">
              <AlertCircle size={16} />
              <span>Intent</span>
              <strong>market analysis</strong>
            </div>
          </div>
          
          {/* Agents Executed - From STATE */}
          <section className="agents-executed">
            <h4>Agents Executed</h4>
            <div className="agent-list">
              {agentsUsed.map((agent, idx) => (
                <div key={idx} className="agent-card">
                  <CheckCircle size={16} className="success-icon" />
                  <div>
                    <p className="agent-name">Market Analysis</p>
                    <p className="agent-time">
                      {formatTime(executionTimes[agent])}
                      {/* 450ms ← FROM STATE */}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          </section>
          
          {/* Agent Execution Report - From LANGGRAPH STATE */}
          {metadata?.execution_details && metadata.execution_details.length > 0 && (
            <section className="agent-execution-report">
              <h4>Agent Execution Report</h4>
              <div className="execution-list">
                {metadata.execution_details.map((detail, idx) => (
                  <div key={idx} className="execution-item">
                    <div className="status-icon">
                      {detail.status === 'success' ? (
                        <CheckCircle className="success" />
                      ) : (
                        <AlertCircle className="error" />
                      )}
                    </div>
                    <div className="detail-info">
                      <p className="agent-name">
                        {detail.agent_name}  {/* "market" ← FROM STATE */}
                      </p>
                      {detail.error && (
                        <p className="error-text">{detail.error}</p>
                      )}
                    </div>
                    <div className="detail-time">
                      <p className="time">
                        {formatTime(detail.execution_time_ms)}
                        {/* "450ms" ← FROM STATE */}
                      </p>
                      <p className="status">{detail.status}</p>
                      {/* "success" ← FROM STATE */}
                    </div>
                  </div>
                ))}
              </div>
            </section>
          )}
          
          {/* Workflow Analysis - From LANGGRAPH STATE */}
          {metadata?.workflow_analysis && (
            <section className="workflow-analysis">
              <h4>Workflow Analysis</h4>
              <div className="analysis-content">
                {metadata.workflow_analysis.detected_intents?.length > 0 && (
                  <div className="analysis-item">
                    <span className="label">Detected Intents:</span>
                    <span className="value">
                      {metadata.workflow_analysis.detected_intents.join(', ')}
                      {/* "market_analysis" ← FROM STATE */}
                    </span>
                  </div>
                )}
                
                {metadata.workflow_analysis.extracted_tickers?.length > 0 && (
                  <div className="analysis-item">
                    <span className="label">Tickers:</span>
                    <span className="value">
                      {metadata.workflow_analysis.extracted_tickers.join(', ')}
                      {/* "AAPL" ← FROM STATE */}
                    </span>
                  </div>
                )}
                
                {metadata.workflow_analysis.execution_errors?.length > 0 && (
                  <div className="analysis-item error">
                    <span className="label">Errors:</span>
                    <span className="value">
                      {metadata.workflow_analysis.execution_errors.join(', ')}
                    </span>
                  </div>
                )}
              </div>
            </section>
          )}
          
          {/* Execution Timeline - From STATE */}
          {Object.keys(executionTimes).length > 0 && (
            <section className="execution-timeline">
              <h4>Execution Timeline</h4>
              <div className="timeline">
                <div className="timeline-item">
                  <span>Input Processing & Intent Detection</span>
                  <span className="time">{formatTime(otherTime / 2)}</span>
                </div>
                
                {Object.entries(executionTimes).map(([agent, time]) => (
                  <div key={agent} className="timeline-item">
                    <span>
                      {agent.replace(/_/g, ' ')}  {/* "market" ← FROM STATE */}
                    </span>
                    <span className="time">
                      {formatTime(time)}  {/* "450ms" ← FROM STATE */}
                    </span>
                  </div>
                ))}
                
                <div className="timeline-item">
                  <span>Response Synthesis & Formatting</span>
                  <span className="time">{formatTime(otherTime / 2)}</span>
                </div>
                
                <div className="timeline-total">
                  <strong>Total Execution Time</strong>
                  <strong className="time">
                    {formatTime(totalTimeMs)}  {/* "550ms" ← FROM STATE */}
                  </strong>
                </div>
              </div>
            </section>
          )}
          
          {/* Performance Metrics */}
          {totalTimeMs > 0 && (
            <section className="performance">
              <h4>Performance</h4>
              <div className="metrics">
                <div className="metric">
                  <span>Response Latency</span>
                  <span className="value good">
                    {formatTime(totalTimeMs)}  {/* "550ms" - shows "Excellent" */}
                  </span>
                </div>
                
                {agentsUsed.length > 1 && (
                  <div className="metric">
                    <span>Parallel Efficiency</span>
                    <span className="value">
                      {agentsUsed.length}x agents  {/* "1x agents" ← FROM STATE */}
                    </span>
                  </div>
                )}
                
                <div className="metric">
                  <span>Response Confidence</span>
                  <div className="confidence-bar">
                    <div className="fill" style={{width: '85%'}}></div>
                  </div>
                  <span>85%</span>
                </div>
              </div>
            </section>
          )}
          
        </div>
      )}
    </div>
  )
}
```

---

## **FINAL DISPLAY IN CHAT UI**

```
┌─────────────────────────────────────────────────────────┐
│                                                         │
│  Q: What is the current price of Apple (AAPL)?        │
│                                                         │
│  A: Apple (AAPL) is currently trading at $245.32      │
│     [Source Citation Link]                             │
│                                                         │
│  ┌─ Execution Details [Active] ✓ ─────────────────┐   │
│  │ Confidence: 85%  │  Intent: market analysis     │   │
│  │                                                 │   │
│  │ 📊 Quick Stats                                  │   │
│  │ ├─ Total Time: 550ms                            │   │
│  │ ├─ Agents: 1 ← FROM STATE                       │   │
│  │ ├─ Confidence: 85%                              │   │
│  │ └─ Intent: market analysis                      │   │
│  │                                                 │   │
│  │ 🤖 Agents Executed ← FROM STATE                 │   │
│  │ ├─ ✓ Market Analysis: 450ms ← FROM STATE       │   │
│  │                                                 │   │
│  │ 📋 Agent Execution Report ← FROM STATE          │   │
│  │ ├─ ✓ market (status: success)                   │   │
│  │ │   └─ 450ms                                    │   │
│  │                                                 │   │
│  │ 🔍 Workflow Analysis ← FROM STATE               │   │
│  │ ├─ Detected Intents: market_analysis ← STATE   │   │
│  │ ├─ Tickers: AAPL ← STATE                        │   │
│  │ └─ Errors: (none)                               │   │
│  │                                                 │   │
│  │ ⏱️  Execution Timeline ← FROM STATE              │   │
│  │ ├─ Input Processing: 50ms                       │   │
│  │ ├─ market agent: 450ms ← STATE                  │   │
│  │ ├─ Synthesis: 50ms                              │   │
│  │ └─ Total: 550ms ← STATE                         │   │
│  │                                                 │   │
│  │ 📈 Performance                                  │   │
│  │ ├─ Response Latency: 550ms (Excellent)         │   │
│  │ ├─ Agents: 1x (from 1 executed) ← STATE        │   │
│  │ └─ Confidence: [████████░░░] 85% ← STATE       │   │
│  │                                                 │   │
│  └─────────────────────────────────────────────────┘   │
│                                                         │
│  💡 This execution details view is powered by         │
│     LangGraph StateGraph for transparent workflow      │
│     execution tracking.                               │
│                                                         │
└─────────────────────────────────────────────────────────┘

Browser Console:
└─ Full Response: {
     message: "Apple (AAPL) is currently trading at $245.32..."
     confidence: 0.85
     intent: "market_analysis"
     agents_used: ["market"]  ← FROM STATE
     execution_times: {"market": 450.25}  ← FROM STATE
     total_time_ms: 550.0
     metadata: {
       execution_details: [
         {
           agent_name: "market"  ← FROM STATE
           status: "success"  ← FROM STATE
           execution_time_ms: 450.25  ← FROM STATE
           error: null  ← FROM STATE
           has_output: true  ← FROM STATE
         }
       ]
       workflow_analysis: {
         detected_intents: ["market_analysis"]  ← FROM STATE
         primary_intent: "market_analysis"  ← FROM STATE
         extracted_tickers: ["AAPL"]  ← FROM STATE
         execution_errors: []  ← FROM STATE
       }
     }
   }

└─ ExecutionData being set: {
     confidence: 0.85
     intent: "market_analysis"
     agentsUsed: ["market"]  ← FROM STATE
     executionTimes: {"market": 450.25}  ← FROM STATE
     totalTimeMs: 550.0
     metadata: {
       execution_details: [...]  ← FROM STATE
       workflow_analysis: {...}  ← FROM STATE
     }
   }

└─ Metadata execution_details: [
     {
       agent_name: "market"  ← FROM STATE
       status: "success"  ← FROM STATE
       execution_time_ms: 450.25  ← FROM STATE
       error: null
       has_output: true
     }
   ]
```

---

## **Summary: Market Analysis Query Journey**

| Step | What Happens | State Data Used/Created | Display Location |
|------|---|---|---|
| **1. Frontend** | User sends "What is the current price of Apple (AAPL)?" | Session ID, message | Chat input |
| **2. Backend** | Orchestration endpoint receives request | Initializes state | API endpoint |
| **3. Input Node** | Validates input, prepares state | `workflow_started_at`, `conversation_history` | Internal |
| **4. Intent Node** | Detects "market_analysis" intent, extracts "AAPL" ticker | `primary_intent`, `detected_intents`, `extracted_tickers` | Internal → will display |
| **5. Router Node** | LLM selects "market" agent based on intent | `selected_agent`, `selected_agents` | Internal → will display |
| **6. Market Agent Node** | Executes market analysis, fetches AAPL price, gets 450ms | `agent_executions`, `execution_times` | Will display in Agent Execution Report |
| **7. Synthesis Node** | Combines output, applies guardrails, formats response | `final_response`, `citations`, `confidence` | Chat message text + citations |
| **8. Return to Backend** | `execute()` returns execution_details + workflow_state | ALL STATE DATA packaged | metadata object |
| **9. Chat Endpoint** | Packages into metadata | `execution_details`, `workflow_analysis` | HTTP response |
| **10. Frontend Hook** | Receives response, extracts execution data | All state fields | Console logs |
| **11. Chat Store** | Adds message with execution data | execution object with metadata | Message object |
| **12. ExecutionDetails** | Renders all sections using state data | All fields for display | Execution Details card |
| **13. User Sees** | Response + "Active" badge + complete metrics | All LangGraph state visible | Chat UI |

**Key Points:**
- ✅ **Router correctly selected "market" agent** (conditional routing worked)
- ✅ **Market agent executed and fetched real data** (450ms execution)
- ✅ **Intent detected: "market_analysis"** (visible in Workflow Analysis)
- ✅ **Ticker extracted: "AAPL"** (visible in Workflow Analysis)
- ✅ **All state data returned to frontend** (execution_details + workflow_analysis)
- ✅ **ExecutionDetails component displays everything** (Active badge + all sections)
- ✅ **Console shows complete response** (for debugging)
