# Backend Orchestration Safety Guardrails - Finance Assistant

**Status**: Framework Document  
**Purpose**: Define safety boundaries for financial AI system  
**Scope**: Input validation, agent execution, response safety, user protection  

---

## 1. Input Validation Guardrails

### 1.1 Query Input Constraints

**Maximum Input Length**
```python
MAX_QUERY_LENGTH = 5000  # characters
MAX_CONVERSATION_HISTORY = 50  # messages
MAX_SESSION_DURATION = 8  # hours
```

**Validation Rules**
```python
def validate_user_input(user_input: str) -> Tuple[bool, str]:
    """Validate user input before processing"""
    
    # Length check
    if len(user_input) > MAX_QUERY_LENGTH:
        return False, "Query too long. Max 5000 characters."
    
    if len(user_input) < 3:
        return False, "Query too short. Provide at least 3 characters."
    
    # Character validation (allow alphanumeric, basic punctuation, symbols)
    if not re.match(r'^[a-zA-Z0-9\s\-\$\%\(\)\,\.\?\!]+$', user_input):
        return False, "Invalid characters in input."
    
    # Check for SQL injection patterns
    dangerous_patterns = ['DROP', 'DELETE', 'INSERT', 'UPDATE', 'SELECT']
    if any(pattern in user_input.upper() for pattern in dangerous_patterns):
        return False, "Query contains suspicious patterns."
    
    # Check for excessive punctuation/symbols
    special_char_ratio = sum(not c.isalnum() and c != ' ' for c in user_input) / len(user_input)
    if special_char_ratio > 0.3:  # More than 30% special chars
        return False, "Query has too many special characters."
    
    return True, ""
```

### 1.2 Data Extraction Safeguards

**Ticker Validation**
```python
VALID_TICKER_LENGTH = (1, 5)  # 1-5 characters
VALID_TICKERS = set()  # Load from NYSE/NASDAQ list

def validate_ticker(ticker: str) -> bool:
    """Only accept real stock tickers"""
    return (
        len(ticker) in range(*VALID_TICKER_LENGTH) and
        ticker.isalpha() and
        ticker in VALID_TICKERS  # Against known ticker list
    )
```

**Amount Validation**
```python
MIN_AMOUNT = 1.0          # Minimum valid amount
MAX_AMOUNT = 10_000_000   # $10M max per amount
MAX_PORTFOLIO_VALUE = 100_000_000  # $100M max portfolio

def validate_amount(amount: float) -> Tuple[bool, str]:
    """Validate financial amounts"""
    if amount < MIN_AMOUNT:
        return False, f"Amount too small (minimum: ${MIN_AMOUNT})"
    
    if amount > MAX_AMOUNT:
        return False, f"Amount exceeds maximum (${MAX_AMOUNT})"
    
    # Check for unrealistic values
    if amount > 1_000_000 and not explicit_confirmation:
        return False, "Large amounts require confirmation"
    
    return True, ""
```

**Timeframe Validation**
```python
MIN_YEARS = 1
MAX_YEARS = 50

def validate_timeframe(years: int) -> Tuple[bool, str]:
    """Validate financial planning timeframes"""
    if years < MIN_YEARS or years > MAX_YEARS:
        return False, f"Timeframe must be {MIN_YEARS}-{MAX_YEARS} years"
    
    return True, ""
```

---

## 2. Financial Data Safeguards

### 2.1 Portfolio Validation

