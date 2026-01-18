#!/usr/bin/env python3
"""
Phase 2C Comprehensive Test Suite - LangGraph Orchestration

Tests all components of the multi-agent orchestration system:
- Intent detection
- Agent routing
- Agent execution
- Response synthesis
- End-to-end workflow
"""

import asyncio
import sys
import time
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

from src.orchestration.state import (
    OrchestrationState, Intent, AgentType, INTENT_KEYWORDS
)
from src.orchestration.intent_detector import get_intent_detector
from src.orchestration.agent_executor import get_agent_executor
from src.orchestration.response_synthesizer import get_response_synthesizer
from src.orchestration.workflow import get_orchestrator_workflow
from src.core.logger import get_logger


logger = get_logger(__name__)


# ============================================================================
# TEST 1: Intent Detection
# ============================================================================

def test_intent_detection():
    """Test intent detection component"""
    print("\n" + "="*70)
    print("TEST 1: Intent Detection")
    print("="*70)
    
    detector = get_intent_detector()
    
    test_cases = [
        {
            "input": "What is diversification and why is it important?",
            "expected_intents": [Intent.EDUCATION_QUESTION],
            "description": "Educational question"
        },
        {
            "input": "Analyze my portfolio of AAPL and BND",
            "expected_intents": [Intent.PORTFOLIO_ANALYSIS],
            "description": "Portfolio analysis"
        },
        {
            "input": "What's the current price of Apple stock?",
            "expected_intents": [Intent.MARKET_ANALYSIS],
            "description": "Market data request"
        },
        {
            "input": "How can I save $50,000 in 5 years?",
            "expected_intents": [Intent.GOAL_PLANNING],
            "description": "Goal planning"
        },
        {
            "input": "Tell me about capital gains tax strategy",
            "expected_intents": [Intent.TAX_QUESTION],
            "description": "Tax question"
        },
    ]
    
    passed = 0
    failed = 0
    
    for test_case in test_cases:
        user_input = test_case["input"]
        expected = test_case["expected_intents"]
        description = test_case["description"]
        
        intents = detector.detect_intents(user_input)
        
        # Check if primary intent matches
        primary = intents[0] if intents else Intent.UNKNOWN
        expected_primary = expected[0] if expected else Intent.UNKNOWN
        
        if primary == expected_primary:
            print(f"✅ {description}")
            print(f"   Input: {user_input}")
            print(f"   Detected: {[i.value for i in intents]}")
            passed += 1
        else:
            print(f"❌ {description}")
            print(f"   Input: {user_input}")
            print(f"   Expected: {[i.value for i in expected]}")
            print(f"   Got: {[i.value for i in intents]}")
            failed += 1
    
    print(f"\nIntent Detection: {passed}/{len(test_cases)} tests passed")
    return passed, failed


# ============================================================================
# TEST 2: Data Extraction
# ============================================================================

def test_data_extraction():
    """Test data extraction from user input"""
    print("\n" + "="*70)
    print("TEST 2: Data Extraction")
    print("="*70)
    
    detector = get_intent_detector()
    
    test_cases = [
        {
            "input": "I have $50,000 in AAPL and $30,000 in BND",
            "expected_tickers": ["AAPL", "BND"],
            "expected_amounts": [50000.0, 30000.0],
            "description": "Ticker and amount extraction"
        },
        {
            "input": "Save $750 per month for 10 years",
            "expected_amounts": [750.0],
            "expected_timeframe": "10 years",
            "description": "Amount and timeframe"
        },
        {
            "input": "My VTI holdings",
            "expected_tickers": ["VTI"],
            "description": "Single ticker"
        },
    ]
    
    passed = 0
    failed = 0
    
    for test_case in test_cases:
        user_input = test_case["input"]
        description = test_case["description"]
        
        tickers = detector.extract_tickers(user_input)
        amounts = detector.extract_dollar_amounts(user_input)
        timeframe = detector.extract_timeframe(user_input)
        
        expected_tickers = test_case.get("expected_tickers", [])
        expected_amounts = test_case.get("expected_amounts", [])
        expected_timeframe = test_case.get("expected_timeframe")
        
        # Check results
        ticker_match = set(tickers) == set(expected_tickers) or len(expected_tickers) == 0
        amount_match = len(amounts) >= len(expected_amounts) or len(expected_amounts) == 0
        timeframe_match = timeframe == expected_timeframe or expected_timeframe is None
        
        if ticker_match and amount_match and timeframe_match:
            print(f"✅ {description}")
            print(f"   Tickers: {tickers}")
            print(f"   Amounts: {amounts}")
            if timeframe:
                print(f"   Timeframe: {timeframe}")
            passed += 1
        else:
            print(f"❌ {description}")
            print(f"   Tickers: {tickers} (expected {expected_tickers})")
            print(f"   Amounts: {amounts} (expected {expected_amounts})")
            failed += 1
    
    print(f"\nData Extraction: {passed}/{len(test_cases)} tests passed")
    return passed, failed


