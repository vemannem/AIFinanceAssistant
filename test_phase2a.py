#!/usr/bin/env python3
"""Test Phase 2A agents - Market Data Provider, Portfolio Analysis, Market Analysis."""

import asyncio
from src.core.market_data import get_market_data_provider
from src.core.portfolio_calc import get_portfolio_calculator, Holding
from src.agents.portfolio_analysis import get_portfolio_analysis_agent
from src.agents.market_analysis import get_market_analysis_agent

print("\n" + "="*80)
print("PHASE 2A AGENT TESTING - Market Data & Portfolio Analysis")
print("="*80)

async def test_market_data_provider():
    """Test Market Data Provider."""
    print("\n📊 TEST 1: Market Data Provider")
    print("-" * 80)
    
    provider = get_market_data_provider()
    
    # Test 1: Single quote
    print("\n✓ Getting quote for AAPL...")
    try:
        quote = provider.get_quote("AAPL")
        print(f"  AAPL: ${quote['price']} ({quote['change_pct']:+.2f}%)")
    except Exception as e:
        print(f"  ❌ Error: {e}")
    
    # Test 2: Multiple quotes
    print("\n✓ Getting multiple quotes (AAPL, GOOGL, MSFT)...")
    try:
        result = provider.get_multiple_quotes(["AAPL", "GOOGL", "MSFT"])
        for quote in result['quotes']:
            print(f"  {quote['ticker']}: ${quote['price']} ({quote['change_pct']:+.2f}%)")
    except Exception as e:
        print(f"  ❌ Error: {e}")
    
    # Test 3: Historical data
    print("\n✓ Getting 1-year historical data for AAPL...")
    try:
        historical = provider.get_historical_data("AAPL", period="1y")
        print(f"  Trend: {historical['trend'].upper()}")
        print(f"  Range: ${historical['min_price']} - ${historical['max_price']}")
        print(f"  Data points: {len(historical['data'])}")
    except Exception as e:
        print(f"  ❌ Error: {e}")
    
    # Test 4: Fundamentals
    print("\n✓ Getting fundamentals for AAPL...")
    try:
        fundamentals = provider.get_fundamentals("AAPL")
        print(f"  Company: {fundamentals['company_name']}")
        print(f"  P/E Ratio: {fundamentals['pe_ratio']}")
        print(f"  Sector: {fundamentals['sector']}")
    except Exception as e:
        print(f"  ❌ Error: {e}")


def test_portfolio_calculator():
    """Test Portfolio Calculator."""
    print("\n\n💼 TEST 2: Portfolio Calculator")
    print("-" * 80)
    
    calculator = get_portfolio_calculator()
    
    # Create sample holdings
    holdings = [
        Holding(ticker="AAPL", quantity=100, current_price=189.95, cost_basis=150.0),
        Holding(ticker="GOOGL", quantity=50, current_price=141.20, cost_basis=120.0),
        Holding(ticker="BND", quantity=200, current_price=82.30, cost_basis=85.0),
    ]
    
    print("\n✓ Calculating portfolio metrics...")
    metrics = calculator.calculate_metrics(holdings)
    
    print(f"  Total Value: ${metrics.total_value:,.2f}")
    print(f"  Total Return: {metrics.total_return_pct:+.2f}%")
    print(f"  Holdings: {metrics.holdings_count}")
    print(f"  Diversification Score: {metrics.diversification_score:.1f}/100")
    print(f"  Risk Level: {metrics.risk_level.upper()}")
    
    print("\n✓ Allocation:")
    for item in metrics.allocation[:3]:
        print(f"  - {item['ticker']}: {item['allocation_pct']:.1f}% (${item['position_value']:,.2f})")
    
    print("\n✓ Asset Distribution:")
    for asset_class, pct in metrics.asset_class_distribution.items():
        if pct > 0:
            print(f"  - {asset_class.title()}: {pct:.1f}%")


async def test_portfolio_analysis_agent():
    """Test Portfolio Analysis Agent."""
    print("\n\n📈 TEST 3: Portfolio Analysis Agent")
    print("-" * 80)
    
    agent = get_portfolio_analysis_agent()
    
    holdings_data = {
        "holdings": [
            {"ticker": "AAPL", "quantity": 100, "current_price": 189.95},
            {"ticker": "GOOGL", "quantity": 50, "current_price": 141.20},
            {"ticker": "BND", "quantity": 200, "current_price": 82.30},
        ]
    }
    
    print("\n✓ Analyzing portfolio...")
    output = await agent.execute(
        user_message="Analyze my portfolio",
        holdings_data=holdings_data
    )
    
    print(f"\n📝 Analysis Summary:")
    print(output.answer_text[:500] + "...")
    
    print(f"\n📊 Structured Data:")
    print(f"  Total Value: ${output.structured_data['total_portfolio_value']:,.2f}")
    print(f"  Diversification: {output.structured_data['diversification_score']:.1f}/100")
    print(f"  Risk Level: {output.structured_data['risk_level']}")
    print(f"  Tools Used: {', '.join(output.tool_calls_made)}")


async def test_market_analysis_agent():
    """Test Market Analysis Agent."""
    print("\n\n💹 TEST 4: Market Analysis Agent")
    print("-" * 80)
    
    agent = get_market_analysis_agent()
    
    print("\n✓ Testing single ticker analysis...")
    output = await agent.execute(
        user_message="What is the current price of Apple stock?",
        query_data={"tickers": ["AAPL"], "analysis_type": "quote"}
    )
    
    print(f"\n📊 Market Quote:")
    print(output.answer_text[:300] + "...")
    
    print(f"\n📊 Structured Data:")
    if isinstance(output.structured_data, dict):
        if 'ticker' in output.structured_data:
            quote = output.structured_data
            print(f"  Ticker: {quote['ticker']}")
            print(f"  Price: ${quote['price']}")
            print(f"  Change: {quote['change_pct']:+.2f}%")
        elif 'quotes' in output.structured_data:
            result = output.structured_data
            print(f"  Retrieved: {result['successful_count']} quotes")


async def main():
    """Run all tests."""
    try:
        # Synchronous tests
        await test_market_data_provider()
        test_portfolio_calculator()
        
        # Async tests
        await test_portfolio_analysis_agent()
        await test_market_analysis_agent()
        
        print("\n" + "="*80)
        print("✅ ALL PHASE 2A TESTS COMPLETE")
        print("="*80 + "\n")
        
    except Exception as e:
        print(f"\n❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