```python
@dataclass
class PortfolioValidation:
    is_valid: bool
    warnings: List[str]
    errors: List[str]
    
def validate_portfolio(portfolio: Dict[str, float]) -> PortfolioValidation:
    """Comprehensive portfolio validation"""
    warnings = []
    errors = []
    
    # Check holdings count
    if len(portfolio) == 0:
        errors.append("Portfolio cannot be empty")
    
    if len(portfolio) > 100:
        errors.append("Portfolio exceeds maximum holdings (100)")
    
    # Check values
    total_value = sum(portfolio.values())
    
    if total_value > MAX_PORTFOLIO_VALUE:
        errors.append(f"Portfolio value exceeds ${MAX_PORTFOLIO_VALUE}")
    
    # Check for extreme concentrations
    for ticker, amount in portfolio.items():
        percentage = (amount / total_value) * 100
        
        if percentage > 95:
            warnings.append(f"{ticker} concentration {percentage:.1f}% - very high risk")
        
        if percentage > 99:
            errors.append(f"{ticker} is {percentage:.1f}% of portfolio - invalid")
    
    # Check for negative values
    for ticker, amount in portfolio.items():
        if amount < 0:
            errors.append(f"{ticker} has negative value")
    
    # Validate individual tickers
    for ticker in portfolio.keys():
        if not validate_ticker(ticker):
            errors.append(f"Invalid ticker: {ticker}")
    
    return PortfolioValidation(
        is_valid=len(errors) == 0,
        warnings=warnings,
        errors=errors
    )
```

### 2.2 Goal Validation

```python
def validate_financial_goal(goal: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """Validate financial planning goals"""
    errors = []
    
    target_amount = goal.get('target_amount', 0)
    current_amount = goal.get('current_amount', 0)
    years = goal.get('years', 0)
    
    # Check values
    if not 0 < target_amount <= MAX_AMOUNT:
        errors.append("Target amount invalid")
    
    if not 0 <= current_amount <= MAX_AMOUNT:
        errors.append("Current amount invalid")
    
    if not 1 <= years <= 50:
        errors.append("Timeframe invalid (1-50 years)")
    
    # Check feasibility
    if current_amount > target_amount:
        errors.append("Current amount exceeds target - goal already met")
    
    # Check for unrealistic growth expectations
    growth_rate = ((target_amount / current_amount) ** (1/years) - 1) * 100 if current_amount > 0 else 0
    
    if growth_rate > 50:  # More than 50% annual growth
        warnings.append(f"Goal requires {growth_rate:.1f}% annual growth - very ambitious")
    
    return len(errors) == 0, errors
```

---

## 3. Agent Execution Safeguards

### 3.1 Execution Limits

```python
@dataclass
class ExecutionLimits:
    # Timeouts
    AGENT_TIMEOUT_MS = 30_000        # 30 seconds per agent
    TOTAL_WORKFLOW_TIMEOUT_MS = 60_000  # 60 seconds total
    
    # Resource limits
    MAX_TOKENS_PER_AGENT = 2000      # Max tokens in response
    MAX_TOKENS_PER_SESSION = 50_000  # Max tokens per session
    
    # Cost limits
    MAX_API_CALLS_PER_HOUR = 100
    MAX_COST_PER_MONTH = 100.00      # $100/month limit
    
    # Concurrency
    MAX_PARALLEL_AGENTS = 3
    MAX_SESSIONS = 1000
```

### 3.2 Timeout & Resource Management

```python
async def execute_with_timeout(
    agent_type: AgentType,
    user_input: str,
    timeout_ms: int = 30_000
) -> Dict[str, Any]:
    """Execute agent with timeout protection"""
    
    try:
        # Set timeout
        result = await asyncio.wait_for(
            agent.execute(user_input),
            timeout=timeout_ms / 1000
        )
        
        return {
            "status": "success",
            "output": result,
            "execution_time_ms": elapsed_ms
        }
    
    except asyncio.TimeoutError:
        logger.warning(f"Agent {agent_type} timeout after {timeout_ms}ms")
        
        return {
            "status": "timeout",
            "error": f"Agent processing took too long (>{timeout_ms}ms)",
            "fallback_response": f"Sorry, the {agent_type} agent took too long to respond. Please try again."
        }
    
    except Exception as e:
        logger.error(f"Agent {agent_type} error: {str(e)}")
        
        return {
            "status": "error",
            "error": str(e),
            "fallback_response": "An error occurred. Please rephrase your question."
        }
```

### 3.3 Token Usage Tracking