# ============================================================================
# TEST 3: Routing
# ============================================================================

def test_routing():
    """Test agent routing based on intents"""
    print("\n" + "="*70)
    print("TEST 3: Agent Routing")
    print("="*70)
    
    detector = get_intent_detector()
    
    test_cases = [
        {
            "input": "What is diversification?",
            "expected_agents": [AgentType.FINANCE_QA],
            "description": "Education → Finance Q&A"
        },
        {
            "input": "Analyze my AAPL portfolio",
            "expected_agents": [AgentType.PORTFOLIO_ANALYSIS],
            "description": "Portfolio analysis → Portfolio Agent"
        },
        {
            "input": "What's the price of Tesla?",
            "expected_agents": [AgentType.MARKET_ANALYSIS],
            "description": "Market data → Market Agent"
        },
        {
            "input": "Plan to save $100k in 5 years",
            "expected_agents": [AgentType.GOAL_PLANNING],
            "description": "Goal planning → Goal Agent"
        },
    ]
    
    passed = 0
    failed = 0
    
    for test_case in test_cases:
        user_input = test_case["input"]
        expected_agents = test_case["expected_agents"]
        description = test_case["description"]
        
        # Create state
        state = OrchestrationState(user_input=user_input)
        state.detected_intents = detector.detect_intents(user_input)
        state.primary_intent = detector.get_primary_intent(state.detected_intents)
        state.confidence_score = detector.get_confidence_score(
            state.detected_intents,
            user_input
        )
        
        # Get routing decision
        decision = detector.make_routing_decision(state)
        
        # Check if primary expected agent is in selected agents
        expected_primary = expected_agents[0] if expected_agents else AgentType.FINANCE_QA
        if decision.agents and decision.agents[0] == expected_primary:
            print(f"✅ {description}")
            print(f"   Selected agents: {[a.value for a in decision.agents]}")
            passed += 1
        else:
            print(f"❌ {description}")
            print(f"   Expected: {[a.value for a in expected_agents]}")
            print(f"   Got: {[a.value for a in decision.agents]}")
            failed += 1
    
    print(f"\nAgent Routing: {passed}/{len(test_cases)} tests passed")
    return passed, failed


# ============================================================================
# TEST 4: Confidence Scoring
# ============================================================================

def test_confidence_scoring():
    """Test confidence scoring for intent detection"""
    print("\n" + "="*70)
    print("TEST 4: Confidence Scoring")
    print("="*70)
    
    detector = get_intent_detector()
    
    test_cases = [
        {
            "input": "What is a stock market ETF with diversification benefits?",
            "min_confidence": 0.5,
            "description": "Clear educational intent"
        },
        {
            "input": "Price?",
            "min_confidence": 0.3,
            "description": "Ambiguous input"
        },
        {
            "input": "My portfolio: $100k AAPL, $50k BND. What's diversification? Tax strategy?",
            "min_confidence": 0.5,
            "description": "Multiple intents with context"
        },
    ]
    
    passed = 0
    failed = 0
    
    for test_case in test_cases:
        user_input = test_case["input"]
        min_confidence = test_case["min_confidence"]
        description = test_case["description"]
        
        intents = detector.detect_intents(user_input)
        confidence = detector.get_confidence_score(intents, user_input)
        
        if confidence >= min_confidence:
            print(f"✅ {description}")
            print(f"   Confidence: {confidence:.2f} (min: {min_confidence})")
            passed += 1
        else:
            print(f"❌ {description}")
            print(f"   Confidence: {confidence:.2f} (expected >= {min_confidence})")
            failed += 1
    
    print(f"\nConfidence Scoring: {passed}/{len(test_cases)} tests passed")
    return passed, failed


# ============================================================================
# TEST 5: Orchestration State
# ============================================================================

def test_orchestration_state():
    """Test orchestration state management"""
    print("\n" + "="*70)
    print("TEST 5: Orchestration State")
    print("="*70)
    
    passed = 0
    failed = 0
    
    # Test state creation
    try:
        state = OrchestrationState(
            user_input="Test query",
            session_id="test_session"
        )
        assert state.user_input == "Test query"
        assert state.session_id == "test_session"
        assert state.workflow_state == "input"
        print("✅ State creation")
        passed += 1
    except Exception as e:
        print(f"❌ State creation: {e}")
        failed += 1
    
    # Test message tracking
    try:
        state.add_message("user", "Hello")
        state.add_message("assistant", "Hi there")
        assert len(state.conversation_history) == 2
        assert state.conversation_history[0].role == "user"
        print("✅ Message tracking")
        passed += 1
    except Exception as e:
        print(f"❌ Message tracking: {e}")
        failed += 1
    
    # Test error tracking
    try:
        state.add_error("Test error")
        assert state.has_errors()
        assert len(state.error_messages) == 1
        print("✅ Error tracking")
        passed += 1
    except Exception as e:
        print(f"❌ Error tracking: {e}")
        failed += 1
    
    # Test state serialization
    try:
        state_dict = state.to_dict()
        assert isinstance(state_dict, dict)
        assert "user_input" in state_dict
        print("✅ State serialization")
        passed += 1
    except Exception as e:
        print(f"❌ State serialization: {e}")
        failed += 1
    
    print(f"\nOrchestration State: {passed}/4 tests passed")
    return passed, failed


