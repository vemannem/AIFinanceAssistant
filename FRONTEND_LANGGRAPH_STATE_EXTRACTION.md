# Frontend LangGraph State Data Extraction

## What LangGraph State Data Is Frontend Pulling?

---

## **FLOW DIAGRAM**

```
┌──────────────────────────────────────────────────────────────┐
│           LANGGRAPH STATE (Backend)                          │
│                                                              │
│  final_state = {                                            │
│    "primary_intent": "market_analysis",    ← STATE         │
│    "detected_intents": ["market_analysis"], ← STATE        │
│    "extracted_tickers": ["AAPL"],          ← STATE         │
│    "selected_agent": "market",             ← STATE         │
│    "selected_agents": ["market"],          ← STATE         │
│    "agent_executions": [                   ← STATE         │
│      {                                                      │
│        "agent": "market",                  ← STATE         │
│        "status": "success",                ← STATE         │
│        "execution_time_ms": 450.25,        ← STATE         │
│        "error": null                       ← STATE         │
│      }                                                      │
│    ],                                                       │
│    "execution_times": {                    ← STATE         │
│      "market": 450.25                      ← STATE         │
│    },                                                       │
│    "final_response": "Apple is...",        ← STATE         │
│    "confidence": 0.85,                     ← STATE         │
│    "citations": [...],                     ← STATE         │
│    "execution_errors": []                  ← STATE         │
│  }                                                          │
└──────────────────────────────────────────────────────────────┘
                          ↓
┌──────────────────────────────────────────────────────────────┐
│   orchestrator.execute() - Lines 730-766                     │
│   (langgraph_workflow.py)                                    │
│                                                              │
│   Returns:                                                   │
│   {                                                          │
│     "response": final_state.get("final_response"),          │
│     "citations": final_state.get("citations"),              │
│     "confidence": final_state.get("confidence"),            │
│     "intent": final_state.get("primary_intent"),   ← STATE  │
│     "agents_used": final_state.get("selected_agents"), ← STATE │
│     "execution_times": final_state.get("execution_times"), ← STATE │
│     "execution_details": [                         ← STATE  │
│       {                                                      │
│         "agent_name": "market",             ← FROM STATE   │
│         "status": "success",                ← FROM STATE   │
│         "execution_time_ms": 450.25,        ← FROM STATE   │
│         "error": null,                      ← FROM STATE   │
│         "has_output": true                  ← FROM STATE   │
│       }                                                      │
│     ],                                                       │
│     "workflow_state": {                     ← STATE DICT    │
│       "detected_intents": [...],            ← STATE        │
│       "primary_intent": "market_analysis",  ← STATE        │
│       "extracted_tickers": ["AAPL"],        ← STATE        │
│       "execution_errors": []                ← STATE        │
│     }                                                        │
│   }                                                          │
└──────────────────────────────────────────────────────────────┘
                          ↓
┌──────────────────────────────────────────────────────────────┐
│   chat.py - Packages into metadata                           │
│   Lines 160-180                                              │
│                                                              │
│   metadata = {                                               │
│     "agent": "langgraph_orchestrator",                       │
│     "tools_used": [...],                                     │
│     "workflow_state": "complete",                            │
│     "execution_details": result.get("execution_details"),   │
│     "workflow_analysis": result.get("workflow_state"),      │
│     "detected_intents": [...],          ← FROM STATE        │
│     "extracted_tickers": [...],         ← FROM STATE        │
│     "execution_errors": []              ← FROM STATE        │
│   }                                                          │
│                                                              │
│   ChatResponse(                                              │
│     ...                                                      │
│     metadata=metadata,       ← CONTAINS STATE DATA          │
│     confidence=confidence,                                   │
│     intent=intent,                                           │
│     agents_used=agents_used, ← FROM STATE                   │
│     execution_times=execution_times, ← FROM STATE           │
│     ...                                                      │
│   )                                                          │
└──────────────────────────────────────────────────────────────┘
                          ↓
                   HTTP Response
                          ↓
┌──────────────────────────────────────────────────────────────┐
│   FRONTEND RECEIVES RESPONSE                                 │
│   (useChat.ts - Line 61)                                     │
│                                                              │
│   const response = await orchestrationService.sendMessage(  │
│     text,                                                    │
│     store.sessionId,                                         │
│     conversationHistory                                      │
│   )                                                          │
│                                                              │
│   response = {                                               │
│     "session_id": "...",                                     │
│     "message": "Apple is trading at...",                     │
│     "citations": [...],                                      │
│     "timestamp": "...",                                      │
│     "metadata": {                        ← HAS STATE DATA    │
│       "execution_details": [...],        ← FROM STATE       │
│       "workflow_analysis": {             ← FROM STATE       │
│         "detected_intents": [...],       ← FROM STATE       │
│         "primary_intent": "market...",   ← FROM STATE       │
│         "extracted_tickers": [...],      ← FROM STATE       │
│         "execution_errors": []           ← FROM STATE       │
│       },                                                     │
│       "detected_intents": [...],         ← FROM STATE       │
│       "extracted_tickers": [...],        ← FROM STATE       │
│       "execution_errors": []             ← FROM STATE       │
│     },                                                       │
│     "confidence": 0.85,                                      │
│     "intent": "market_analysis",         ← FROM STATE       │
│     "agents_used": ["market"],           ← FROM STATE       │
│     "execution_times": {                 ← FROM STATE       │
│       "market": 450.25                   ← FROM STATE       │
│     },                                                       │
│     "total_time_ms": 550.0                                   │
│   }                                                          │
│                                                              │
│   console.log('Full Response:', response)                   │
│   console.log('ExecutionData:', executionData)              │
│   console.log('Metadata execution_details:', ...)           │
└──────────────────────────────────────────────────────────────┘
                          ↓
         useChat.ts EXTRACTS STATE DATA
         (Lines 67-80)
                          ↓
┌──────────────────────────────────────────────────────────────┐
│   WHAT FRONTEND EXTRACTS FROM RESPONSE                       │
│   (Lines 67-80 in useChat.ts)                               │
│                                                              │
│   Directly from response object:                             │
│   ├─ response.confidence           ← From state            │
│   ├─ response.intent               ← From state (primary_intent) │
│   ├─ response.agents_used          ← From state (selected_agents) │
│   ├─ response.execution_times      ← From state            │
│   ├─ response.total_time_ms        ← From state            │
│   └─ response.metadata             ← From state (nested)   │
│                                                              │
│   From response.metadata:                                    │
│   ├─ response.metadata.execution_details    ← From state    │
│   ├─ response.metadata.workflow_analysis    ← From state    │
│   ├─ response.metadata.detected_intents     ← From state    │
│   ├─ response.metadata.extracted_tickers    ← From state    │
│   └─ response.metadata.execution_errors     ← From state    │
│                                                              │
│   Creates executionData object:                              │
│   const executionData = {                                    │
│     confidence: response.confidence,                         │
│     intent: response.intent,                                 │
│     agentsUsed: response.agents_used,      ← STATE DATA     │
│     executionTimes: response.execution_times, ← STATE DATA  │
│     totalTimeMs: response.total_time_ms,                    │
│     metadata: response.metadata            ← STATE DATA     │
│   }                                                          │
│                                                              │
│   The metadata object contains:                              │
│   ├─ execution_details (FROM STATE)                          │
│   ├─ workflow_analysis (FROM STATE)                          │
│   ├─ detected_intents (FROM STATE)                           │
│   ├─ extracted_tickers (FROM STATE)                          │
│   └─ execution_errors (FROM STATE)                           │
└──────────────────────────────────────────────────────────────┘
                          ↓
┌──────────────────────────────────────────────────────────────┐
│   STORE MESSAGE WITH STATE DATA                              │
│   (Lines 81-100 in useChat.ts)                               │
│                                                              │
│   const assistantMessage: Message = {                        │
│     id: "msg-123",                                           │
│     text: "Apple is...",                                     │
│     sender: 'assistant',                                     │
│     timestamp: new Date(),                                   │
│     citations: response.citations,                           │
│     execution: executionData,  ← CONTAINS ALL STATE DATA    │
│     metadata: {                                              │
│       workflow_state: 'complete',                            │
│       confidence_score: response.confidence, ← STATE         │
│       agents_count: response.agents_used.length, ← STATE     │
│       error_messages: []                                     │
│     }                                                         │
│   }                                                          │
│                                                              │
│   store.addMessage(assistantMessage)                         │
└──────────────────────────────────────────────────────────────┘
                          ↓
┌──────────────────────────────────────────────────────────────┐
│   EXECUTION DETAILS COMPONENT RECEIVES STATE DATA            │
│   (ExecutionDetails.tsx)                                     │
│                                                              │
│   Receives props:                                            │
│   ├─ confidence: number              ← FROM STATE           │
│   ├─ intent: string                  ← FROM STATE           │
│   ├─ agentsUsed: string[]            ← FROM STATE           │
│   ├─ executionTimes: object          ← FROM STATE           │
│   ├─ totalTimeMs: number             ← FROM STATE           │
│   └─ metadata: {                                             │
│      ├─ execution_details: [...]     ← FROM STATE           │
│      ├─ workflow_analysis: {...}     ← FROM STATE           │
│      └─ ...other fields              ← FROM STATE           │
│    }                                                         │
│                                                              │
│   Uses state data in rendering:                              │
│   ├─ Has execution_details? → Show "Active" badge           │
│   ├─ Show agents: agentsUsed.length                          │
│   ├─ Show timing: executionTimes[agent]                      │
│   ├─ Show intents: metadata.workflow_analysis.detected_intents │
│   ├─ Show tickers: metadata.workflow_analysis.extracted_tickers │
│   ├─ Show agents report: metadata.execution_details          │
│   └─ Show timeline breakdown: executionTimes values          │
└──────────────────────────────────────────────────────────────┘
```