```python
class TokenUsageTracker:
    """Track and enforce token limits"""
    
    def __init__(self):
        self.session_tokens: Dict[str, int] = {}
        self.monthly_tokens: Dict[str, int] = {}
    
    def check_token_budget(self, session_id: str, agent: AgentType) -> bool:
        """Verify token budget before execution"""
        
        session_used = self.session_tokens.get(session_id, 0)
        
        # Check session limit
        if session_used > MAX_TOKENS_PER_SESSION:
            return False, "Session token limit exceeded"
        
        # Check monthly limit
        month_key = datetime.now().strftime("%Y-%m")
        monthly_used = self.monthly_tokens.get(month_key, 0)
        
        if monthly_used > MAX_TOKENS_PER_MONTH:
            return False, "Monthly token limit exceeded"
        
        return True, ""
    
    def record_usage(self, session_id: str, tokens_used: int):
        """Record token usage"""
        self.session_tokens[session_id] = self.session_tokens.get(session_id, 0) + tokens_used
        
        month_key = datetime.now().strftime("%Y-%m")
        self.monthly_tokens[month_key] = self.monthly_tokens.get(month_key, 0) + tokens_used
```

---

## 4. Response Safety Guardrails

### 4.1 Financial Advice Disclaimers

```python
DISCLAIMERS = {
    "tax": """⚠️ **TAX DISCLAIMER**: This is educational information only, 
              not tax advice. Consult a qualified tax professional for your 
              specific situation.""",
    
    "investment": """⚠️ **INVESTMENT DISCLAIMER**: This analysis is for 
                     informational purposes only. Past performance doesn't 
                     guarantee future results. Consider your risk tolerance 
                     and financial goals.""",
    
    "goal_planning": """⚠️ **PLANNING DISCLAIMER**: These projections are 
                        estimates based on assumptions. Actual results may 
                        vary significantly.""",
    
    "general": """⚠️ **GENERAL DISCLAIMER**: Not financial advice. Consult 
                   a qualified financial advisor before making decisions."""
}

def add_appropriate_disclaimer(state: OrchestrationState) -> str:
    """Add disclaimer based on intent"""
    response = state.synthesized_response
    
    if Intent.TAX_QUESTION in state.detected_intents:
        response += f"\n\n{DISCLAIMERS['tax']}"
    
    elif Intent.INVESTMENT_PLAN in state.detected_intents:
        response += f"\n\n{DISCLAIMERS['investment']}"
    
    elif Intent.GOAL_PLANNING in state.detected_intents:
        response += f"\n\n{DISCLAIMERS['goal_planning']}"
    
    else:
        response += f"\n\n{DISCLAIMERS['general']}"
    
    return response
```

### 4.2 Confidence-Based Response Filtering

```python
def validate_response_confidence(state: OrchestrationState) -> Tuple[bool, str]:
    """Ensure high-confidence responses"""
    
    MINIMUM_CONFIDENCE = 0.6
    
    # Check primary agent confidence
    for execution in state.agent_executions:
        if execution.status == "success":
            output = execution.output
            if hasattr(output, 'confidence'):
                if output.confidence < MINIMUM_CONFIDENCE:
                    return False, (
                        "The system is not confident in its response. "
                        "Please rephrase your question more specifically."
                    )
    
    return True, ""
```

### 4.3 Hallucination Detection

```python
def detect_potential_hallucination(response: str, context: Dict[str, Any]) -> bool:
    """Detect suspicious patterns in responses"""
    
    warnings = []
    
    # Check for made-up ticker symbols
    extracted_tickers = re.findall(r'\b[A-Z]{2,5}\b', response)
    for ticker in extracted_tickers:
        if ticker not in context.get('valid_tickers', []):
            warnings.append(f"Response mentions unknown ticker: {ticker}")
    
    # Check for unrealistic returns
    return_patterns = re.findall(r'(\d+(?:\.\d{1,2})?)\%?\s*(?:return|growth)', response, re.IGNORECASE)
    for return_str in return_patterns:
        try:
            return_pct = float(return_str)
            if return_pct > 100:  # Over 100% annual return
                warnings.append(f"Unrealistic return mentioned: {return_pct}%")
        except ValueError:
            pass
    
    if warnings:
        logger.warning(f"Potential hallucinations detected: {warnings}")
        return True
    
    return False
```

