#!/usr/bin/env python3
"""
Phase 2B Testing Suite - Tests for Goal Planning, Tax Education, and News Synthesizer Agents

Run with: /usr/bin/python3 test_phase2b.py
"""

import asyncio
import sys
from datetime import datetime

# Test imports
from src.agents.goal_planning import get_goal_planning_agent
from src.agents.tax_education import get_tax_education_agent
from src.agents.news_synthesizer import get_news_synthesizer_agent


async def test_goal_planning_agent():
    """Test Goal Planning Agent"""
    print("\n" + "="*70)
    print("TEST 1: Goal Planning Agent")
    print("="*70)

    agent = get_goal_planning_agent()

    # Test case 1: Basic goal projection
    print("\n📊 Test Case 1: Basic Goal Projection")
    print("-" * 50)

    goal_data = {
        "current_value": 10000,
        "goal_amount": 100000,
        "time_horizon_years": 10,
        "risk_appetite": "moderate",
        "current_return": 6.0
    }

    output = await agent.execute(
        "I have $10k and want to reach $100k in 10 years. What should I do?",
        goal_data=goal_data
    )

    print(f"✅ Agent executed successfully")
    print(f"   - Answer length: {len(output.answer_text)} chars")
    print(f"   - Tools used: {output.tool_calls_made}")
    print(f"   - Structured data keys: {list(output.structured_data.keys())}")

    # Check structured data
    assert output.structured_data, "Should have structured data"
    assert "required_monthly_contribution" in output.structured_data
    assert "projected_value_with_contributions" in output.structured_data
    assert "allocation_suggestion" in output.structured_data

    monthly_contrib = output.structured_data["required_monthly_contribution"]
    print(f"   - Required monthly contribution: ${monthly_contrib:,.2f}")
    print(f"   - Projected years to goal: {output.structured_data['projected_years_to_goal']:.1f}")
    print(f"   - Risk level: {output.structured_data['risk_level']}")

    # Test case 2: Already at goal
    print("\n📊 Test Case 2: Already at Goal")
    print("-" * 50)

    goal_data_achieved = {
        "current_value": 100000,
        "goal_amount": 100000,
        "time_horizon_years": 5,
        "risk_appetite": "low"
    }

    output2 = await agent.execute(
        "I have $100k. Can I maintain this goal?",
        goal_data=goal_data_achieved
    )

    assert output2.answer_text
    assert "monthly" in output2.answer_text.lower() or "contribution" in output2.answer_text.lower()
    print(f"✅ Handled goal achievement correctly")

    # Test case 3: Short term high growth
    print("\n📊 Test Case 3: Short Term High Growth")
    print("-" * 50)

    goal_data_short = {
        "current_value": 50000,
        "goal_amount": 75000,
        "time_horizon_years": 2,
        "risk_appetite": "high",
        "current_return": 8.5
    }

    output3 = await agent.execute(
        "I need $75k in 2 years. I can take risks.",
        goal_data=goal_data_short
    )

    allocation = output3.structured_data.get("allocation_suggestion", {})
    print(f"✅ Short-term allocation: {allocation}")
    assert allocation.get("stocks", 0) >= 40, "Short-term high risk should have at least 40% stocks"

    print("\n✅ TEST 1: Goal Planning Agent - ALL TESTS PASSED\n")
    return True


async def test_tax_education_agent():
    """Test Tax Education Agent"""
    print("\n" + "="*70)
    print("TEST 2: Tax Education Agent")
    print("="*70)

    agent = get_tax_education_agent()

    # Test case 1: Capital gains question
    print("\n🏛️ Test Case 1: Capital Gains Question")
    print("-" * 50)

    tax_data = {
        "category_filter": "capital_gains"
    }

    output = await agent.execute(
        "What's the difference between long-term and short-term capital gains?",
        tax_data=tax_data
    )

    assert output.answer_text, "Should have answer"
    assert output.tool_calls_made, "Should have used tools"

    print(f"✅ Agent executed successfully")
    print(f"   - Answer length: {len(output.answer_text)} chars")
    print(f"   - Tools used: {output.tool_calls_made}")
    print(f"   - Citations count: {len(output.citations)}")
    print(f"   - Chunks retrieved: {output.structured_data.get('chunks_retrieved', 0)}")

    # Verify RAG was used
    assert "pinecone_retrieval" in output.tool_calls_made, "Should use RAG retrieval"
    assert "openai_chat" in output.tool_calls_made, "Should use LLM"

    # Test case 2: IRA/401k question
    print("\n🏛️ Test Case 2: Retirement Account Question")
    print("-" * 50)

    tax_data_2 = {
        "category_filter": "retirement"
    }

    output2 = await agent.execute(
        "Can I have both a 401k and an IRA at the same time?",
        tax_data=tax_data_2
    )

    assert output2.answer_text, "Should have answer"
    assert "401" in output2.answer_text or "ira" in output2.answer_text.lower()

    print(f"✅ Handled retirement account question")
    print(f"   - Citations: {len(output2.citations)}")

    # Test case 3: Tax strategy question
    print("\n🏛️ Test Case 3: Tax Strategy Question")
    print("-" * 50)

    output3 = await agent.execute(
        "What is tax-loss harvesting and how does it work?",
        tax_data={}
    )

    assert output3.answer_text, "Should have answer"
    print(f"✅ Explained tax strategy concept")
    print(f"   - Answer length: {len(output3.answer_text)} chars")

    # Check for disclaimers
    answer_lower = output3.answer_text.lower()
    disclaimer_keywords = ["educational", "not tax advice", "consult", "cpa", "professional"]
    has_disclaimer = any(keyword in answer_lower for keyword in disclaimer_keywords)
    assert has_disclaimer, "Should include tax advice disclaimer"
    print(f"   - Includes proper disclaimer: ✅")

    print("\n✅ TEST 2: Tax Education Agent - ALL TESTS PASSED\n")
    return True