---

## **EXACT STATE DATA FIELDS PULLED TO FRONTEND**

### **From response object directly:**

```typescript
// useChat.ts Line 61-80
const response = await orchestrationService.sendMessage(...)

// EXTRACTED FROM STATE (via orchestrator.execute()):
const executionData = {
  confidence: response.confidence,              // ← state.confidence
  intent: response.intent,                      // ← state.primary_intent
  agentsUsed: response.agents_used,            // ← state.selected_agents
  executionTimes: response.execution_times,    // ← state.execution_times
  totalTimeMs: response.total_time_ms,         // ← calculated
  metadata: response.metadata                   // ← Contains state data
}
```

### **From response.metadata (nested state data):**

```typescript
// ExecutionDetails.tsx receives this metadata
response.metadata = {
  // Direct state fields
  "agent": "langgraph_orchestrator",
  "tools_used": [...],
  "workflow_state": "complete",
  
  // ← FROM LANGGRAPH STATE:
  "execution_details": [
    {
      "agent_name": "market",           // ← state.agent_executions[0].agent
      "status": "success",              // ← state.agent_executions[0].status
      "execution_time_ms": 450.25,      // ← state.agent_executions[0].execution_time_ms
      "error": null,                    // ← state.agent_executions[0].error
      "has_output": true                // ← from state.agent_executions[0].output
    }
  ],
  
  // ← FROM LANGGRAPH STATE:
  "workflow_analysis": {
    "detected_intents": ["market_analysis"],     // ← state.detected_intents
    "primary_intent": "market_analysis",         // ← state.primary_intent
    "extracted_tickers": ["AAPL"],              // ← state.extracted_tickers
    "execution_errors": []                       // ← state.execution_errors
  },
  
  // Duplicated for convenience:
  "detected_intents": ["market_analysis"],       // ← state.detected_intents
  "extracted_tickers": ["AAPL"],                // ← state.extracted_tickers
  "execution_errors": []                         // ← state.execution_errors
}
```