---

## 5. User Data Protection

### 5.1 Session Management

```python
@dataclass
class SessionGuardrails:
    MAX_SESSION_LIFETIME = 28800  # 8 hours in seconds
    MAX_MESSAGES_PER_SESSION = 100
    ENCRYPTION_KEY = os.getenv("SESSION_ENCRYPTION_KEY")
    
    def validate_session(self, session_id: str, state: OrchestrationState) -> bool:
        """Validate session is still active and valid"""
        
        # Check conversation history size
        if len(state.conversation_history) > self.MAX_MESSAGES_PER_SESSION:
            return False  # Session too long
        
        # Check session age
        if state.session_start_time:
            age_seconds = (datetime.now() - state.session_start_time).total_seconds()
            if age_seconds > self.MAX_SESSION_LIFETIME:
                return False  # Session expired
        
        return True
```

### 5.2 Data Sanitization for Storage

```python
def sanitize_for_storage(state: OrchestrationState) -> Dict[str, Any]:
    """Remove sensitive data before logging/storage"""
    
    sanitized = {
        "session_id": state.session_id,
        "detected_intents": [i.value for i in state.detected_intents],
        "selected_agents": [a.value for a in state.selected_agents],
        "execution_times": state.execution_times,
        "workflow_state": state.workflow_state,
    }
    
    # DO NOT STORE:
    # - Actual portfolio amounts
    # - Specific financial goals
    # - Agent outputs with sensitive data
    # - User's full conversation
    
    return sanitized
```

### 5.3 PII Detection & Handling

```python
def detect_pii(text: str) -> List[str]:
    """Detect personally identifiable information"""
    
    pii_patterns = {
        "ssn": r'\d{3}-\d{2}-\d{4}',
        "email": r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
        "phone": r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',
        "credit_card": r'\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b',
        "bank_account": r'\b\d{10,12}\b',
    }
    
    detected_pii = []
    
    for pii_type, pattern in pii_patterns.items():
        if re.search(pattern, text):
            detected_pii.append(pii_type)
    
    return detected_pii

def handle_pii_detection(user_input: str) -> Tuple[bool, str]:
    """Handle PII in user input"""
    
    detected = detect_pii(user_input)
    
    if detected:
        return False, (
            f"Please don't include sensitive information like {', '.join(detected)}. "
            "They won't be needed for this analysis."
        )
    
    return True, ""
```

---

## 6. Business Logic Safeguards

### 6.1 Market Data Freshness

```python
class MarketDataValidator:
    """Ensure market data is current"""
    
    MAX_DATA_AGE_MINUTES = 30  # Market data not older than 30 min
    MARKET_HOURS = {
        "open": time(9, 30),
        "close": time(16, 0),
    }
    
    def is_market_hours(self) -> bool:
        """Check if market is currently open"""
        now = datetime.now()
        
        if now.weekday() >= 5:  # Weekend
            return False
        
        return self.MARKET_HOURS["open"] <= now.time() <= self.MARKET_HOURS["close"]
    
    def validate_data_freshness(self, data_timestamp: datetime) -> bool:
        """Check if market data is fresh"""
        
        age = datetime.now() - data_timestamp
        age_minutes = age.total_seconds() / 60
        
        if age_minutes > self.MAX_DATA_AGE_MINUTES:
            logger.warning(f"Market data is {age_minutes:.0f} minutes old")
            return False
        
        return True
```

### 6.2 Portfolio Sanity Checks

```python
def check_portfolio_sanity(portfolio: Dict[str, float]) -> List[str]:
    """Identify concerning portfolio patterns"""
    
    warnings = []
    total = sum(portfolio.values())
    
    # High concentration risk
    for ticker, amount in portfolio.items():
        pct = (amount / total) * 100
        if pct > 50:
            warnings.append(f"High concentration: {ticker} is {pct:.1f}% of portfolio")
        if pct > 80:
            warnings.append(f"EXTREME concentration: {ticker} is {pct:.1f}%")
    
    # All same sector (if data available)
    sectors = get_sectors(portfolio.keys())
    if len(set(sectors)) == 1:
        warnings.append("Entire portfolio in single sector - low diversification")
    
    # No bonds/fixed income (risky for some investors)
    bond_tickers = {'BND', 'AGG', 'TLT', 'LQD'}
    if not any(t in bond_tickers for t in portfolio.keys()):
        warnings.append("No fixed income - all equity portfolio")
    
    return warnings
```

