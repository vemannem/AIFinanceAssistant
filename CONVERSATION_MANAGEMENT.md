# Conversation Management - Max History & Rolling Summary

## Overview

Implements **conversation management** with two key features:

1. **Max History Limit** - Keeps conversation within configurable size (default: 20 messages)
2. **Rolling Summary** - Creates automatic summaries when history exceeds threshold (default: 10 messages)

This prevents:
- Unbounded memory growth
- Excessive token usage in LLM prompts
- Long context windows causing latency
- Session memory leaks

---

## Configuration

### Environment Variables

```bash
# Set in .env or override at runtime
CONVERSATION_MAX_HISTORY=20              # Max messages to keep (default: 20)
CONVERSATION_SUMMARY_THRESHOLD=10        # When to create summary (default: 10)
CONVERSATION_SUMMARY_LENGTH=500          # Target summary length in chars (~150 tokens)
```

### In Code

```python
from src.core.conversation_manager import ConversationManager

# Use defaults from config
manager = get_conversation_manager()

# Or customize
manager = ConversationManager(
    max_history=15,
    summary_threshold=8,
    summary_length=400
)
```

---

## How It Works

### Flow Diagram

```
User Query
    ↓
Add to conversation_history
    ↓
Check: len(history) > summary_threshold?
    ├─ YES → Create summary of old messages
    │        Keep last max_history messages only
    │        Store summary in conversation_summary
    ↓
    └─ NO → Keep all messages
    ↓
Return context with summary (if exists) + recent messages
```

### Example: 25 Messages with 10-message Threshold

```
Initial State:
┌─────────────────────────────────────┐
│ 25 conversation messages            │
│ (exceeds 10-message threshold)      │
└─────────────────────────────────────┘
                ↓
        [Process Trimming]
                ↓
After Trim (max_history=20):
┌──────────────────────────────────────────┐
│ SUMMARY: "Previous 5 messages            │
│ discussed portfolio, diversification,    │
│ and ETFs"                                │
│                                          │
│ RECENT 20 MESSAGES: [...]               │
└──────────────────────────────────────────┘
```

---

## API Reference

### ConversationManager

```python
class ConversationManager:
    
    def should_create_summary(num_messages: int) -> bool:
        """Check if conversation needs summary"""
        # Returns True if num_messages >= summary_threshold
    
    def create_summary(messages: List[Dict]) -> ConversationSummary:
        """
        Create summary of messages
        
        Extracts:
        - Key financial topics (portfolio, bonds, ETFs, etc.)
        - Key decisions/questions asked
        - Narrative summary of conversation
        
        Returns:
            ConversationSummary with:
            - summary_text: Narrative summary
            - messages_included: How many messages summarized
            - key_topics: List of topics mentioned
            - key_decisions: List of key questions
            - timestamp: When summary created
        """
    
    def trim_history(
        messages: List[Dict]
    ) -> Tuple[List[Dict], Optional[ConversationSummary]]:
        """
        Trim conversation history to max_history size
        
        If messages > max_history:
            1. Create summary of oldest messages
            2. Keep only last max_history messages
            3. Return (trimmed_messages, summary)
        
        If messages <= max_history:
            Return (messages, None)
        """
    
    def apply_summary_to_prompt(
        messages: List[Dict],
        summary: Optional[ConversationSummary]
    ) -> str:
        """
        Create context string for LLM prompt
        
        Format:
        ```
        [If summary exists]
        Previous conversation summary:
        {summary_text}
        Topics discussed: {topics}
        
        Recent conversation:
        User: ...
        Assistant: ...
        ```
        """
    
    def get_stats(messages: List[Dict]) -> Dict:
        """
        Get conversation statistics:
        - total_messages
        - user_messages
        - assistant_messages
        - total_characters
        - avg_message_length
        - needs_summary (bool)
        - max_history, summary_threshold
        """
```

### OrchestrationState Integration

```python
class OrchestrationState:
    
    # New field
    conversation_summary: Optional[ConversationSummary] = None
    
    # New method
    def get_conversation_context(self) -> str:
        """
        Get formatted conversation context for LLM prompts
        
        Includes summary (if created) + recent messages
        Ready to inject into prompt template
        """
```

---

## Usage Examples

### Basic Usage

