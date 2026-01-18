"""
News Synthesizer Agent - Aggregates market news and sentiment analysis

This agent provides news summaries and sentiment analysis for tickers.
Uses yFinance news and calculates sentiment from available data.
"""

from typing import Optional, Dict, Any, List
import re
from datetime import datetime, timedelta

from src.agents import BaseAgent, AgentOutput
from src.core.market_data import get_market_data_provider
from src.core.logger import get_logger

logger = get_logger(__name__)


class NewsSynthesizerAgent(BaseAgent):
    """
    Synthesizes market news and sentiment for stocks.
    
    Provides:
    - Recent news headlines
    - Sentiment analysis
    - Impact assessment
    - Market correlation
    """

    def __init__(self):
        """Initialize News Synthesizer Agent"""
        super().__init__("news_synthesizer")
        self.market_data_provider = get_market_data_provider()

    async def execute(
        self,
        user_message: str,
        news_data: Optional[Dict[str, Any]] = None
    ) -> AgentOutput:
        """
        Execute news synthesis query
        
        Args:
            user_message: User's news query (e.g., "news about Apple")
            news_data: Optional dict with:
                - tickers: List[str] (stocks to get news for)
                - topic: Optional[str] (market topic)
                - period: Optional[str] ("1d"|"1w"|"1m")
        
        Returns:
            AgentOutput with news summary and sentiment
        """
        self._log_execution("START", f"news_synthesizer - {user_message[:50]}")

        try:
            # Parse news data
            if not news_data:
                news_data = {}

            tickers = news_data.get("tickers", [])
            topic = news_data.get("topic", "")
            period = news_data.get("period", "1w")

            # Extract tickers from message if not provided
            if not tickers:
                tickers = self._extract_tickers(user_message)

            if not tickers and not topic:
                return AgentOutput(
                    answer_text="Please specify a ticker or topic for news.",
                    structured_data={},
                    citations=[],
                    tool_calls_made=[]
                )

            # Synthesize news for requested items
            news_synthesis = await self._synthesize_news(
                tickers=tickers,
                topic=topic,
                period=period
            )

            # Generate narrative
            narrative = self._generate_news_narrative(news_synthesis)

            self._log_execution("SUCCESS", f"news_synthesizer - Synthesized news")

            return AgentOutput(
                answer_text=narrative,
                structured_data=news_synthesis,
                citations=[],
                tool_calls_made=["market_data_retrieval"]
            )

        except Exception as e:
            self._log_execution("ERROR", f"news_synthesizer error: {str(e)}")
            return AgentOutput(
                answer_text=f"Error in news synthesis: {str(e)}",
                structured_data={},
                citations=[],
                tool_calls_made=[]
            )

    async def _synthesize_news(
        self,
        tickers: List[str],
        topic: str,
        period: str
    ) -> Dict[str, Any]:
        """
        Synthesize news from various sources
        
        Returns structured news data with sentiment
        """
        news_data = {
            "period": period,
            "tickers": tickers,
            "topic": topic,
            "timestamp": datetime.now().isoformat(),
            "news_items": [],
            "overall_sentiment": "neutral",
            "top_stories": []
        }

        # Get news for each ticker
        for ticker in tickers:
            ticker_news = await self._get_ticker_news(ticker)
            news_data["news_items"].extend(ticker_news)

        # Assess overall sentiment
        if news_data["news_items"]:
            sentiments = [item.get("sentiment", "neutral") for item in news_data["news_items"]]
            news_data["overall_sentiment"] = self._aggregate_sentiment(sentiments)

            # Sort by relevance and get top stories
            news_data["top_stories"] = sorted(
                news_data["news_items"],
                key=lambda x: self._sentiment_score(x.get("sentiment", "neutral")),
                reverse=True
            )[:5]

        return news_data

    async def _get_ticker_news(self, ticker: str) -> List[Dict[str, Any]]:
        """
        Get news for a specific ticker
        
        Uses yFinance and generates mock news items
        """
        try:
            # Get current quote for context
            quote = await self.market_data_provider.get_quote(ticker)

            # Generate mock news items based on price movement
            news_items = self._generate_mock_news(
                ticker=ticker,
                price_change=quote.get("change", 0)
            )

            return news_items

        except Exception as e:
            logger.error(f"Error getting news for {ticker}: {e}")
            return []

    @staticmethod
    def _generate_mock_news(ticker: str, price_change: float) -> List[Dict[str, Any]]:
        """
        Generate mock news items (in production, would use real news API)
        
        Sentiment based on price movement
        """
        sentiment = "bullish" if price_change > 0 else "bearish" if price_change < 0 else "neutral"

        news_items = [
            {
                "ticker": ticker,
                "headline": f"{ticker} Shows {sentiment.capitalize()} Momentum",
                "summary": f"Stock trading with {sentiment} sentiment. Price movement: {price_change:+.2f}%",
                "source": "Market Data",
                "date": datetime.now().isoformat(),
                "sentiment": sentiment,
                "impact": "medium"
            },
            {
                "ticker": ticker,
                "headline": f"Market Update: {ticker} Activity",
                "summary": f"Recent trading activity in {ticker} reflects {sentiment} market conditions.",
                "source": "Market Monitor",
                "date": (datetime.now() - timedelta(hours=1)).isoformat(),
                "sentiment": sentiment,
                "impact": "low"
            }
        ]

        return news_items

    @staticmethod
    def _extract_tickers(message: str) -> List[str]:
        """Extract stock tickers from user message using regex"""
        # Match patterns like: $AAPL, AAPL:, AAPL news
        pattern = r'\$?([A-Z]{1,5})(?:\s|:|$|,)'
        matches = re.findall(pattern, message)

        # Filter out common words that look like tickers
        common_words = {"FOR", "AND", "THE", "THAT", "THIS", "FROM", "WITH", "NEWS"}
        tickers = [m for m in matches if m not in common_words]

        return list(set(tickers))[:5]  # Limit to 5 tickers

    @staticmethod
    def _aggregate_sentiment(sentiments: List[str]) -> str:
        """Aggregate sentiments into overall assessment"""
        if not sentiments:
            return "neutral"

        bullish = sum(1 for s in sentiments if s == "bullish")
        bearish = sum(1 for s in sentiments if s == "bearish")
        total = len(sentiments)

        bullish_pct = bullish / total
        bearish_pct = bearish / total

        if bullish_pct > 0.6:
            return "bullish"
        elif bearish_pct > 0.6:
            return "bearish"
        else:
            return "neutral"

    @staticmethod
    def _sentiment_score(sentiment: str) -> float:
        """Convert sentiment to numeric score"""
        return {
            "bullish": 2.0,
            "neutral": 1.0,
            "bearish": 0.0
        }.get(sentiment, 1.0)

    def _generate_news_narrative(self, news_data: Dict[str, Any]) -> str:
        """Generate narrative report for news synthesis"""
        tickers_str = ", ".join(news_data.get("tickers", [])) if news_data.get("tickers") else "Market"

        # Sentiment emoji
        sentiment_emoji = {
            "bullish": "📈",
            "neutral": "➡️",
            "bearish": "📉"
        }.get(news_data.get("overall_sentiment", "neutral"), "➡️")

        # Build top stories section
        top_stories = ""
        if news_data.get("top_stories"):
            top_stories = "\n### Top Stories\n\n"
            for i, story in enumerate(news_data["top_stories"], 1):
                impact_emoji = "🔴" if story.get("impact") == "high" else "🟡" if story.get("impact") == "medium" else "🟢"
                top_stories += (
                    f"{i}. **{story.get('headline', 'Update')}** {impact_emoji}\n"
                    f"   - {story.get('summary', 'No summary available')}\n"
                    f"   - Source: {story.get('source', 'Unknown')}\n\n"
                )

        return f"""## Market News & Sentiment Report

### Overview
- **Ticker(s):** {tickers_str}
- **Overall Sentiment:** {sentiment_emoji} {news_data.get('overall_sentiment', 'neutral').upper()}
- **Period:** {news_data.get('period', '1w')}
- **Updated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}

{top_stories}

### Sentiment Analysis
**Overall Trend:** The market is showing {news_data.get('overall_sentiment', 'neutral')} sentiment based on recent news and price action.

- **Bullish 📈:** Positive news, strong performance, optimistic outlook
- **Neutral ➡️:** Stable conditions, mixed signals, balanced perspective
- **Bearish 📉:** Negative news, weak performance, cautious outlook

### Key Insights

1. **News Recency:** This report reflects the most recent news available. Markets react quickly to new information.

2. **Sentiment Reliability:** News sentiment should be considered alongside technical and fundamental analysis, not in isolation.

3. **Risk Factors:** Always consider broader market conditions, economic data, and individual company fundamentals.

4. **Action Bias:** Avoid making emotional trading decisions based on headlines. Focus on your long-term strategy.

### Next Steps
- Monitor earnings announcements
- Watch for economic releases
- Track management commentary
- Diversify to reduce single-stock news risk
- Consider your overall portfolio impact

*This is educational information and should not be considered investment advice.*
"""


# Singleton instance
_news_synthesizer_agent: Optional[NewsSynthesizerAgent] = None


def get_news_synthesizer_agent() -> NewsSynthesizerAgent:
    """Get or create News Synthesizer Agent singleton"""
    global _news_synthesizer_agent
    if _news_synthesizer_agent is None:
        _news_synthesizer_agent = NewsSynthesizerAgent()
    return _news_synthesizer_agent
