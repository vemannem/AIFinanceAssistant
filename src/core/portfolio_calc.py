"""Portfolio Calculator - Calculate allocation, diversification, and risk metrics."""

from typing import List, Dict, Any, Tuple, Optional
from dataclasses import dataclass
from src.core.logger import get_logger
from src.core.config import Config

logger = get_logger(__name__, Config.LOG_LEVEL)


@dataclass
class Holding:
    """Single holding in portfolio."""
    ticker: str
    quantity: float
    current_price: float
    cost_basis: float = 0.0  # Optional: for tax calculations


@dataclass
class PortfolioMetrics:
    """Portfolio metrics and analysis."""
    total_value: float
    total_cost: float
    total_gain_loss: float
    total_return_pct: float
    holdings_count: int
    allocation: List[Dict[str, Any]]
    diversification_score: float  # 0-100
    asset_class_distribution: Dict[str, float]
    risk_level: str  # low, moderate, high
    largest_position: str  # ticker of largest position
    largest_position_pct: float


class PortfolioCalculator:
    """Calculate portfolio metrics and analysis."""
    
    # Asset class mapping (simplified)
    ASSET_CLASS_MAP = {
        # Large cap
        'AAPL': 'large_cap', 'MSFT': 'large_cap', 'GOOGL': 'large_cap',
        'AMZN': 'large_cap', 'NVDA': 'large_cap', 'TSLA': 'large_cap',
        # Small cap (example)
        'LMND': 'small_cap', 'SNOW': 'small_cap',
        # Bonds
        'BND': 'bonds', 'AGG': 'bonds', 'TLT': 'bonds',
        # ETFs (general)
        'SPY': 'large_cap_etf', 'QQQ': 'tech_etf', 'VTI': 'total_market_etf',
    }
    
    def __init__(self):
        """Initialize portfolio calculator."""
        logger.info("📊 Portfolio Calculator initialized")
    
    def calculate_metrics(self, holdings: List[Holding]) -> PortfolioMetrics:
        """
        Calculate comprehensive portfolio metrics.
        
        Args:
            holdings: List of Holding objects
            
        Returns:
            PortfolioMetrics with all calculations
        """
        if not holdings:
            logger.warning("⚠️  Empty portfolio")
            return self._empty_portfolio_metrics()
        
        # Calculate total values
        total_value = sum(h.quantity * h.current_price for h in holdings)
        total_cost = sum(h.quantity * h.cost_basis for h in holdings) if any(h.cost_basis for h in holdings) else total_value
        total_gain_loss = total_value - total_cost
        total_return_pct = (total_gain_loss / total_cost * 100) if total_cost > 0 else 0
        
        # Calculate allocation
        allocation = []
        largest_position_pct = 0
        largest_position_ticker = holdings[0].ticker
        
        for holding in holdings:
            position_value = holding.quantity * holding.current_price
            position_pct = (position_value / total_value * 100) if total_value > 0 else 0
            
            allocation.append({
                "ticker": holding.ticker,
                "quantity": holding.quantity,
                "current_price": holding.current_price,
                "position_value": round(position_value, 2),
                "allocation_pct": round(position_pct, 2),
                "gain_loss": round(position_value - (holding.quantity * holding.cost_basis), 2)
            })
            
            if position_pct > largest_position_pct:
                largest_position_pct = position_pct
                largest_position_ticker = holding.ticker
        
        # Sort by allocation percentage
        allocation.sort(key=lambda x: x['allocation_pct'], reverse=True)
        
        # Calculate diversification score (Herfindahl index)
        diversification_score = self._calculate_diversification(allocation)
        
        # Calculate asset class distribution
        asset_dist = self._calculate_asset_distribution(holdings, total_value)
        
        # Estimate risk level
        risk_level = self._estimate_risk_level(asset_dist, diversification_score)
        
        metrics = PortfolioMetrics(
            total_value=round(total_value, 2),
            total_cost=round(total_cost, 2),
            total_gain_loss=round(total_gain_loss, 2),
            total_return_pct=round(total_return_pct, 2),
            holdings_count=len(holdings),
            allocation=allocation,
            diversification_score=round(diversification_score, 1),
            asset_class_distribution=asset_dist,
            risk_level=risk_level,
            largest_position=largest_position_ticker,
            largest_position_pct=round(largest_position_pct, 2)
        )
        
        logger.info(f"✅ Portfolio metrics calculated: ${total_value:.2f}, {len(holdings)} holdings")
        return metrics
    
    def calculate_rebalancing(
        self, 
        holdings: List[Holding], 
        target_allocation: Dict[str, float]
    ) -> Dict[str, Any]:
        """
        Calculate rebalancing recommendations.
        
        Args:
            holdings: Current holdings
            target_allocation: Target allocation (e.g., {"stocks": 70, "bonds": 30})
            
        Returns:
            {
                "current_allocation": {...},
                "target_allocation": {...},
                "required_trades": [
                    {"ticker": "AAPL", "action": "buy", "amount": 1000},
                    {"ticker": "BND", "action": "sell", "amount": 500}
                ],
                "rebalance_urgency": "low|medium|high"
            }
        """
        metrics = self.calculate_metrics(holdings)
        current_allocation = {h['ticker']: h['allocation_pct'] for h in metrics.allocation}
        
        required_trades = []
        max_drift = 0
        
        for ticker in target_allocation.keys():
            current = current_allocation.get(ticker, 0)
            target = target_allocation[ticker]
            drift = abs(current - target)
            max_drift = max(max_drift, drift)
            
            if drift > 2:  # Only rebalance if drift > 2%
                amount_pct = target - current
                amount_value = metrics.total_value * amount_pct / 100
                
                required_trades.append({
                    "ticker": ticker,
                    "action": "buy" if amount_pct > 0 else "sell",
                    "amount": round(abs(amount_value), 2),
                    "drift_pct": round(drift, 2)
                })
        
        # Determine urgency
        if max_drift > 10:
            urgency = "high"
        elif max_drift > 5:
            urgency = "medium"
        else:
            urgency = "low"
        
        logger.info(f"📊 Rebalancing calculated: {len(required_trades)} trades needed")
        
        return {
            "current_allocation": current_allocation,
            "target_allocation": target_allocation,
            "required_trades": sorted(required_trades, key=lambda x: x['drift_pct'], reverse=True),
            "rebalance_urgency": urgency,
            "max_drift_pct": round(max_drift, 2)
        }
    
    def _calculate_diversification(self, allocation: List[Dict]) -> float:
        """
        Calculate diversification score using Herfindahl index.
        Higher score = better diversification (0-100).
        """
        if not allocation:
            return 0
        
        # For single holding, diversification score is 0
        if len(allocation) == 1:
            return 0
        
        # Herfindahl index: sum of squared allocation percentages
        herfindahl = sum((item['allocation_pct'] / 100) ** 2 for item in allocation)
        
        # Convert to 0-100 score (inverse)
        # If perfectly diversified (equal weight): score = 100
        # If all in one: score = 0
        num_holdings = len(allocation)
        min_herfindahl = 1 / num_holdings  # Perfect diversification
        max_herfindahl = 1  # Single holding
        
        # Avoid division by zero for single holding (already handled above)
        diversification = ((max_herfindahl - herfindahl) / (max_herfindahl - min_herfindahl)) * 100
        return max(0, min(100, diversification))  # Clamp to 0-100
    
    def _calculate_asset_distribution(self, holdings: List[Holding], total_value: float) -> Dict[str, float]:
        """Calculate distribution across asset classes."""
        distribution = {
            "large_cap": 0.0,
            "small_cap": 0.0,
            "bonds": 0.0,
            "international": 0.0,
            "commodities": 0.0,
            "other": 0.0
        }
        
        for holding in holdings:
            asset_class = self.ASSET_CLASS_MAP.get(holding.ticker, "other")
            position_value = holding.quantity * holding.current_price
            pct = (position_value / total_value * 100) if total_value > 0 else 0
            distribution[asset_class] += pct
        
        return {k: round(v, 2) for k, v in distribution.items()}
    
    def _estimate_risk_level(self, asset_dist: Dict[str, float], diversification: float) -> str:
        """Estimate portfolio risk level."""
        equity_pct = asset_dist['large_cap'] + asset_dist['small_cap'] + asset_dist['international']
        
        if diversification < 30:
            return "high"
        elif equity_pct > 80:
            return "high"
        elif equity_pct < 30:
            return "low"
        else:
            return "moderate"
    
    def _empty_portfolio_metrics(self) -> PortfolioMetrics:
        """Return empty portfolio metrics."""
        return PortfolioMetrics(
            total_value=0,
            total_cost=0,
            total_gain_loss=0,
            total_return_pct=0,
            holdings_count=0,
            allocation=[],
            diversification_score=0,
            asset_class_distribution={},
            risk_level="unknown",
            largest_position="N/A",
            largest_position_pct=0
        )


# Singleton instance
_portfolio_calculator: Optional[PortfolioCalculator] = None


def get_portfolio_calculator() -> PortfolioCalculator:
    """Get or create portfolio calculator singleton."""
    global _portfolio_calculator
    if _portfolio_calculator is None:
        _portfolio_calculator = PortfolioCalculator()
    return _portfolio_calculator