---

## **SPECIFIC STATE FIELDS PULLED**

| Frontend Variable | Source State Field | Purpose | Display Location |
|---|---|---|---|
| `response.intent` | `state.primary_intent` | Shows detected intent | Intent badge in header |
| `response.agents_used` | `state.selected_agents` | Shows which agents ran | "Agents Executed" section |
| `response.execution_times` | `state.execution_times` | Shows time per agent | Timeline & agent cards |
| `response.confidence` | `state.confidence` | Shows confidence score | Confidence badge & metric |
| `metadata.execution_details` | Built from `state.agent_executions` | Shows agent execution report | "Agent Execution Report" section |
| `metadata.workflow_analysis.detected_intents` | `state.detected_intents` | Shows detected intents | "Workflow Analysis" section |
| `metadata.workflow_analysis.extracted_tickers` | `state.extracted_tickers` | Shows extracted symbols | "Workflow Analysis" section |
| `metadata.workflow_analysis.execution_errors` | `state.execution_errors` | Shows any errors | Error display in workflow |
| `metadata.workflow_analysis.primary_intent` | `state.primary_intent` | Shows primary intent | Workflow analysis |

---

## **CODE TRACE: Where State Data Goes**

### **Step 1: State captured in LangGraph (backend)**
```python
# langgraph_workflow.py - Line 750+
state["selected_agents"] = ["market"]
state["execution_times"] = {"market": 450.25}
state["agent_executions"] = [{"agent": "market", "status": "success", ...}]
state["detected_intents"] = ["market_analysis"]
state["extracted_tickers"] = ["AAPL"]
state["primary_intent"] = "market_analysis"
state["execution_errors"] = []
```

### **Step 2: Packaged in execute() return (backend)**
```python
# langgraph_workflow.py - Line 750-766
return {
    "response": final_state.get("final_response"),
    "agents_used": final_state.get("selected_agents"),  ← STATE
    "execution_times": final_state.get("execution_times"),  ← STATE
    "execution_details": execution_report,  ← FROM STATE
    "workflow_state": {
        "detected_intents": final_state.get("detected_intents"),  ← STATE
        "extracted_tickers": final_state.get("extracted_tickers"),  ← STATE
        "execution_errors": final_state.get("execution_errors")  ← STATE
    }
}
```

