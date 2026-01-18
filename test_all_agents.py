#!/usr/bin/env python3
"""
Complete Agent Suite Test - Tests all 6 agents (Phase 1 + 2A + 2B)

This test validates that all agents in the system are functional and 
can work together in an integrated environment.

Run with: /usr/bin/python3 test_all_agents.py
"""

import asyncio
import sys
from datetime import datetime

# Phase 1 Agent
from src.agents.finance_qa import get_finance_qa_agent

# Phase 2A Agents
from src.agents.portfolio_analysis import get_portfolio_analysis_agent
from src.agents.market_analysis import get_market_analysis_agent

# Phase 2B Agents
from src.agents.goal_planning import get_goal_planning_agent
from src.agents.tax_education import get_tax_education_agent
from src.agents.news_synthesizer import get_news_synthesizer_agent


async def test_finance_qa_agent():
    """Test Finance Q&A Agent (Phase 1)"""
    print("\n" + "="*70)
    print("TEST 1: Finance Q&A Agent (Phase 1)")
    print("="*70)

    agent = get_finance_qa_agent()

    queries = [
        "What is diversification in investing?",
        "How do ETFs work?",
    ]

    for i, query in enumerate(queries, 1):
        print(f"\n📚 Query {i}: {query}")
        print("-" * 50)

        output = await agent.execute(query)

        assert output.answer_text, "Should have answer"
        assert output.tool_calls_made, "Should have used tools"

        print(f"✅ Answer generated ({len(output.answer_text)} chars)")
        print(f"   - Tools used: {output.tool_calls_made}")
        print(f"   - Citations: {len(output.citations)}")

        if output.citations:
            print(f"   - Sources: {[c.get('title', 'Unknown')[:40] for c in output.citations[:2]]}")

    print("\n✅ TEST 1: Finance Q&A Agent - PASSED\n")
    return True


async def test_portfolio_analysis_agent():
    """Test Portfolio Analysis Agent (Phase 2A)"""
    print("\n" + "="*70)
    print("TEST 2: Portfolio Analysis Agent (Phase 2A)")
    print("="*70)

    agent = get_portfolio_analysis_agent()

    test_cases = [
        {
            "name": "Well-diversified portfolio",
            "data": {
                "holdings": [
                    {"ticker": "AAPL", "quantity": 100, "current_price": 189.95, "cost_basis": 150.0},
                    {"ticker": "GOOGL", "quantity": 50, "current_price": 141.20, "cost_basis": 120.0},
                    {"ticker": "BND", "quantity": 200, "current_price": 82.30, "cost_basis": 85.0},
                ],
                "analysis_type": "full"
            }
        },
        {
            "name": "Single-ticker concentrated portfolio",
            "data": {
                "holdings": [
                    {"ticker": "TSLA", "quantity": 500, "current_price": 250.0, "cost_basis": 150.0},
                ],
                "analysis_type": "full"
            }
        }
    ]

    for case in test_cases:
        print(f"\n📊 Test Case: {case['name']}")
        print("-" * 50)

        output = await agent.execute(
            f"Analyze my portfolio: {case['name']}",
            holdings_data=case['data']
        )

        assert output.answer_text, "Should have analysis"
        assert output.structured_data, "Should have metrics"

        metrics = output.structured_data
        assert "total_portfolio_value" in metrics
        assert "diversification_score" in metrics
        assert "risk_level" in metrics

        print(f"✅ Portfolio analyzed")
        print(f"   - Value: ${metrics.get('total_portfolio_value', 0):,.2f}")
        print(f"   - Diversification: {metrics.get('diversification_score', 0):.1f}/100")
        print(f"   - Risk: {metrics.get('risk_level', 'unknown')}")
        print(f"   - Holdings: {len(metrics.get('allocation', []))}")

    print("\n✅ TEST 2: Portfolio Analysis Agent - PASSED\n")
    return True


async def test_market_analysis_agent():
    """Test Market Analysis Agent (Phase 2A)"""
    print("\n" + "="*70)
    print("TEST 3: Market Analysis Agent (Phase 2A)")
    print("="*70)

    agent = get_market_analysis_agent()

    test_cases = [
        {
            "name": "Single ticker quote",
            "message": "What's the price of Apple?",
            "data": {"tickers": ["AAPL"], "analysis_type": "quote"}
        },
        {
            "name": "Multiple ticker comparison",
            "message": "Compare GOOGL, MSFT, and AAPL",
            "data": {"tickers": ["GOOGL", "MSFT", "AAPL"], "analysis_type": "comparison"}
        },
        {
            "name": "Ticker extraction from message",
            "message": "Show me quotes for Tesla and Amazon",
            "data": {"analysis_type": "quote"}
        }
    ]

    for case in test_cases:
        print(f"\n📈 Test Case: {case['name']}")
        print("-" * 50)

        output = await agent.execute(
            case['message'],
            query_data=case['data']
        )

        assert output.answer_text, "Should have market data"
        assert output.structured_data, "Should have structured data"

        print(f"✅ Market data retrieved")
        print(f"   - Answer length: {len(output.answer_text)} chars")
        print(f"   - Tools used: {output.tool_calls_made}")

    print("\n✅ TEST 3: Market Analysis Agent - PASSED\n")
    return True