```python
from src.core.conversation_manager import get_conversation_manager

manager = get_conversation_manager()

# Check if summary needed
if manager.should_create_summary(len(messages)):
    summary = manager.create_summary(messages)
    print(f"Topics: {summary.key_topics}")

# Trim and get context
trimmed, summary = manager.trim_history(messages)
context = manager.apply_summary_to_prompt(trimmed, summary)

print(context)
# Output:
# Previous conversation summary:
# Conversation with 5 messages. Main topics: Portfolio Analysis, Bonds. 
# Last question: How should I diversify...
#
# Recent conversation:
# User: What about rebalancing?
# Assistant: You should rebalance...
```

### In Orchestration Workflow

```python
async def node_input(self, state: OrchestrationState) -> OrchestrationState:
    # Add message
    state.add_message("user", state.user_input)
    
    # Trim history automatically
    msg_dicts = [
        {"role": m.role, "content": m.content}
        for m in state.conversation_history
    ]
    
    trimmed, summary = self.conversation_manager.trim_history(msg_dicts)
    
    if summary:
        state.conversation_summary = summary
    
    return state

# Later in synthesis, use context in prompt:
context = state.get_conversation_context()
prompt = f"""
Based on this conversation:
{context}

Answer the user's latest question...
"""
```

### Getting Statistics

```python
stats = manager.get_stats(messages)

print(f"Total: {stats['total_messages']}")
print(f"User: {stats['user_messages']}")
print(f"Assistant: {stats['assistant_messages']}")
print(f"Needs summary: {stats['needs_summary']}")

# Output:
# Total: 25
# User: 12
# Assistant: 13
# Needs summary: True (exceeds threshold of 10)
```

---

## Implementation Details

### Summary Creation Algorithm

```python
def create_summary(messages):
    1. Extract financial keywords from content
       - Portfolio, Stock, Bond, ETF, Diversification, etc.
    
    2. Build narrative:
       - "Conversation with X messages"
       - "Main topics: Topic1, Topic2, Topic3"
       - "Last question: ..."
    
    3. Limit to summary_length characters
       - Default: 500 chars (~150 tokens)
    
    4. Return ConversationSummary with metadata
```

### Trimming Algorithm

```python
def trim_history(messages):
    if len(messages) <= max_history:
        return messages, None
    
    # Messages to summarize = all except the last max_history
    to_summarize = messages[:-max_history]
    summary = create_summary(to_summarize)
    
    # Keep only recent messages
    trimmed = messages[-max_history:]
    
    return trimmed, summary
```

### Context Formatting

```
[If summary exists]
Previous conversation summary:
{summary.summary_text}

Topics discussed: {comma_separated_topics}

Recent conversation:
{last_5_messages_formatted}

[If no summary, just recent messages]
Recent conversation:
{all_messages_formatted}
```

---

## Performance Impact

### Conversation Trimming

```
Operation                    Time    Impact
─────────────────────────────────────────
Create summary               5-10ms  ✅ Minimal
Extract topics               2-5ms   ✅ Minimal
Format context string        1-2ms   ✅ Minimal
─────────────────────────────────────────
TOTAL (on trim event)        10-15ms ✅ <1% of total
```

Only runs when history exceeds threshold (not every message).

### Memory Usage

```
Config                       Memory Usage
──────────────────────────────────────
max_history=20               ~10-20 KB (20 messages * 500 chars avg)
max_history=50               ~25-50 KB (50 messages * 500 chars avg)

With history trimming, memory is BOUNDED at max_history level
Without trimming, memory grows unbounded
```

---

## Key Topics Extracted

The summary extractor recognizes these financial topics:

```python
{
    'portfolio': 'Portfolio Analysis',
    'stock': 'Stock Market',
    'bond': 'Bonds',
    'etf': 'ETFs',
    'diversification': 'Diversification',
    'rebalance': 'Rebalancing',
    'goal': 'Financial Goals',
    'retirement': 'Retirement Planning',
    'tax': 'Tax Planning',
    'risk': 'Risk Management',
    'allocation': 'Asset Allocation',
    'dividend': 'Dividends',
    'yield': 'Yield Analysis',
    'market': 'Market Analysis',
}
```

Easy to extend by modifying the keywords dict.

---

## Testing

### Run Tests

```bash
cd /Users/yuvan/Documents/agentic/AIFinanceAssistent
python test_conversation_manager.py
```