### **Step 3: Packed into metadata (backend, chat.py)**
```python
# chat.py - Line 160-180
metadata = {
    "execution_details": result.get("execution_details"),  ← FROM STATE
    "workflow_analysis": result.get("workflow_state"),  ← FROM STATE
    "detected_intents": result.get("workflow_state", {}).get("detected_intents", []),  ← STATE
    "extracted_tickers": result.get("workflow_state", {}).get("extracted_tickers", []),  ← STATE
    "execution_errors": result.get("workflow_state", {}).get("execution_errors", [])  ← STATE
}

response = ChatResponse(
    metadata=metadata,  ← CONTAINS ALL STATE
    agents_used=agents_used,  ← STATE
    execution_times=execution_times,  ← STATE
    ...
)
```

### **Step 4: Extracted in frontend (useChat.ts)**
```typescript
// useChat.ts - Line 61-80
const response = await orchestrationService.sendMessage(...)

const executionData = {
    agentsUsed: response.agents_used,  ← FROM STATE (selected_agents)
    executionTimes: response.execution_times,  ← FROM STATE
    metadata: response.metadata,  ← FROM STATE DATA
}

console.log('Full Response:', response)  // Shows all state data
console.log('Metadata execution_details:', response.metadata?.execution_details)  // FROM STATE
```

### **Step 5: Passed to ExecutionDetails component**
```tsx
// useChat.ts - Line 81-100
const assistantMessage = {
    execution: executionData,  ← HAS STATE DATA
    ...
}

// Later in component rendering:
<ExecutionDetails
    agentsUsed={message.execution.agentsUsed}  ← FROM STATE
    executionTimes={message.execution.executionTimes}  ← FROM STATE
    metadata={message.execution.metadata}  ← FROM STATE
/>
```

### **Step 6: Displayed in ExecutionDetails component**
```tsx
// ExecutionDetails.tsx - Line 25-100+
const ExecutionDetails = ({
    agentsUsed = [],  // ["market"] ← FROM STATE
    executionTimes = {},  // {"market": 450.25} ← FROM STATE
    metadata = {}  // {execution_details, workflow_analysis} ← FROM STATE
}) => {
    
    // Render using state data:
    {agentsUsed.map(agent => (
        <div>{agent}: {executionTimes[agent]}ms</div>
        // Shows: market: 450.25ms ← FROM STATE
    ))}
    
    {metadata?.execution_details?.map(detail => (
        <div>{detail.agent_name}: {detail.status} ({detail.execution_time_ms}ms)</div>
        // Shows: market: success (450.25ms) ← FROM STATE
    ))}
    
    {metadata?.workflow_analysis?.detected_intents && (
        <div>Intents: {metadata.workflow_analysis.detected_intents}</div>
        // Shows: Intents: market_analysis ← FROM STATE
    )}
    
    {metadata?.workflow_analysis?.extracted_tickers && (
        <div>Tickers: {metadata.workflow_analysis.extracted_tickers}</div>
        // Shows: Tickers: AAPL ← FROM STATE
    )}
}
```

---

## **SUMMARY: What Frontend Pulls**

**Frontend pulls THESE LangGraph state fields:**

1. ✅ `selected_agents` → displays in "Agents Executed" section
2. ✅ `execution_times` → displays timing breakdown in timeline
3. ✅ `agent_executions` → displays in "Agent Execution Report" section
4. ✅ `detected_intents` → displays in "Workflow Analysis" section
5. ✅ `extracted_tickers` → displays in "Workflow Analysis" section
6. ✅ `primary_intent` → displays as intent badge
7. ✅ `execution_errors` → displays errors if any
8. ✅ `confidence` → displays confidence score
9. ✅ `final_response` → displays as chat message text

**How it flows:**
```
LangGraph State
    ↓
orchestrator.execute() returns state data
    ↓
chat.py packs into metadata
    ↓
ChatResponse sent to frontend
    ↓
useChat extracts: response.agents_used, response.execution_times, response.metadata
    ↓
ExecutionDetails component receives and displays all state data
    ↓
User sees: "Active" badge + all state information
```

**What you see in browser console:**
- `Full Response` shows all state data returned from backend
- `ExecutionData being set` shows extracted state data
- `Metadata execution_details` shows agent execution records from state

**What you see in UI:**
- Intent badge (from state.primary_intent)
- Agent count (from state.selected_agents.length)
- Agent timing (from state.execution_times)
- Agent execution report (from state.agent_executions)
- Intents/Tickers (from state.detected_intents, state.extracted_tickers)
- Confidence (from state.confidence)