---

## 7. Error Handling & Fallbacks

### 7.1 Graceful Degradation

```python
def get_fallback_response(intent: Intent, error: str) -> str:
    """Provide safe fallback responses"""
    
    fallbacks = {
        Intent.EDUCATION_QUESTION: 
            "I can help with financial education. Please ask a specific question "
            "about concepts like diversification, stocks, bonds, or investing.",
        
        Intent.PORTFOLIO_ANALYSIS:
            "I can help analyze portfolios. Please provide specific tickers "
            "(like AAPL, BND) and amounts to analyze.",
        
        Intent.MARKET_ANALYSIS:
            "I can help with market data. Please ask about specific stock prices "
            "or market conditions.",
        
        Intent.GOAL_PLANNING:
            "I can help with financial planning. Please specify your target amount, "
            "current savings, and timeline.",
        
        Intent.TAX_QUESTION:
            "I can provide tax education. Please ask a specific tax question. "
            "⚠️ Remember: consult a qualified tax professional for your situation.",
        
        Intent.UNKNOWN:
            "I'm a financial assistant. I can help with portfolio analysis, "
            "market research, financial planning, tax questions, and more. What would you like to know?",
    }
    
    return fallbacks.get(intent, fallbacks[Intent.UNKNOWN])
```

### 7.2 Error Severity Levels

```python
@dataclass
class ErrorSeverity:
    INFO = "info"      # Informational, no impact
    WARNING = "warning"  # Non-critical issue
    ERROR = "error"    # Function degraded
    CRITICAL = "critical"  # Service impacted
    
def categorize_error(error: Exception, context: str) -> str:
    """Categorize error severity"""
    
    if isinstance(error, TimeoutError):
        return ErrorSeverity.WARNING
    
    elif isinstance(error, ValueError):
        return ErrorSeverity.INFO
    
    elif isinstance(error, ConnectionError):
        return ErrorSeverity.ERROR
    
    else:
        return ErrorSeverity.WARNING

def should_continue_workflow(severity: str) -> bool:
    """Determine if workflow should continue"""
    return severity in [ErrorSeverity.INFO, ErrorSeverity.WARNING]
```

---

## 8. Rate Limiting & DDoS Protection

### 8.1 Per-User Rate Limiting

```python
class RateLimiter:
    """Prevent abuse and excessive usage"""
    
    LIMITS = {
        "queries_per_minute": 10,
        "queries_per_hour": 100,
        "queries_per_day": 500,
    }
    
    def __init__(self):
        self.user_requests: Dict[str, List[datetime]] = {}
    
    def is_allowed(self, user_id: str) -> bool:
        """Check if user is within rate limits"""
        
        now = datetime.now()
        one_minute_ago = now - timedelta(minutes=1)
        one_hour_ago = now - timedelta(hours=1)
        one_day_ago = now - timedelta(days=1)
        
        # Initialize user if needed
        if user_id not in self.user_requests:
            self.user_requests[user_id] = []
        
        requests = self.user_requests[user_id]
        
        # Filter old requests
        requests = [r for r in requests if r > one_day_ago]
        
        # Count requests in each window
        minute_count = sum(1 for r in requests if r > one_minute_ago)
        hour_count = sum(1 for r in requests if r > one_hour_ago)
        day_count = len(requests)
        
        # Check limits
        if minute_count >= self.LIMITS["queries_per_minute"]:
            return False, f"Rate limit: max {self.LIMITS['queries_per_minute']} queries/minute"
        
        if hour_count >= self.LIMITS["queries_per_hour"]:
            return False, f"Rate limit: max {self.LIMITS['queries_per_hour']} queries/hour"
        
        if day_count >= self.LIMITS["queries_per_day"]:
            return False, f"Rate limit: max {self.LIMITS['queries_per_day']} queries/day"
        
        # Record this request
        self.user_requests[user_id] = requests + [now]
        
        return True, ""
```