async def test_news_synthesizer_agent():
    """Test News Synthesizer Agent"""
    print("\n" + "="*70)
    print("TEST 3: News Synthesizer Agent")
    print("="*70)

    agent = get_news_synthesizer_agent()

    # Test case 1: Single ticker news
    print("\n📰 Test Case 1: Single Ticker News")
    print("-" * 50)

    news_data = {
        "tickers": ["AAPL"],
        "period": "1w"
    }

    output = await agent.execute(
        "What's the news on Apple?",
        news_data=news_data
    )

    assert output.answer_text, "Should have news summary"
    assert output.structured_data, "Should have structured data"

    print(f"✅ Agent executed successfully")
    print(f"   - Answer length: {len(output.answer_text)} chars")
    print(f"   - Tools used: {output.tool_calls_made}")
    print(f"   - Overall sentiment: {output.structured_data.get('overall_sentiment', 'unknown')}")
    print(f"   - News items: {len(output.structured_data.get('news_items', []))}")
    print(f"   - Top stories: {len(output.structured_data.get('top_stories', []))}")

    # Verify structure
    assert "overall_sentiment" in output.structured_data
    assert "news_items" in output.structured_data
    assert output.structured_data["overall_sentiment"] in ["bullish", "neutral", "bearish"]

    # Test case 2: Multiple tickers
    print("\n📰 Test Case 2: Multiple Tickers Comparison")
    print("-" * 50)

    news_data_multi = {
        "tickers": ["AAPL", "GOOGL", "MSFT"]
    }

    output2 = await agent.execute(
        "Compare news on AAPL, GOOGL, and MSFT",
        news_data=news_data_multi
    )

    assert len(output2.structured_data.get("tickers", [])) == 3
    news_count = len(output2.structured_data.get("news_items", []))
    print(f"✅ Retrieved news for multiple tickers")
    print(f"   - Tickers: {output2.structured_data.get('tickers')}")
    print(f"   - Total news items: {news_count}")

    # Test case 3: Ticker extraction from message
    print("\n📰 Test Case 3: Ticker Extraction from Message")
    print("-" * 50)

    output3 = await agent.execute(
        "What's the news on TSLA and AMZN? Both stocks look interesting."
    )

    assert output3.answer_text, "Should extract tickers from message"
    print(f"✅ Extracted tickers from natural language")
    print(f"   - News items found: {len(output3.structured_data.get('news_items', []))}")

    # Test case 4: Market-wide topic
    print("\n📰 Test Case 4: Market Topic")
    print("-" * 50)

    news_data_topic = {
        "topic": "technology"
    }

    output4 = await agent.execute(
        "What's happening in tech?",
        news_data=news_data_topic
    )

    assert output4.answer_text, "Should have market overview"
    print(f"✅ Provided market topic overview")
    print(f"   - Topic: {output4.structured_data.get('topic', 'unknown')}")

    print("\n✅ TEST 3: News Synthesizer Agent - ALL TESTS PASSED\n")
    return True


async def run_all_tests():
    """Run all Phase 2B tests"""
    print("\n" + "="*70)
    print("PHASE 2B TESTING SUITE")
    print("="*70)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}")

    tests = [
        ("Goal Planning Agent", test_goal_planning_agent),
        ("Tax Education Agent", test_tax_education_agent),
        ("News Synthesizer Agent", test_news_synthesizer_agent),
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
    print("PHASE 2B TEST SUMMARY")
    print("="*70)

    for test_name, result in results:
        print(f"{test_name:40} {result}")

    passed = sum(1 for _, r in results if "✅" in r)
    total = len(results)

    print(f"\n{'='*70}")
    print(f"Total: {passed}/{total} tests passed")
    print(f"{'='*70}\n")

    if passed == total:
        print("✅ ALL PHASE 2B TESTS COMPLETE\n")
        return 0
    else:
        print(f"❌ {total - passed} test(s) failed\n")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(run_all_tests())
    sys.exit(exit_code)