async def test_goal_planning_agent():
    """Test Goal Planning Agent (Phase 2B)"""
    print("\n" + "="*70)
    print("TEST 4: Goal Planning Agent (Phase 2B)")
    print("="*70)

    agent = get_goal_planning_agent()

    test_cases = [
        {
            "name": "Long-term goal (10 years)",
            "data": {
                "current_value": 25000,
                "goal_amount": 250000,
                "time_horizon_years": 10,
                "risk_appetite": "moderate",
                "current_return": 6.0
            }
        },
        {
            "name": "Short-term aggressive goal (3 years)",
            "data": {
                "current_value": 50000,
                "goal_amount": 100000,
                "time_horizon_years": 3,
                "risk_appetite": "high",
                "current_return": 8.5
            }
        }
    ]

    for case in test_cases:
        print(f"\n💰 Test Case: {case['name']}")
        print("-" * 50)

        output = await agent.execute(
            f"Help me plan: {case['name']}",
            goal_data=case['data']
        )

        assert output.answer_text, "Should have projections"
        assert output.structured_data, "Should have metrics"

        metrics = output.structured_data
        assert "required_monthly_contribution" in metrics
        assert "allocation_suggestion" in metrics

        print(f"✅ Goal projections calculated")
        print(f"   - Monthly contribution: ${metrics.get('required_monthly_contribution', 0):,.2f}")
        print(f"   - Years to goal: {metrics.get('projected_years_to_goal', 0):.1f}")
        print(f"   - Allocation: {metrics.get('allocation_suggestion', {})}")

    print("\n✅ TEST 4: Goal Planning Agent - PASSED\n")
    return True


async def test_tax_education_agent():
    """Test Tax Education Agent (Phase 2B)"""
    print("\n" + "="*70)
    print("TEST 5: Tax Education Agent (Phase 2B)")
    print("="*70)

    agent = get_tax_education_agent()

    queries = [
        "What is tax-loss harvesting?",
        "How are dividends taxed?",
        "What's the difference between traditional and Roth IRA?",
    ]

    for i, query in enumerate(queries, 1):
        print(f"\n🏛️ Query {i}: {query}")
        print("-" * 50)

        output = await agent.execute(
            query,
            tax_data={"category_filter": "tax"}
        )

        assert output.answer_text, "Should have answer"

        print(f"✅ Tax information provided ({len(output.answer_text)} chars)")
        print(f"   - Tools used: {output.tool_calls_made}")
        print(f"   - Citations: {len(output.citations)}")

        # Check for disclaimer
        answer_lower = output.answer_text.lower()
        has_disclaimer = any(
            kw in answer_lower 
            for kw in ["not tax advice", "educational", "consult", "professional"]
        )
        print(f"   - Disclaimer included: {'✅' if has_disclaimer else '⚠️'}")

    print("\n✅ TEST 5: Tax Education Agent - PASSED\n")
    return True


async def test_news_synthesizer_agent():
    """Test News Synthesizer Agent (Phase 2B)"""
    print("\n" + "="*70)
    print("TEST 6: News Synthesizer Agent (Phase 2B)")
    print("="*70)

    agent = get_news_synthesizer_agent()

    test_cases = [
        {
            "name": "Market news for single ticker",
            "message": "What's the latest news on Apple?",
            "data": {"tickers": ["AAPL"]}
        },
        {
            "name": "Market topic overview",
            "message": "What's happening in the tech sector?",
            "data": {"topic": "technology"}
        }
    ]

    for case in test_cases:
        print(f"\n📰 Test Case: {case['name']}")
        print("-" * 50)

        output = await agent.execute(
            case['message'],
            news_data=case['data']
        )

        assert output.answer_text, "Should have news summary"
        assert output.structured_data, "Should have structured data"

        data = output.structured_data
        assert "overall_sentiment" in data
        assert "timestamp" in data

        print(f"✅ News synthesized")
        print(f"   - Sentiment: {data.get('overall_sentiment', 'unknown')}")
        print(f"   - News items: {len(data.get('news_items', []))}")
        print(f"   - Tools used: {output.tool_calls_made}")

    print("\n✅ TEST 6: News Synthesizer Agent - PASSED\n")
    return True