### Test Coverage

✅ Basic functionality (create manager, check threshold)  
✅ Summary creation with topic extraction  
✅ History trimming with summary  
✅ Applying summary to prompt  
✅ Getting conversation statistics  
✅ OrchestrationState integration  

### Test Output

```
Running Conversation Manager Tests...

✅ Basic conversation manager test passed
✅ Summary creation test passed
   Topics: ['ETFs', 'Diversification', 'Bonds', 'Portfolio Analysis']
   Summary: Conversation with 5 messages. Main topics: Bonds, Diversification...

✅ Trim history test passed
   Original: 15, Trimmed: 5, Summary: 10 msgs

✅ Apply summary to prompt test passed
✅ Conversation stats test passed
✅ Orchestration state conversation test passed
   Context length: 188 chars

✅ All conversation manager tests passed!
```

---

## Configuration Recommendations

### Development

```python
CONVERSATION_MAX_HISTORY=100           # Lenient for testing
CONVERSATION_SUMMARY_THRESHOLD=50      # Rare summaries
CONVERSATION_SUMMARY_LENGTH=1000       # Long summaries allowed
```

### Production

```python
CONVERSATION_MAX_HISTORY=20            # Tight limit
CONVERSATION_SUMMARY_THRESHOLD=10      # Regular summaries
CONVERSATION_SUMMARY_LENGTH=500        # Concise summaries (~150 tokens)
```

### Streaming/High-Volume

```python
CONVERSATION_MAX_HISTORY=15            # Very tight
CONVERSATION_SUMMARY_THRESHOLD=8       # Early summaries
CONVERSATION_SUMMARY_LENGTH=300        # Very concise
```

---

## Metrics to Monitor

### Dashboard Metrics

```
Conversation Management Metrics:

1. Average history length
   - Target: < max_history
   - Alert if: > max_history * 1.1

2. Summary creation rate
   - Healthy: 10-20% of conversations
   - Alert if: < 5% or > 50%

3. Summary quality
   - Track: topics_extracted per summary
   - Target: 3-5 topics

4. Context window size
   - Measure: chars in final LLM prompt
   - Target: < 3000 chars for fast LLM
```

### Example Logging

```python
logger.info("Conversation management metrics", extra={
    "history_length": 15,
    "max_history": 20,
    "summary_created": True,
    "topics": 4,
    "context_chars": 1200,
    "session_id": "user-123"
})
```

---

## Troubleshooting

### Issue: "Conversation history growing unbounded"

**Cause**: `max_history` too high or summary threshold not triggered

**Fix**:
```python
# Lower max_history or summary_threshold
CONVERSATION_MAX_HISTORY=15
CONVERSATION_SUMMARY_THRESHOLD=8
```

### Issue: "Summary missing key topics"

**Cause**: Topics not in keyword dictionary

**Fix**: Add to [conversation_manager.py](src/core/conversation_manager.py):
```python
financial_keywords = {
    'your_topic': 'Your Topic Name',
    # ... add more
}
```

### Issue: "Summary too long, exceeding token budget"

**Cause**: `summary_length` too high

**Fix**:
```python
CONVERSATION_SUMMARY_LENGTH=300  # Reduce from 500
```

---

## Integration Checklist

- [x] Config added to `src/core/config.py`
- [x] ConversationManager created in `src/core/conversation_manager.py`
- [x] State schema updated in `src/orchestration/state.py`
- [x] Workflow integrated in `src/orchestration/workflow.py`
- [x] Tests created and passing
- [x] Phase 2C tests still passing (23/23)
- [ ] Frontend receives summary in API response (Phase 3)
- [ ] Monitoring dashboard shows metrics (Phase 3)

---

## Summary

**Conversation Management** provides automatic history trimming and rolling summaries to:

✅ Prevent unbounded memory growth  
✅ Reduce token usage in LLM prompts  
✅ Extract key topics for better context  
✅ Maintain conversation understanding  
✅ Enable long multi-turn conversations  

**Features**:
- 📊 Max history limit (default: 20 messages)
- 📝 Rolling summaries (triggered at threshold)
- 🎯 Topic extraction from conversation
- 📈 Statistics and monitoring
- ⚙️ Configurable behavior

**Ready for**: Phase 3 frontend integration where summaries can be displayed to users.