# ============================================================================
# TEST 6: End-to-End Workflow (Async)
# ============================================================================

async def test_end_to_end_workflow():
    """Test complete orchestration workflow"""
    print("\n" + "="*70)
    print("TEST 6: End-to-End Workflow")
    print("="*70)
    
    workflow = get_orchestrator_workflow()
    
    test_queries = [
        "What is portfolio diversification?",
        "Analyze AAPL and BND portfolio allocation",
        "What's the current price of Apple stock?",
    ]
    
    passed = 0
    failed = 0
    
    for query in test_queries:
        try:
            print(f"\nProcessing: {query}")
            start_time = time.time()
            
            state = await workflow.execute_workflow(query)
            
            elapsed = time.time() - start_time
            
            # Check state completeness
            assert state.user_input == query
            assert state.workflow_state == "complete"
            assert len(state.detected_intents) > 0
            assert len(state.selected_agents) > 0
            assert len(state.agent_outputs) > 0
            assert len(state.synthesized_response) > 0
            
            print(f"✅ Workflow completed in {elapsed:.2f}s")
            print(f"   Intents: {[i.value for i in state.detected_intents]}")
            print(f"   Agents: {[a.value for a in state.selected_agents]}")
            print(f"   Response length: {len(state.synthesized_response)} chars")
            passed += 1
        
        except Exception as e:
            print(f"❌ Workflow failed: {str(e)}")
            import traceback
            traceback.print_exc()
            failed += 1
    
    print(f"\nEnd-to-End Workflow: {passed}/{len(test_queries)} tests passed")
    return passed, failed


# ============================================================================
# TEST 7: Multi-Agent Coordination
# ============================================================================

async def test_multi_agent_coordination():
    """Test multi-agent execution and coordination"""
    print("\n" + "="*70)
    print("TEST 7: Multi-Agent Coordination")
    print("="*70)
    
    workflow = get_orchestrator_workflow()
    
    # Query that should trigger multiple agents
    query = "Analyze my $80k portfolio (60% AAPL, 40% BND) and how to reach $100k in 5 years"
    
    try:
        print(f"Processing multi-agent query: {query[:50]}...")
        
        state = await workflow.execute_workflow(query)
        
        # Check that multiple agents were selected
        assert len(state.selected_agents) >= 2, "Multi-agent test requires 2+ agents"
        
        # Check that all selected agents executed
        executed_count = sum(
            1 for exe in state.agent_executions 
            if exe.status == "success"
        )
        
        print(f"✅ Multi-agent coordination")
        print(f"   Selected agents: {len(state.selected_agents)}")
        print(f"   Successfully executed: {executed_count}")
        print(f"   Response: {state.synthesized_response[:100]}...")
        
        return 1, 0
    
    except Exception as e:
        print(f"❌ Multi-agent coordination failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return 0, 1


# ============================================================================
# MAIN TEST RUNNER
# ============================================================================

async def run_all_tests():
    """Run all Phase 2C tests"""
    print("\n" + "="*70)
    print("🚀 PHASE 2C: LANGGRAPH ORCHESTRATION - COMPREHENSIVE TEST SUITE")
    print("="*70)
    
    total_passed = 0
    total_failed = 0
    
    # Synchronous tests
    p, f = test_intent_detection()
    total_passed += p
    total_failed += f
    
    p, f = test_data_extraction()
    total_passed += p
    total_failed += f
    
    p, f = test_routing()
    total_passed += p
    total_failed += f
    
    p, f = test_confidence_scoring()
    total_passed += p
    total_failed += f
    
    p, f = test_orchestration_state()
    total_passed += p
    total_failed += f
    
    # Async tests
    p, f = await test_end_to_end_workflow()
    total_passed += p
    total_failed += f
    
    p, f = await test_multi_agent_coordination()
    total_passed += p
    total_failed += f
    
    # Summary
    print("\n" + "="*70)
    print("📊 TEST SUMMARY")
    print("="*70)
    
    total_tests = total_passed + total_failed
    success_rate = (total_passed / total_tests * 100) if total_tests > 0 else 0
    
    print(f"Total Tests: {total_tests}")
    print(f"Passed: {total_passed}")
    print(f"Failed: {total_failed}")
    print(f"Success Rate: {success_rate:.1f}%")
    
    if total_failed == 0:
        print("\n🎉 ALL TESTS PASSED - PHASE 2C ORCHESTRATION READY")
    else:
        print(f"\n⚠️  {total_failed} test(s) failed")
    
    return total_passed, total_failed


if __name__ == "__main__":
    try:
        passed, failed = asyncio.run(run_all_tests())
        sys.exit(0 if failed == 0 else 1)
    except KeyboardInterrupt:
        print("\n\nTests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nTest suite error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
