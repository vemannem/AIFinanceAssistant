"""Portfolio Analysis Agent - Analyzes portfolios and provides recommendations."""

import asyncio
from typing import Optional, List, Dict, Any
from src.agents import BaseAgent, AgentOutput
from src.core.logger import get_logger
from src.core.config import Config
from src.core.market_data import get_market_data_provider, MarketDataError
from src.core.portfolio_calc import get_portfolio_calculator, Holding

logger = get_logger(__name__, Config.LOG_LEVEL)


class PortfolioAnalysisAgent(BaseAgent):
    """
    Portfolio Analysis Agent.
    
    Analyzes investment portfolios for:
    - Asset allocation
    - Diversification scoring
    - Risk assessment
    - Rebalancing recommendations
    """
    
    def __init__(self):
        """Initialize portfolio analysis agent."""
        super().__init__("portfolio_analysis")
        self.market_data = get_market_data_provider()
        self.calculator = get_portfolio_calculator()
        logger.info("🎯 Portfolio Analysis Agent initialized")
    
    async def execute(
        self,
        user_message: str,
        conversation_context: Optional[str] = None,
        holdings_data: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> AgentOutput:
        """
        Execute portfolio analysis.
        
        Args:
            user_message: User's portfolio query
            conversation_context: Previous conversation history
            holdings_data: {
                "holdings": [
                    {"ticker": "AAPL", "quantity": 100, "current_price": 189.95},
                    {"ticker": "BND", "quantity": 50, "current_price": 82.30}
                ],
                "analysis_type": "allocation|diversification|rebalance|full"
            }
            
        Returns:
            AgentOutput with portfolio analysis
        """
        self._log_execution("START", f"portfolio_analysis - {user_message[:50]}")
        
        try:
            # Validate holdings data
            if not holdings_data or "holdings" not in holdings_data:
                return AgentOutput(
                    answer_text="❌ No portfolio holdings provided. Please provide holdings data with tickers, quantities, and current prices.",
                    citations=[],
                    tool_calls_made=["validation"],
                    structured_data={"error": "missing_holdings"}
                )
            
            # Convert to Holding objects
            holdings = [
                Holding(
                    ticker=h['ticker'],
                    quantity=float(h['quantity']),
                    current_price=float(h['current_price']),
                    cost_basis=float(h.get('cost_basis', h['current_price']))
                )
                for h in holdings_data['holdings']
            ]
            
            # Calculate metrics
            metrics = self.calculator.calculate_metrics(holdings)
            
            # Generate analysis
            answer_text = self._generate_analysis(metrics, holdings_data)
            
            # Prepare structured data
            structured_data = {
                "total_portfolio_value": metrics.total_value,
                "holdings_count": metrics.holdings_count,
                "allocation": metrics.allocation,
                "diversification_score": metrics.diversification_score,
                "risk_level": metrics.risk_level,
                "asset_distribution": metrics.asset_class_distribution,
                "total_return": metrics.total_return_pct,
                "largest_position": {
                    "ticker": metrics.largest_position,
                    "allocation_pct": metrics.largest_position_pct
                }
            }
            
            # Check if rebalancing requested
            if holdings_data.get('analysis_type') == 'rebalance':
                target_allocation = holdings_data.get('target_allocation', {
                    "STOCKS": 70, "BONDS": 30
                })
                rebalance_plan = self.calculator.calculate_rebalancing(holdings, target_allocation)
                structured_data['rebalancing'] = rebalance_plan
            
            self._log_execution("END", f"Total portfolio value: ${metrics.total_value}")
            
            return AgentOutput(
                answer_text=answer_text,
                citations=[],
                tool_calls_made=["market_data_retrieval", "portfolio_calculation"],
                structured_data=structured_data
            )
            
        except MarketDataError as e:
            logger.error(f"❌ Market data error: {str(e)}")
            return AgentOutput(
                answer_text=f"⚠️ Error retrieving market data: {str(e)}",
                citations=[],
                tool_calls_made=["market_data_retrieval"],
                structured_data={"error": str(e)}
            )
        
        except Exception as e:
            logger.error(f"❌ Portfolio analysis error: {str(e)}")
            return AgentOutput(
                answer_text=f"❌ Error analyzing portfolio: {str(e)}",
                citations=[],
                tool_calls_made=["portfolio_calculation"],
                structured_data={"error": str(e)}
            )
    
    def _generate_analysis(self, metrics, holdings_data: Dict[str, Any]) -> str:
        """Generate portfolio analysis narrative."""
        analysis = f"""
## Portfolio Analysis Report

### Portfolio Overview
- **Total Value:** ${metrics.total_value:,.2f}
- **Holdings:** {metrics.holdings_count} positions
- **Total Return:** {metrics.total_return_pct:+.2f}%
- **Risk Level:** {metrics.risk_level.upper()}

### Asset Allocation
"""
        for item in metrics.allocation:
            analysis += f"\n- **{item['ticker']}**: {item['allocation_pct']:.1f}% (${item['position_value']:,.2f})"
        
        analysis += f"""

### Diversification Analysis
- **Diversification Score:** {metrics.diversification_score:.1f}/100
- **Largest Position:** {metrics.largest_position} ({metrics.largest_position_pct:.1f}%)
"""
        
        # Add diversification assessment
        if metrics.diversification_score >= 70:
            diversification_status = "✅ Excellent - Well diversified across multiple positions"
        elif metrics.diversification_score >= 50:
            diversification_status = "⚠️ Good - Reasonable diversification, but could improve"
        else:
            diversification_status = "❌ Poor - Concentrated in few positions, high risk"
        
        analysis += f"\nStatus: {diversification_status}"
        
        # Asset class distribution
        analysis += "\n\n### Asset Class Distribution"
        for asset_class, pct in metrics.asset_class_distribution.items():
            if pct > 0:
                analysis += f"\n- {asset_class.replace('_', ' ').title()}: {pct:.1f}%"
        
        # Risk assessment
        analysis += f"\n\n### Risk Assessment\n"
        if metrics.risk_level == "high":
            analysis += "⚠️ **HIGH RISK:** Portfolio is heavily weighted toward equities. Consider diversifying into bonds or stable assets if risk-averse."
        elif metrics.risk_level == "moderate":
            analysis += "✅ **MODERATE RISK:** Balanced portfolio suitable for medium-term investors."
        else:
            analysis += "✅ **LOW RISK:** Conservative portfolio with significant bond allocation."
        
        # Recommendations
        analysis += "\n\n### Recommendations\n"
        if metrics.largest_position_pct > 50:
            analysis += f"1. ⚠️ **Reduce Concentration:** {metrics.largest_position} represents {metrics.largest_position_pct:.1f}% of portfolio. Consider reducing to <30% for better diversification.\n"
        
        if metrics.diversification_score < 50:
            analysis += "2. ⚠️ **Increase Diversification:** Add positions in different asset classes or sectors to reduce risk.\n"
        
        if metrics.total_return_pct > 0:
            analysis += f"3. ✅ **Performance:** Portfolio is up {metrics.total_return_pct:.2f}%. Monitor performance quarterly.\n"
        
        return analysis.strip()


# Singleton getter
_portfolio_agent: Optional[PortfolioAnalysisAgent] = None


def get_portfolio_analysis_agent() -> PortfolioAnalysisAgent:
    """Get or create portfolio analysis agent singleton."""
    global _portfolio_agent
    if _portfolio_agent is None:
        _portfolio_agent = PortfolioAnalysisAgent()
    return _portfolio_agent
