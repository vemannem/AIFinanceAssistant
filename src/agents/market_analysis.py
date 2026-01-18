"""Market Analysis Agent - Provides market data and stock analysis."""

import asyncio
from typing import Optional, List, Dict, Any
from src.agents import BaseAgent, AgentOutput
from src.core.logger import get_logger
from src.core.config import Config
from src.core.market_data import get_market_data_provider, MarketDataError

logger = get_logger(__name__, Config.LOG_LEVEL)


class MarketAnalysisAgent(BaseAgent):
    """
    Market Analysis Agent.
    
    Provides market data and analysis for:
    - Stock quotes and price movements
    - Historical trends
    - Fundamental metrics (P/E, dividend, etc.)
    - Technical indicators
    """
    
    def __init__(self):
        """Initialize market analysis agent."""
        super().__init__("market_analysis")
        self.market_data = get_market_data_provider()
        logger.info("📈 Market Analysis Agent initialized")
    
    async def execute(
        self,
        user_message: str,
        conversation_context: Optional[str] = None,
        query_data: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> AgentOutput:
        """
        Execute market analysis.
        
        Args:
            user_message: User's market query (e.g., "What's the price of AAPL?")
            conversation_context: Previous conversation history
            query_data: {
                "tickers": ["AAPL", "GOOGL"],
                "analysis_type": "quote|historical|fundamentals|comparison"
            }
            
        Returns:
            AgentOutput with market analysis
        """
        self._log_execution("START", f"market_analysis - {user_message[:50]}")
        
        try:
            # Extract tickers from user message if not provided
            tickers = self._extract_tickers(user_message, query_data)
            
            if not tickers:
                return AgentOutput(
                    answer_text="❌ No stock tickers found. Please specify which stocks you'd like to analyze (e.g., AAPL, GOOGL).",
                    citations=[],
                    tool_calls_made=["parsing"],
                    structured_data={"error": "no_tickers"}
                )
            
            # Get analysis type
            analysis_type = query_data.get('analysis_type', 'quote') if query_data else 'quote'
            
            # Fetch market data
            if len(tickers) == 1:
                result = await self._analyze_single_ticker(tickers[0], analysis_type)
            else:
                result = await self._analyze_multiple_tickers(tickers, analysis_type)
            
            self._log_execution("END", f"Market analysis complete for {len(tickers)} tickers")
            
            return result
            
        except MarketDataError as e:
            logger.error(f"❌ Market data error: {str(e)}")
            return AgentOutput(
                answer_text=f"⚠️ Error retrieving market data: {str(e)}",
                citations=[],
                tool_calls_made=["market_data_retrieval"],
                structured_data={"error": str(e)}
            )
        
        except Exception as e:
            logger.error(f"❌ Market analysis error: {str(e)}")
            return AgentOutput(
                answer_text=f"❌ Error analyzing market data: {str(e)}",
                citations=[],
                tool_calls_made=["market_data_retrieval"],
                structured_data={"error": str(e)}
            )
    
    async def _analyze_single_ticker(self, ticker: str, analysis_type: str) -> AgentOutput:
        """Analyze single ticker."""
        if analysis_type == "fundamentals":
            fundamentals = self.market_data.get_fundamentals(ticker)
            answer_text = self._format_fundamentals(ticker, fundamentals)
            structured_data = fundamentals
        
        elif analysis_type == "historical":
            historical = self.market_data.get_historical_data(ticker, period="1y")
            answer_text = self._format_historical(ticker, historical)
            structured_data = historical
        
        else:  # quote
            quote = self.market_data.get_quote(ticker)
            answer_text = self._format_quote(quote)
            structured_data = quote
        
        return AgentOutput(
            answer_text=answer_text,
            citations=[],
            tool_calls_made=["market_data_retrieval"],
            structured_data=structured_data
        )
    
    async def _analyze_multiple_tickers(self, tickers: List[str], analysis_type: str) -> AgentOutput:
        """Analyze multiple tickers."""
        result = self.market_data.get_multiple_quotes(tickers)
        
        answer_text = self._format_multiple_quotes(result)
        
        return AgentOutput(
            answer_text=answer_text,
            citations=[],
            tool_calls_made=["market_data_retrieval"],
            structured_data=result
        )
    
    def _extract_tickers(self, message: str, query_data: Optional[Dict]) -> List[str]:
        """Extract stock tickers from message or query data."""
        if query_data and 'tickers' in query_data:
            return query_data['tickers']
        
        # Simple extraction - look for common ticker patterns
        import re
        tickers = re.findall(r'\b[A-Z]{1,5}\b', message)
        
        # Filter out common words
        common_words = {'WHAT', 'ABOUT', 'PRICE', 'STOCK', 'IS', 'THE', 'OF'}
        tickers = [t for t in tickers if t not in common_words and len(t) <= 5]
        
        return list(set(tickers))  # Remove duplicates
    
    def _format_quote(self, quote: Dict[str, Any]) -> str:
        """Format quote data as readable text."""
        change_symbol = "📈" if quote['change'] >= 0 else "📉"
        
        return f"""
## Market Quote - {quote['ticker']}

**Current Price:** ${quote['price']}  
**Change:** {change_symbol} {quote['change']:+.2f} ({quote['change_pct']:+.2f}%)  
**Currency:** {quote['currency']}  
**Updated:** {quote['timestamp']}

### Analysis
{"The stock is **UP**" if quote['change'] > 0 else "The stock is **DOWN**"} {abs(quote['change_pct']):.2f}% today.

**Next Steps:**
- Check historical trends for context
- Review company fundamentals
- Analyze volume and trading patterns
"""
    
    def _format_multiple_quotes(self, result: Dict[str, Any]) -> str:
        """Format multiple quotes as comparison."""
        answer = f"## Market Comparison\n\n**Quotes Retrieved:** {result['successful_count']}/{result['total_count']}\n\n"
        
        for quote in result['quotes']:
            change_symbol = "📈" if quote['change'] >= 0 else "📉"
            answer += f"- **{quote['ticker']}**: ${quote['price']} {change_symbol} {quote['change_pct']:+.2f}%\n"
        
        if result['failed']:
            answer += f"\n**Failed Retrievals:** {len(result['failed'])}\n"
            for failed in result['failed']:
                answer += f"- {failed['ticker']}: {failed['error']}\n"
        
        return answer
    
    def _format_fundamentals(self, ticker: str, fundamentals: Dict[str, Any]) -> str:
        """Format fundamental data."""
        market_cap = fundamentals.get('market_cap')
        market_cap_str = f"${market_cap:,}" if isinstance(market_cap, (int, float)) else 'N/A'
        avg_volume = fundamentals.get('avg_volume')
        avg_volume_str = f"{avg_volume:,}" if isinstance(avg_volume, (int, float)) else 'N/A'
        
        return f"""
## Fundamentals - {fundamentals['company_name']} ({ticker})

### Key Metrics
- **P/E Ratio:** {fundamentals.get('pe_ratio', 'N/A')}
- **EPS:** ${fundamentals.get('eps', 'N/A')}
- **Market Cap:** {market_cap_str}
- **Dividend Yield:** {fundamentals.get('dividend_yield', 'N/A')}%

### 52-Week Range
- **High:** ${fundamentals.get('52_week_high', 'N/A')}
- **Low:** ${fundamentals.get('52_week_low', 'N/A')}
- **Avg Volume:** {avg_volume_str}

### Classification
- **Sector:** {fundamentals.get('sector', 'N/A')}
- **Industry:** {fundamentals.get('industry', 'N/A')}

**Note:** Fundamental data is as of market close. Check financial statements for detailed analysis.
"""
    
    def _format_historical(self, ticker: str, historical: Dict[str, Any]) -> str:
        """Format historical data."""
        data = historical['data']
        if not data:
            return f"No historical data available for {ticker}"
        
        recent = data[-1]
        oldest = data[0]
        
        return f"""
## Historical Data - {ticker} ({historical['period']})

### Current Performance
- **Trend:** {historical['trend'].upper()}
- **Highest:** ${historical['max_price']}
- **Lowest:** ${historical['min_price']}

### Recent Price
- **Close:** ${recent['close']}
- **High:** ${recent['high']}
- **Low:** ${recent['low']}
- **Volume:** {recent['volume']:,}

### Period Range
- **From:** {oldest['date']}
- **To:** {recent['date']}

**Analysis:** The stock has been {historical['trend']} over the past {historical['period']}. 
Price ranged from ${historical['min_price']} to ${historical['max_price']}.
"""


# Singleton getter
_market_agent: Optional[MarketAnalysisAgent] = None


def get_market_analysis_agent() -> MarketAnalysisAgent:
    """Get or create market analysis agent singleton."""
    global _market_agent
    if _market_agent is None:
        _market_agent = MarketAnalysisAgent()
    return _market_agent