async def test_agent_integration():
    """Test agents working together (simulation)"""
    print("\n" + "="*70)
    print("INTEGRATION TEST: Multi-Agent Workflow")
    print("="*70)
    print("\n📋 Scenario: User wants complete portfolio analysis and planning")
    print("-" * 70)

    # Step 1: Portfolio Analysis
    print("\n1️⃣ Analyzing current portfolio...")
    portfolio_agent = get_portfolio_analysis_agent()
    portfolio_output = await portfolio_agent.execute(
        "Analyze my portfolio",
        holdings_data={
            "holdings": [
                {"ticker": "AAPL", "quantity": 100, "current_price": 189.95, "cost_basis": 150.0},
                {"ticker": "BND", "quantity": 200, "current_price": 82.30, "cost_basis": 85.0},
            ],
            "analysis_type": "full"
        }
    )

    portfolio_value = portfolio_output.structured_data.get('total_portfolio_value', 0)
    diversification = portfolio_output.structured_data.get('diversification_score', 0)
    print(f"   ✅ Current portfolio value: ${portfolio_value:,.2f}")
    print(f"   ✅ Diversification score: {diversification:.1f}/100")

    # Step 2: Goal Planning
    print("\n2️⃣ Planning to reach $100k in 5 years...")
    goal_agent = get_goal_planning_agent()
    goal_output = await goal_agent.execute(
        "Help me reach $100k",
        goal_data={
            "current_value": portfolio_value,
            "goal_amount": 100000,
            "time_horizon_years": 5,
            "risk_appetite": "moderate",
            "current_return": 6.0
        }
    )

    monthly_contrib = goal_output.structured_data.get('required_monthly_contribution', 0)
    print(f"   ✅ Required monthly contribution: ${monthly_contrib:,.2f}")

    # Step 3: Tax Planning
    print("\n3️⃣ Getting tax considerations...")
    tax_agent = get_tax_education_agent()
    tax_output = await tax_agent.execute(
        "What tax considerations should I know about investing?"
    )
    print(f"   ✅ Tax guidance retrieved ({len(tax_output.answer_text)} chars)")

    # Step 4: Market News
    print("\n4️⃣ Checking market sentiment...")
    news_agent = get_news_synthesizer_agent()
    news_output = await news_agent.execute(
        "What's the market sentiment?",
        news_data={"topic": "market"}
    )
    sentiment = news_output.structured_data.get('overall_sentiment', 'neutral')
    print(f"   ✅ Overall market sentiment: {sentiment}")

    print("\n✅ INTEGRATION TEST: Multi-Agent Workflow - PASSED\n")
    return True


async def run_all_agent_tests():
    """Run all agent tests"""
    print("\n" + "="*70)
    print("COMPREHENSIVE AGENT SUITE TEST")
    print("Testing all 6 agents (Phase 1 + 2A + 2B)")
    print("="*70)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}")

    tests = [
        ("Finance Q&A Agent (Phase 1)", test_finance_qa_agent),
        ("Portfolio Analysis Agent (Phase 2A)", test_portfolio_analysis_agent),
        ("Market Analysis Agent (Phase 2A)", test_market_analysis_agent),
        ("Goal Planning Agent (Phase 2B)", test_goal_planning_agent),
        ("Tax Education Agent (Phase 2B)", test_tax_education_agent),
        ("News Synthesizer Agent (Phase 2B)", test_news_synthesizer_agent),
        ("Multi-Agent Integration", test_agent_integration),
    ]

    results = []

    for test_name, test_func in tests:
        try:
            result = await test_func()
            results.append((test_name, "✅ PASS"))
        except AssertionError as e:
            results.append((test_name, f"❌ FAIL: {str(e)}"))
            print(f"\n❌ Test failed: {e}\n")
        except Exception as e:
            results.append((test_name, f"❌ ERROR: {str(e)}"))
            print(f"\n❌ Unexpected error: {e}\n")

    # Print summary
    print("\n" + "="*70)
    print("COMPREHENSIVE AGENT SUITE TEST SUMMARY")
    print("="*70)

    for test_name, result in results:
        print(f"{test_name:45} {result}")

    passed = sum(1 for _, r in results if "✅" in r)
    total = len(results)

    print(f"\n{'='*70}")
    print(f"Total: {passed}/{total} tests passed")
    print(f"{'='*70}")

    print("\n" + "="*70)
    print("AGENT SUITE STATUS")
    print("="*70)
    print(f"✅ Finance Q&A Agent:        {'Ready' if any('Finance Q&A' in t[0] and '✅' in t[1] for t in results) else 'Failed'}")
    print(f"✅ Portfolio Analysis Agent: {'Ready' if any('Portfolio Analysis' in t[0] and '✅' in t[1] for t in results) else 'Failed'}")
    print(f"✅ Market Analysis Agent:    {'Ready' if any('Market Analysis' in t[0] and '✅' in t[1] for t in results) else 'Failed'}")
    print(f"✅ Goal Planning Agent:      {'Ready' if any('Goal Planning' in t[0] and '✅' in t[1] for t in results) else 'Failed'}")
    print(f"✅ Tax Education Agent:      {'Ready' if any('Tax Education' in t[0] and '✅' in t[1] for t in results) else 'Failed'}")
    print(f"✅ News Synthesizer Agent:   {'Ready' if any('News Synthesizer' in t[0] and '✅' in t[1] for t in results) else 'Failed'}")

    print(f"\n✅ COMPREHENSIVE INTEGRATION: {'Ready' if any('Integration' in t[0] and '✅' in t[1] for t in results) else 'Failed'}\n")

    if passed == total:
        print("🎉 ALL AGENTS OPERATIONAL - SYSTEM READY\n")
        return 0
    else:
        print(f"❌ {total - passed} test(s) failed\n")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(run_all_agent_tests())
    sys.exit(exit_code)
