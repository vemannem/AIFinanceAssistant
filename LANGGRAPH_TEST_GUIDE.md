## 🧪 TEST GUIDE: Goal Planning → LangGraph State Display

### Prerequisites
- Backend running: `python -m uvicorn src.web_app:app --host 0.0.0.0 --port 8000`
- Frontend running: `npm run dev` (should be on http://localhost:5173)
- Both services accessible

### Step-by-Step Test

#### 1. **Open Frontend in Browser**
   - Go to: http://localhost:5173/
   - Should see the AI Finance Assistant interface

#### 2. **Navigate to Goal Planning Tab**
   - Click on **"Goals"** tab in the main navigation

#### 3. **Fill Goal Planning Form**
   ```
   - Current Value: 50000
   - Goal Amount: 100000
   - Time Horizon: 5 years
   - Risk Appetite: Moderate
   - Expected Annual Return: 6.0%
   ```

#### 4. **Click "Plan Goal" Button**
   - Button shows "Planning..." while processing
   - **Expected**: LangGraph State tab shows a **loading indicator with progress bar**
   - Message: "Processing your request... LangGraph is executing agents and collecting metrics"
   - This takes 10-30 seconds

#### 5. **Wait for Response**
   - Backend is processing (calling agents + LLM synthesis)
   - **Expected**: Goal Planning tab shows the result with:
     - Detailed plan metrics
     - Monthly savings needed
     - Projected value
     - Investment calculations

#### 6. **Check LangGraph State Tab**
   - Click on **"LangGraph State"** tab
   - **Expected**: Should see execution metrics:
     ```
     ✓ Confidence: 0.85
     ✓ Intent: goal_planning
     ✓ Agents Executed: goal_planning, portfolio_analysis
     ✓ Execution Times: {timing data}
     ✓ Total Time: 13-15 seconds
     ```

### What You Should See

**During Processing (Loading State):**
```
⏳ Processing your request...
LangGraph is executing agents and collecting metrics
[=====>_____] This may take 10-30 seconds...
```

**After Completion (Metrics Display):**
```
📊 LangGraph Execution State

⚡ Quick Stats
├─ Total Execution: 13.08s
├─ Agents Executed: 2
├─ Confidence: 0.85
└─ Primary Intent: goal_planning

📋 Intent Analysis
├─ Detected Intent: goal_planning
├─ Confidence Score: 0.85
└─ Supporting Details...

⏱️ Execution Timeline
├─ goal_planning: 0.1ms
├─ portfolio_analysis: 0.0ms
└─ synthesis: 12s
```

### Troubleshooting

**If you see "No Execution Data":**
1. Check browser console (F12) for errors
2. Verify backend is returning metrics:
   ```bash
   curl -X POST http://localhost:8000/api/agents/goal-planning \
     -H "Content-Type: application/json" \
     -d '{"current_value":50000,"goal_amount":100000,"time_horizon_years":5,"risk_appetite":"moderate","current_return":6.0}'
   ```
   Response should include: `confidence`, `intent`, `agents_used`, `execution_times`, `total_time_ms`

**If loading doesn't show:**
1. Hard refresh browser: `Cmd+Shift+R` (Mac) or `Ctrl+Shift+R` (Windows)
2. Check if backend is running on port 8000
3. Verify frontend rebuilt successfully

**If metrics don't appear after loading:**
1. Check browser console for JavaScript errors
2. Verify langgraphStore is being updated
3. Check that GoalPlanningView is calling `langgraphStore.setExecution()`

### Key Components Updated

1. **langgraphStore** (frontend/src/store/langgraphStore.ts)
   - Tracks last LangGraph execution
   - Independent of chat messages
   - Has `lastExecution` and `loading` state

2. **GoalPlanningView** (frontend/src/components/Goals/GoalPlanningView.tsx)
   - Sets `langgraphStore.setLoading(true)` when starting
   - Calls `langgraphStore.setExecution()` when goal planning completes
   - Clears loading state in finally block

3. **LangGraphStateTab** (frontend/src/components/LangGraphStateTab.tsx)
   - Reads from `langgraphStore.lastExecution`
   - Shows progress bar during loading
   - Displays metrics when available

### Expected Response Time
- **Total**: 13-30 seconds
  - Agent execution: ~100ms
  - LLM synthesis: ~10-20 seconds
  - Response formatting: ~100ms

### Success Criteria ✅
- [ ] Form fills without errors
- [ ] "Plan Goal" button shows loading state
- [ ] LangGraph State tab shows "Processing your request..." with progress bar
- [ ] After 15-30 seconds, metrics appear
- [ ] Metrics show correct values (confidence, intent, agents_used, total_time_ms)
- [ ] Goal Planning tab shows the actual goal plan data
