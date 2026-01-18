"""
Safety Guardrails Implementation

Production-ready safety checks for finance assistant orchestration.
Handles input validation, resource limits, compliance, and error handling.
"""

import re
import asyncio
import hashlib
from datetime import datetime, timedelta
from typing import Tuple, List, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum

from src.core.logger import get_logger


logger = get_logger(__name__)


class ErrorSeverity(str, Enum):
    """Error severity levels"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


# ============================================================================
# CONFIGURATION
# ============================================================================

class GuardrailsConfig:
    """Centralized guardrails configuration"""
    
    # Input constraints
    MAX_QUERY_LENGTH = 5000
    MIN_QUERY_LENGTH = 3
    
    # Financial limits
    MIN_AMOUNT = 1.0
    MAX_AMOUNT = 10_000_000  # $10M
    MAX_PORTFOLIO_VALUE = 100_000_000  # $100M
    MIN_YEARS = 1
    MAX_YEARS = 50
    
    # Agent execution
    AGENT_TIMEOUT_MS = 30_000  # 30 seconds
    TOTAL_WORKFLOW_TIMEOUT_MS = 60_000  # 60 seconds
    MAX_PARALLEL_AGENTS = 3
    
    # Token limits
    MAX_TOKENS_PER_AGENT = 2000
    MAX_TOKENS_PER_SESSION = 50_000
    MAX_TOKENS_PER_MONTH = 1_000_000
    
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
    
    # Portfolio constraints
    MAX_CONCENTRATION_WARNING = 50  # 50% in single position
    MAX_CONCENTRATION_ERROR = 95    # 95% in single position


# ============================================================================
# INPUT VALIDATION
# ============================================================================

class InputValidator:
    """Validates user input before processing"""
    
    def __init__(self):
        self.config = GuardrailsConfig()
    
    def validate_query(self, user_input: str) -> Tuple[bool, Optional[str]]:
        """
        Comprehensive query validation
        
        Returns: (is_valid, error_message)
        """
        
        # Length validation
        if len(user_input) > self.config.MAX_QUERY_LENGTH:
            return False, f"Query too long. Maximum {self.config.MAX_QUERY_LENGTH} characters."
        
        if len(user_input) < self.config.MIN_QUERY_LENGTH:
            return False, f"Query too short. Minimum {self.config.MIN_QUERY_LENGTH} characters."
        
        # Character validation (allow alphanumeric + basic punctuation)
        if not re.match(r'^[a-zA-Z0-9\s\-\$\%\(\)\,\.\?\!]+$', user_input):
            return False, "Query contains invalid characters."
        
        # SQL injection prevention
        dangerous_patterns = ['DROP', 'DELETE', 'INSERT', 'UPDATE', '--', '/*']
        if any(pattern in user_input.upper() for pattern in dangerous_patterns):
            return False, "Query contains suspicious patterns."
        
        # Excessive special characters
        special_count = sum(1 for c in user_input if not c.isalnum() and c != ' ')
        if special_count / len(user_input) > 0.3:
            return False, "Query has too many special characters."
        
        logger.info(f"Query validation passed: {len(user_input)} chars")
        
        return True, None
    
    def validate_ticker(self, ticker: str) -> bool:
        """Validate stock ticker symbol"""
        
        # Basic validation: 1-5 uppercase letters
        if not re.match(r'^[A-Z]{1,5}$', ticker):
            return False
        
        # Exclude common English words
        excluded = {
            'THE', 'AND', 'FOR', 'WITH', 'FROM', 'THAT', 'THIS', 'WHAT',
            'WHEN', 'WHERE', 'HOW', 'WHY', 'IS', 'IT', 'MY', 'YOUR',
            'PORTFOLIO', 'STOCK', 'PRICE', 'SHARE', 'DIVIDEND'
        }
        
        return ticker not in excluded
    
    def validate_tickers(self, tickers: List[str]) -> Tuple[bool, List[str]]:
        """Validate list of tickers"""
        
        invalid = [t for t in tickers if not self.validate_ticker(t)]
        
        if invalid:
            return False, invalid
        
        return True, []
    
    def validate_amount(self, amount: float) -> Tuple[bool, Optional[str]]:
        """Validate financial amount"""
        
        if amount < self.config.MIN_AMOUNT:
            return False, f"Amount too small (minimum: ${self.config.MIN_AMOUNT})"
        
        if amount > self.config.MAX_AMOUNT:
            return False, f"Amount exceeds maximum (${self.config.MAX_AMOUNT:,.0f})"
        
        # Check for unrealistic values
        if amount > 1_000_000:
            logger.warning(f"Large amount detected: ${amount:,.0f}")
        
        return True, None
    
    def validate_timeframe(self, years: int) -> Tuple[bool, Optional[str]]:
        """Validate financial planning timeframe"""
        
        if years < self.config.MIN_YEARS:
            return False, f"Minimum timeframe is {self.config.MIN_YEARS} year"
        
        if years > self.config.MAX_YEARS:
            return False, f"Maximum timeframe is {self.config.MAX_YEARS} years"
        
        return True, None


# ============================================================================
# FINANCIAL DATA VALIDATION
# ============================================================================

@dataclass
class ValidationResult:
    """Result of data validation"""
    is_valid: bool
    errors: List[str]
    warnings: List[str]


class FinancialValidator:
    """Validates financial data (portfolio, goals, etc.)"""
    
    def __init__(self):
        self.config = GuardrailsConfig()
        self.input_validator = InputValidator()
    
    def validate_portfolio(self, portfolio: Dict[str, float]) -> ValidationResult:
        """Comprehensive portfolio validation"""
        
        errors = []
        warnings = []
        
        # Empty portfolio check
        if not portfolio:
            errors.append("Portfolio cannot be empty")
            return ValidationResult(False, errors, warnings)
        
        # Holdings count check
        if len(portfolio) > 100:
            errors.append("Portfolio exceeds maximum holdings (100)")
        
        # Calculate total value
        total_value = sum(portfolio.values())
        
        if total_value > self.config.MAX_PORTFOLIO_VALUE:
            errors.append(f"Portfolio value exceeds ${self.config.MAX_PORTFOLIO_VALUE:,.0f}")
        
        # Validate each holding
        for ticker, amount in portfolio.items():
            # Ticker validation
            if not self.input_validator.validate_ticker(ticker):
                errors.append(f"Invalid ticker: {ticker}")
            
            # Amount validation
            valid, msg = self.input_validator.validate_amount(amount)
            if not valid:
                errors.append(f"{ticker}: {msg}")
            
            # Concentration check
            if total_value > 0:
                percentage = (amount / total_value) * 100
                
                if percentage > self.config.MAX_CONCENTRATION_ERROR:
                    errors.append(
                        f"{ticker} concentration {percentage:.1f}% exceeds maximum"
                    )
                elif percentage > self.config.MAX_CONCENTRATION_WARNING:
                    warnings.append(
                        f"{ticker} concentration {percentage:.1f}% is very high (risk)"
                    )
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )
    
    def validate_goal(self, goal: Dict[str, Any]) -> ValidationResult:
        """Validate financial goal"""
        
        errors = []
        warnings = []
        
        target = goal.get('target_amount', 0)
        current = goal.get('current_amount', 0)
        years = goal.get('years', 0)
        
        # Validate amounts
        if not (0 < target <= self.config.MAX_AMOUNT):
            errors.append("Target amount invalid")
        
        if not (0 <= current <= self.config.MAX_AMOUNT):
            errors.append("Current amount invalid")
        
        # Validate timeframe
        if not (self.config.MIN_YEARS <= years <= self.config.MAX_YEARS):
            errors.append(f"Timeframe must be {self.config.MIN_YEARS}-{self.config.MAX_YEARS} years")
        
        # Goal feasibility checks
        if current > target:
            errors.append("Current amount exceeds target (goal already achieved)")
        
        # Check for unrealistic growth
        if current > 0 and years > 0:
            growth_rate = ((target / current) ** (1 / years) - 1) * 100
            
            if growth_rate > 50:  # >50% annual growth
                warnings.append(
                    f"Goal requires {growth_rate:.1f}% annual growth (very ambitious)"
                )
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )


# ============================================================================
# PII DETECTION
# ============================================================================

class PIIDetector:
    """Detects personally identifiable information"""
    
    PII_PATTERNS = {
        "ssn": r'\d{3}-\d{2}-\d{4}',
        "email": r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
        "phone": r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',
        "credit_card": r'\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b',
        "bank_account": r'\b\d{10,12}\b',
        "ssn_alt": r'\b\d{9}\b',
    }
    
    def detect(self, text: str) -> Tuple[bool, List[str]]:
        """
        Detect PII in text
        
        Returns: (has_pii, pii_types_found)
        """
        
        detected_types = []
        
        for pii_type, pattern in self.PII_PATTERNS.items():
            if re.search(pattern, text):
                detected_types.append(pii_type)
        
        has_pii = len(detected_types) > 0
        
        if has_pii:
            logger.warning(f"PII detected: {detected_types}")
        
        return has_pii, detected_types
    
    def get_warning(self, detected_types: List[str]) -> str:
        """Get user-friendly warning message"""
        
        type_names = {
            "ssn": "Social Security Number",
            "email": "email address",
            "phone": "phone number",
            "credit_card": "credit card number",
            "bank_account": "bank account number",
        }
        
        readable_types = [type_names.get(t, t) for t in detected_types]
        
        return (
            f"Please don't include sensitive information like {', '.join(readable_types)}. "
            "This information is not needed for financial analysis."
        )


# ============================================================================
# RATE LIMITING
# ============================================================================

class RateLimiter:
    """Per-user rate limiting"""
    
    def __init__(self):
        self.config = GuardrailsConfig()
        self.user_requests: Dict[str, List[datetime]] = {}
    
    def is_allowed(self, user_id: str) -> Tuple[bool, Optional[str]]:
        """
        Check if user is within rate limits
        
        Returns: (is_allowed, error_message)
        """
        
        now = datetime.now()
        
        # Initialize user if needed
        if user_id not in self.user_requests:
            self.user_requests[user_id] = []
        
        requests = self.user_requests[user_id]
        
        # Clean up old requests
        one_day_ago = now - timedelta(days=1)
        requests = [r for r in requests if r > one_day_ago]
        self.user_requests[user_id] = requests
        
        # Count requests in each window
        one_minute_ago = now - timedelta(minutes=1)
        one_hour_ago = now - timedelta(hours=1)
        
        minute_count = sum(1 for r in requests if r > one_minute_ago)
        hour_count = sum(1 for r in requests if r > one_hour_ago)
        day_count = len(requests)
        
        # Check limits
        if minute_count >= self.config.QUERIES_PER_MINUTE:
            return False, f"Rate limit: max {self.config.QUERIES_PER_MINUTE} queries/minute"
        
        if hour_count >= self.config.QUERIES_PER_HOUR:
            return False, f"Rate limit: max {self.config.QUERIES_PER_HOUR} queries/hour"
        
        if day_count >= self.config.QUERIES_PER_DAY:
            return False, f"Rate limit: max {self.config.QUERIES_PER_DAY} queries/day"
        
        # Record this request
        self.user_requests[user_id] = requests + [now]
        
        return True, None


# ============================================================================
# EXECUTION SAFEGUARDS
# ============================================================================

async def execute_with_timeout(
    coro,
    timeout_ms: int = 30_000,
    timeout_message: str = "Operation timed out"
) -> Dict[str, Any]:
    """
    Execute coroutine with timeout protection
    
    Args:
        coro: Coroutine to execute
        timeout_ms: Timeout in milliseconds
        timeout_message: Message for timeout
    
    Returns:
        Dict with status, result, and timing
    """
    
    import time
    start_time = time.time()
    
    try:
        result = await asyncio.wait_for(
            coro,
            timeout=timeout_ms / 1000
        )
        
        execution_time_ms = (time.time() - start_time) * 1000
        
        return {
            "status": "success",
            "result": result,
            "execution_time_ms": execution_time_ms
        }
    
    except asyncio.TimeoutError:
        execution_time_ms = (time.time() - start_time) * 1000
        
        logger.warning(f"Timeout after {execution_time_ms:.0f}ms")
        
        return {
            "status": "timeout",
            "error": timeout_message,
            "execution_time_ms": execution_time_ms
        }
    
    except Exception as e:
        execution_time_ms = (time.time() - start_time) * 1000
        
        logger.error(f"Execution error: {str(e)}")
        
        return {
            "status": "error",
            "error": str(e),
            "execution_time_ms": execution_time_ms
        }


# ============================================================================
# DISCLAIMER MANAGEMENT
# ============================================================================

class DisclaimerManager:
    """Manages financial advice disclaimers"""
    
    DISCLAIMERS = {
        "tax": (
            "⚠️ **TAX DISCLAIMER**: This is educational information only, "
            "not tax advice. Consult a qualified tax professional for your specific situation."
        ),
        "investment": (
            "⚠️ **INVESTMENT DISCLAIMER**: This analysis is for informational purposes only. "
            "Past performance doesn't guarantee future results. Consider your risk tolerance "
            "and financial goals before making decisions."
        ),
        "goal_planning": (
            "⚠️ **PLANNING DISCLAIMER**: These projections are estimates based on assumptions. "
            "Actual results may vary significantly based on market conditions and changes."
        ),
        "general": (
            "⚠️ **GENERAL DISCLAIMER**: Not financial advice. Consult a qualified financial "
            "advisor before making investment decisions."
        ),
    }
    
    def get_disclaimer(self, disclaimer_type: str = "general") -> str:
        """Get appropriate disclaimer"""
        return self.DISCLAIMERS.get(disclaimer_type, self.DISCLAIMERS["general"])
    
    def add_disclaimers(self, response: str, intent_types: List[str]) -> str:
        """Add disclaimers based on intent types"""
        
        if "tax" in intent_types or "tax_question" in str(intent_types):
            response += f"\n\n{self.get_disclaimer('tax')}"
        elif "investment" in intent_types or "goal_planning" in intent_types:
            response += f"\n\n{self.get_disclaimer('goal_planning')}"
        else:
            response += f"\n\n{self.get_disclaimer('general')}"
        
        return response


# ============================================================================
# AUDIT LOGGING
# ============================================================================

@dataclass
class AuditLog:
    """Audit trail entry"""
    timestamp: datetime
    session_id: str
    user_id: str
    action: str
    status: str  # "success", "error", "warning"
    agents_used: List[str]
    query_hash: str  # Hash of query (not query itself)
    response_length: int
    execution_time_ms: float
    error_code: Optional[str] = None
    error_message: Optional[str] = None


class AuditLogger:
    """Logs events for compliance and debugging"""
    
    def create_log(
        self,
        session_id: str,
        user_id: str,
        user_query: str,
        agents_used: List[str],
        response: str,
        success: bool,
        execution_time_ms: float,
        error: Optional[str] = None
    ) -> AuditLog:
        """Create audit log entry (without storing sensitive data)"""
        
        # Hash query (don't store actual query for privacy)
        query_hash = hashlib.sha256(user_query.encode()).hexdigest()[:16]
        
        return AuditLog(
            timestamp=datetime.now(),
            session_id=session_id,
            user_id=user_id,
            action="orchestration_execution",
            status="success" if success else "error",
            agents_used=agents_used,
            query_hash=query_hash,
            response_length=len(response),
            execution_time_ms=execution_time_ms,
            error_code="unknown_error" if error else None,
            error_message=error
        )


# ============================================================================
# SINGLETON INSTANCES
# ============================================================================

_input_validator = None
_financial_validator = None
_pii_detector = None
_rate_limiter = None
_disclaimer_manager = None
_audit_logger = None


def get_input_validator() -> InputValidator:
    global _input_validator
    if _input_validator is None:
        _input_validator = InputValidator()
    return _input_validator


def get_financial_validator() -> FinancialValidator:
    global _financial_validator
    if _financial_validator is None:
        _financial_validator = FinancialValidator()
    return _financial_validator


def get_pii_detector() -> PIIDetector:
    global _pii_detector
    if _pii_detector is None:
        _pii_detector = PIIDetector()
    return _pii_detector


def get_rate_limiter() -> RateLimiter:
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = RateLimiter()
    return _rate_limiter


def get_disclaimer_manager() -> DisclaimerManager:
    global _disclaimer_manager
    if _disclaimer_manager is None:
        _disclaimer_manager = DisclaimerManager()
    return _disclaimer_manager


def get_audit_logger() -> AuditLogger:
    global _audit_logger
    if _audit_logger is None:
        _audit_logger = AuditLogger()
    return _audit_logger