---

## 9. Audit & Compliance Logging

### 9.1 Audit Trail

```python
@dataclass
class AuditLog:
    timestamp: datetime
    session_id: str
    user_id: str
    action: str  # "query", "error", "agent_execution"
    severity: str
    input_hash: str  # Hash of input (not stored)
    agents_used: List[str]
    success: bool
    error_code: Optional[str] = None

def create_audit_log(state: OrchestrationState, user_id: str) -> AuditLog:
    """Create audit trail entry"""
    
    return AuditLog(
        timestamp=datetime.now(),
        session_id=state.session_id,
        user_id=user_id,
        action="orchestration",
        severity="info" if not state.has_errors() else "warning",
        input_hash=hashlib.sha256(state.user_input.encode()).hexdigest(),
        agents_used=[a.value for a in state.selected_agents],
        success=not state.has_errors()
    )
```

---

## 10. Integration Checklist

### Before Phase 3 Frontend Launch

- [ ] Input validation implemented for all entry points
- [ ] Financial data validation enforced
- [ ] Agent execution timeouts configured
- [ ] Token usage tracking enabled
- [ ] Disclaimers added to all responses
- [ ] Confidence scoring enforced
- [ ] Session management implemented
- [ ] PII detection active
- [ ] Rate limiting deployed
- [ ] Audit logging configured
- [ ] Error fallbacks tested
- [ ] Market data freshness checks enabled
- [ ] Portfolio sanity checks active
- [ ] All guardrails documented

---

## 11. Guardrails Configuration File

Create `config/guardrails.py`:

```python
"""
Safety guardrails configuration for finance assistant
"""

class Guardrails:
    # Input constraints
    MAX_QUERY_LENGTH = 5000
    MIN_QUERY_LENGTH = 3
    
    # Financial limits
    MIN_AMOUNT = 1.0
    MAX_AMOUNT = 10_000_000
    MAX_PORTFOLIO_VALUE = 100_000_000
    MIN_YEARS = 1
    MAX_YEARS = 50
    
    # Agent execution
    AGENT_TIMEOUT_MS = 30_000
    TOTAL_WORKFLOW_TIMEOUT_MS = 60_000
    MAX_PARALLEL_AGENTS = 3
    
    # Token limits
    MAX_TOKENS_PER_AGENT = 2000
    MAX_TOKENS_PER_SESSION = 50_000
    
    # Rate limiting
    QUERIES_PER_MINUTE = 10
    QUERIES_PER_HOUR = 100
    QUERIES_PER_DAY = 500
    
    # Confidence thresholds
    MIN_RESPONSE_CONFIDENCE = 0.6
    
    # Data freshness
    MAX_MARKET_DATA_AGE_MINUTES = 30
    
    # Session management
    MAX_SESSION_LIFETIME_SECONDS = 28800  # 8 hours
    MAX_MESSAGES_PER_SESSION = 100
```

---

## Summary

### Critical Guardrails (Must Have)

1. ✅ Input validation & length limits
2. ✅ Financial data validation (amounts, tickers, timeframes)
3. ✅ Agent execution timeouts
4. ✅ Token usage tracking
5. ✅ Financial advice disclaimers
6. ✅ PII detection and prevention
7. ✅ Rate limiting per user
8. ✅ Error handling and fallbacks
9. ✅ Audit logging
10. ✅ Market data freshness checks

### Implementation Priority

**Phase 3 Must-Have**:
- Input validation
- Financial data validation
- Disclaimers
- Timeouts
- Error handling

**Phase 3 Nice-to-Have**:
- Token tracking
- Detailed audit logs
- Advanced hallucination detection
- Machine learning-based abuse detection

**Post-Phase 3**:
- Advanced security features
- Regulatory compliance (SOX, FINRA)
- Advanced ML-based fraud detection
- Blockchain audit trail

This comprehensive guardrails framework ensures the finance assistant is safe, reliable, and trustworthy for users.
