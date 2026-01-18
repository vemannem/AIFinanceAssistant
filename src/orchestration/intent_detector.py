"""
Intent Detector for Multi-Agent Orchestration

Detects user intent and extracts relevant context from user queries.
Routes queries to appropriate agents based on intent classification.
"""

import re
from typing import List, Dict, Any, Optional
import logging
from src.orchestration.state import (
    Intent, AgentType, RouterDecision, 
    OrchestrationState, INTENT_KEYWORDS
)
from src.core.llm_provider import get_llm_provider


logger = logging.getLogger(__name__)


class IntentDetector:
    """
    Multi-intent detector using keyword matching and LLM fallback
    
    Detects user intent(s) from natural language input and extracts
    relevant structured data (tickers, amounts, timeframes, etc.)
    """
    
    def __init__(self):
        self.intent_keywords = INTENT_KEYWORDS
    
    def detect_intents(self, user_input: str) -> List[Intent]:
        """
        Detect one or more intents from user input
        
        Args:
            user_input: User's natural language query
            
        Returns:
            List of detected intents (ordered by confidence)
        """
        detected_intents = []
        input_lower = user_input.lower()
        
        # Keyword-based detection (fast path)
        intent_scores = {}
        
        for intent, keywords in self.intent_keywords.items():
            if intent == Intent.UNKNOWN:
                continue
            
            # Count matching keywords
            matches = sum(1 for keyword in keywords if keyword in input_lower)
            if matches > 0:
                intent_scores[intent] = matches
        
        # Sort by score (descending)
        if intent_scores:
            sorted_intents = sorted(
                intent_scores.items(), 
                key=lambda x: x[1], 
                reverse=True
            )
            
            # Take top intents with good scores
            for intent, score in sorted_intents:
                if score >= 1:  # At least 1 keyword match
                    detected_intents.append(intent)
        
        # If no intents detected, return UNKNOWN
        if not detected_intents:
            detected_intents = [Intent.UNKNOWN]
        
        logger.info(f"Detected intents for '{user_input[:50]}': {detected_intents}")
        return detected_intents
    
    def get_primary_intent(self, intents: List[Intent]) -> Intent:
        """Get primary intent from list"""
        if intents and intents[0] != Intent.UNKNOWN:
            return intents[0]
        return Intent.UNKNOWN
    
    def extract_tickers(self, user_input: str) -> List[str]:
        """
        Extract stock ticker symbols from input
        
        Looks for patterns like:
        - Single caps: AAPL, BND, VTI
        - In quotes: "AAPL", 'BND'
        - After $ or ticker: $AAPL, ticker AAPL
        """
        tickers = []
        
        # Pattern 1: Uppercase 2-5 character words (likely tickers, avoid single letters)
        pattern1 = r'\b([A-Z]{2,5})\b'
        
        # Pattern 2: In quotes
        pattern2 = r"['\"]([A-Z]{2,5})['\"]"
        
        # Pattern 3: After common prefixes
        pattern3 = r'(?:ticker|symbol|holding)[\s:]*([A-Z]{2,5})'
        
        # Combine matches from all patterns
        matches1 = re.findall(pattern1, user_input)
        matches2 = re.findall(pattern2, user_input)
        matches3 = re.findall(pattern3, user_input, re.IGNORECASE)
        
        all_matches = matches1 + matches2 + matches3
        
        # Common English words to exclude (all caps)
        excluded_words = {
            'THE', 'AND', 'FOR', 'WITH', 'FROM', 'THAT', 'THIS',
            'WHAT', 'WHEN', 'WHERE', 'HOW', 'WHY', 'IS', 'IT', 'MY',
            'YOUR', 'PORTFOLIO', 'STOCK', 'PRICE', 'SHARE', 'DIVIDEND',
            'ANNUAL', 'ALSO', 'SOME', 'EACH', 'MANY', 'MORE', 'HAVE',
            'WILL', 'CAN', 'ABOUT', 'BEEN', 'THAN', 'JUST', 'INTO',
            'OVER', 'ONLY', 'WHICH', 'WOULD', 'COULD', 'SHOULD',
            'I', 'A', 'IN', 'ON', 'AT', 'BY', 'TO', 'OF', 'OR', 'UP'
        }
        
        for match in all_matches:
            if match not in excluded_words and match not in tickers:
                tickers.append(match)
        
        logger.info(f"Extracted tickers: {tickers}")
        return list(set(tickers))  # Remove duplicates
    
    def extract_dollar_amounts(self, user_input: str) -> List[float]:
        """
        Extract dollar amounts from input
        
        Looks for patterns like: $50000, $50k, $50K, 50000, 50,000
        """
        amounts = []
        
        # Pattern 1: $50000 or $50,000
        pattern1 = r'\$[\d,]+(?:\.\d{2})?'
        
        # Pattern 2: 50000 or 50,000 (after context keywords)
        pattern2 = r'(?:goal|save|contribute|amount|total|have|worth|portfolio)[\s:]*[\$]?([\d,]+(?:\.\d{2})?)'
        
        matches1 = re.findall(pattern1, user_input)
        matches2 = re.findall(pattern2, user_input, re.IGNORECASE)
        
        for match in matches1 + matches2:
            # Remove $ and commas
            clean = match.replace('$', '').replace(',', '')
            try:
                amounts.append(float(clean))
            except ValueError:
                continue
        
        logger.info(f"Extracted amounts: {amounts}")
        return amounts
    
    def extract_timeframe(self, user_input: str) -> Optional[str]:
        """
        Extract financial timeframe/goal
        
        Looks for: "5 years", "10 year horizon", "in 3 months", etc.
        """
        patterns = [
            r'(\d+)\s*years?',
            r'(\d+)\s*months?',
            r'(\d+)\s*(?:business\s+)?days?',
            r'(\d+)[-/]year',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, user_input, re.IGNORECASE)
            if match:
                logger.info(f"Extracted timeframe: {match.group(0)}")
                return match.group(0)
        
        return None
    
    def get_confidence_score(self, intents: List[Intent], user_input: str) -> float:
        """
        Calculate confidence score for intent detection (0.0 to 1.0)
        
        Factors:
        - Number of matching keywords
        - Clarity of input
        - Presence of extractable data
        """
        if Intent.UNKNOWN in intents and len(intents) == 1:
            return 0.3  # Low confidence for unknown
        
        input_lower = user_input.lower()
        
        # Count keyword matches across all detected intents
        keyword_matches = 0
        for intent in intents:
            if intent in self.intent_keywords:
                matches = sum(
                    1 for kw in self.intent_keywords[intent]
                    if kw in input_lower
                )
                keyword_matches += matches
        
        # Score factors
        score = 0.5  # Base score
        
        # Keyword matches increase score
        score += min(0.3, keyword_matches * 0.1)
        
        # Extracted data increases score
        if self.extract_tickers(user_input):
            score += 0.1
        if self.extract_dollar_amounts(user_input):
            score += 0.1
        if self.extract_timeframe(user_input):
            score += 0.1
        
        return min(1.0, max(0.3, score))
    
    def make_routing_decision(self, state: OrchestrationState) -> RouterDecision:
        """
        Make routing decision based on detected intents
        
        Determines which agents should handle the request
        """
        intents = state.detected_intents
        primary = state.primary_intent or Intent.UNKNOWN
        
        # Build list of agents from intent mapping
        agents_to_call = []
        for intent in intents:
            from src.orchestration.state import INTENT_TO_AGENTS
            if intent in INTENT_TO_AGENTS:
                for agent in INTENT_TO_AGENTS[intent]:
                    if agent not in agents_to_call:
                        agents_to_call.append(agent)
        
        # Default fallback
        if not agents_to_call:
            agents_to_call = [AgentType.FINANCE_QA]
        
        # Extract data for agents
        extracted_data = {
            "tickers": self.extract_tickers(state.user_input),
            "amounts": self.extract_dollar_amounts(state.user_input),
            "timeframe": self.extract_timeframe(state.user_input),
        }
        
        decision = RouterDecision(
            intents=intents,
            primary_intent=primary,
            agents=agents_to_call,
            confidence=state.confidence_score,
            reasoning=f"Detected intents: {[i.value for i in intents]}. Routing to {len(agents_to_call)} agent(s).",
            extracted_data=extracted_data
        )
        
        logger.info(f"Routing decision: {decision.agents}")
        return decision


# Singleton instance
_detector = None


def get_intent_detector() -> IntentDetector:
    """Get singleton instance of intent detector"""
    global _detector
    if _detector is None:
        _detector = IntentDetector()
    return _detector
