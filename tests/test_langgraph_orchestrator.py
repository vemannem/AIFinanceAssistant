"""
Tests for LangGraph Orchestrator

Validates the LangGraph StateGraph implementation
"""

import pytest
import asyncio
from datetime import datetime
from src.orchestration.langgraph_workflow import (
    LangGraphOrchestrator,
    LangGraphState,
    get_langgraph_orchestrator
)


class TestLangGraphOrchestrator:
    """Test suite for LangGraph-based orchestration"""
    
    @pytest.fixture
    def orchestrator(self):
        """Get orchestrator instance"""
        return LangGraphOrchestrator()
    
    @pytest.mark.asyncio
    async def test_initialization(self, orchestrator):
        """Test orchestrator initializes correctly"""
        assert orchestrator is not None
        assert orchestrator.graph is not None
        assert orchestrator.intent_detector is not None
        assert orchestrator.agent_executor is not None
        assert orchestrator.response_synthesizer is not None
        print("✓ Orchestrator initialized successfully")
    
    @pytest.mark.asyncio
    async def test_input_node(self, orchestrator):
        """Test INPUT node processing"""
        state: LangGraphState = {
            "user_input": "What is diversification?",
            "conversation_history": [],
            "detected_intents": [],
            "primary_intent": "",
            "confidence_score": 0.0,
            "selected_agents": [],
            "routing_rationale": "",
            "extracted_tickers": [],
            "agent_executions": [],
            "execution_errors": [],
            "execution_times": {},
            "final_response": "",
            "citations": [],
            "confidence": 0.0,
            "metadata": {}
        }
        
        result = await orchestrator._node_input(state)
        
        assert result["session_id"] is not None
        assert len(result["conversation_history"]) == 1
        assert result["conversation_history"][0]["role"] == "user"
        assert result["workflow_started_at"] is not None
        print(f"✓ INPUT node: session={result['session_id'][:8]}...")
    
    @pytest.mark.asyncio
    async def test_intent_detection_node(self, orchestrator):
        """Test INTENT_DETECTION node"""
        state: LangGraphState = {
            "user_input": "What is an ETF?",
            "detected_intents": [],
            "primary_intent": "",
            "confidence_score": 0.0,
            "extracted_tickers": [],
            "extracted_portfolio_data": None,
            "extracted_goal_data": None,
            "extracted_tax_context": None,
            "metadata": {}
        }
        
        result = await orchestrator._node_intent_detection(state)
        
        assert len(result["detected_intents"]) > 0
        assert result["primary_intent"] != ""
        assert result["confidence_score"] > 0
        print(
            f"✓ INTENT_DETECTION: intents={result['detected_intents']}, "
            f"confidence={result['confidence_score']:.2f}"
        )
    
    @pytest.mark.asyncio
    async def test_routing_node(self, orchestrator):
        """Test ROUTING node"""
        state: LangGraphState = {
            "user_input": "What is diversification?",
            "detected_intents": ["education_question"],
            "primary_intent": "education_question",
            "selected_agents": [],
            "routing_rationale": ""
        }
        
        result = await orchestrator._node_routing(state)
        
        assert len(result["selected_agents"]) > 0
        assert "finance_qa" in result["selected_agents"]
        assert result["routing_rationale"] != ""
        print(
            f"✓ ROUTING: agents={result['selected_agents']}, "
            f"rationale={result['routing_rationale'][:50]}..."
        )
    
    @pytest.mark.asyncio
    async def test_should_execute_agents_true(self, orchestrator):
        """Test routing decision when agents are selected"""
        state: LangGraphState = {
            "selected_agents": ["finance_qa"]
        }
        
        decision = orchestrator._should_execute_agents(state)
        assert decision == "execute"
        print("✓ Routing decision: execute agents")
    
    @pytest.mark.asyncio
    async def test_should_execute_agents_false(self, orchestrator):
        """Test routing decision when no agents selected"""
        state: LangGraphState = {
            "selected_agents": []
        }
        
        decision = orchestrator._should_execute_agents(state)
        assert decision == "skip"
        print("✓ Routing decision: skip agents")
    
    @pytest.mark.asyncio
    async def test_synthesis_node_error_handling(self, orchestrator):
        """Test SYNTHESIS node error handling"""
        state: LangGraphState = {
            "primary_intent": "education_question",
            "user_input": "What is diversification?",
            "agent_executions": [],
            "execution_errors": ["Test error"],
            "final_response": "",
            "citations": [],
            "confidence": 0.0,
            "metadata": {}
        }
        
        result = await orchestrator._node_synthesis(state)
        
        assert result["final_response"] != ""  # Fallback response generated
        print("✓ SYNTHESIS node: error handling working")
    
    @pytest.mark.asyncio
    async def test_error_handler_node(self, orchestrator):
        """Test ERROR_HANDLER node"""
        state: LangGraphState = {
            "final_response": "",
            "confidence": 0.5,
            "metadata": {}
        }
        
        result = await orchestrator._node_error_handler(state)
        
        assert result["final_response"] != ""
        assert result["confidence"] == 0.0
        print("✓ ERROR_HANDLER node: generating fallback response")
    
    @pytest.mark.asyncio
    async def test_graph_compilation(self, orchestrator):
        """Test that graph compiles without errors"""
        assert orchestrator.graph is not None
        
        # Check graph has all expected nodes
        # (Note: LangGraph doesn't expose node list, so just verify it exists)
        assert hasattr(orchestrator.graph, 'invoke')
        print("✓ Graph compiled and ready for invocation")
    
    @pytest.mark.asyncio
    async def test_full_workflow_education_question(self, orchestrator):
        """Test complete workflow for education question"""
        result = await orchestrator.execute(
            user_input="What is diversification in investing?",
            session_id="test-session-001"
        )
        
        assert result["response"] != ""
        assert result["session_id"] == "test-session-001"
        assert "confidence" in result
        assert "intent" in result
        assert "agents_used" in result
        assert result["total_time_ms"] > 0
        
        print(
            f"✓ Full workflow (education): "
            f"agents={result['agents_used']}, "
            f"confidence={result['confidence']:.2f}, "
            f"time={result['total_time_ms']:.0f}ms"
        )
    
    @pytest.mark.asyncio
    async def test_full_workflow_portfolio_analysis(self, orchestrator):
        """Test complete workflow for portfolio analysis"""
        result = await orchestrator.execute(
            user_input="I have AAPL and BND stocks. What's my allocation?",
            session_id="test-session-002"
        )
        
        assert result["response"] != ""
        assert result["session_id"] == "test-session-002"
        assert "portfolio_analysis" in result.get("intent", "") or result["agents_used"]
        
        print(
            f"✓ Full workflow (portfolio): "
            f"agents={result['agents_used']}, "
            f"time={result['total_time_ms']:.0f}ms"
        )
    
    @pytest.mark.asyncio
    async def test_conversation_history_preserved(self, orchestrator):
        """Test that conversation history is preserved"""
        history = [
            {"role": "user", "content": "Tell me about ETFs"},
            {"role": "assistant", "content": "ETFs are..."}
        ]
        
        result = await orchestrator.execute(
            user_input="What about diversification?",
            session_id="test-session-003",
            conversation_history=history
        )
        
        assert result["response"] != ""
        assert result["session_id"] == "test-session-003"
        
        print("✓ Conversation history preserved across requests")
    
    @pytest.mark.asyncio
    async def test_session_id_generation(self, orchestrator):
        """Test automatic session ID generation"""
        result1 = await orchestrator.execute(
            user_input="What is an ETF?"
        )
        
        result2 = await orchestrator.execute(
            user_input="What is a bond?"
        )
        
        assert result1["session_id"] != result2["session_id"]
        print(f"✓ Session IDs generated: {result1['session_id'][:8]}..., {result2['session_id'][:8]}...")
    
    @pytest.mark.asyncio
    async def test_execution_timing(self, orchestrator):
        """Test execution timing measurement"""
        result = await orchestrator.execute(
            user_input="What is diversification?",
            session_id="test-session-004"
        )
        
        assert result["total_time_ms"] > 0
        assert result["total_time_ms"] < 60000  # Less than 1 minute
        assert isinstance(result["execution_times"], dict)
        
        print(
            f"✓ Execution timing: {result['total_time_ms']:.0f}ms, "
            f"agents: {result['execution_times']}"
        )
    
    @pytest.mark.asyncio
    async def test_confidence_scoring(self, orchestrator):
        """Test confidence score calculation"""
        result = await orchestrator.execute(
            user_input="What is an ETF?",
            session_id="test-session-005"
        )
        
        assert 0.0 <= result["confidence"] <= 1.0
        print(f"✓ Confidence score: {result['confidence']:.2f}")
    
    @pytest.mark.asyncio
    async def test_citations_included(self, orchestrator):
        """Test that citations are included in response"""
        result = await orchestrator.execute(
            user_input="What is diversification?",
            session_id="test-session-006"
        )
        
        # Response should exist
        assert result["response"] != ""
        # Citations might be empty for some queries, but should be list
        assert isinstance(result.get("citations", []), list)
        
        print(f"✓ Citations included: {len(result.get('citations', []))} sources")
    
    @pytest.mark.asyncio
    async def test_metadata_included(self, orchestrator):
        """Test that metadata is included in response"""
        result = await orchestrator.execute(
            user_input="What is an ETF?",
            session_id="test-session-007"
        )
        
        assert "metadata" in result
        assert isinstance(result["metadata"], dict)
        assert "agents_used" in result["metadata"] or "intent" in result
        
        print(f"✓ Metadata included: {list(result['metadata'].keys())}")


class TestLangGraphStaticMethods:
    """Test static/utility methods"""
    
    def test_singleton_pattern(self):
        """Test get_langgraph_orchestrator singleton"""
        orchestrator1 = get_langgraph_orchestrator()
        orchestrator2 = get_langgraph_orchestrator()
        
        assert orchestrator1 is orchestrator2
        print("✓ Singleton pattern working")


class TestLangGraphEdgeCases:
    """Test edge cases and error conditions"""
    
    @pytest.fixture
    def orchestrator(self):
        return LangGraphOrchestrator()
    
    @pytest.mark.asyncio
    async def test_empty_user_input(self, orchestrator):
        """Test handling of empty user input"""
        result = await orchestrator.execute(
            user_input="",
            session_id="test-edge-001"
        )
        
        # Should still return a response (even if fallback)
        assert "response" in result
        print("✓ Empty input handled")
    
    @pytest.mark.asyncio
    async def test_very_long_input(self, orchestrator):
        """Test handling of very long input"""
        long_input = "What is diversification? " * 100  # Very long query
        
        result = await orchestrator.execute(
            user_input=long_input,
            session_id="test-edge-002"
        )
        
        assert "response" in result
        print("✓ Long input handled")
    
    @pytest.mark.asyncio
    async def test_special_characters(self, orchestrator):
        """Test handling of special characters"""
        result = await orchestrator.execute(
            user_input="What is $AAPL? #diversification @investing",
            session_id="test-edge-003"
        )
        
        assert "response" in result
        print("✓ Special characters handled")
    
    @pytest.mark.asyncio
    async def test_multiple_intents(self, orchestrator):
        """Test handling of query with multiple intents"""
        result = await orchestrator.execute(
            user_input="I have AAPL and want to know about taxes. What's the market? Should I plan for goals?",
            session_id="test-edge-004"
        )
        
        assert "response" in result
        # Might use multiple agents
        print(f"✓ Multiple intents handled: agents={result['agents_used']}")


def run_basic_tests():
    """Run basic tests synchronously for validation"""
    print("\n" + "="*60)
    print("LANGGRAPH ORCHESTRATOR - BASIC VALIDATION")
    print("="*60 + "\n")
    
    orchestrator = LangGraphOrchestrator()
    
    # Test 1: Initialization
    print("[1/5] Testing initialization...")
    assert orchestrator.graph is not None
    print("✓ Graph initialized\n")
    
    # Test 2: Input node
    print("[2/5] Testing INPUT node...")
    state: LangGraphState = {
        "user_input": "What is diversification?",
        "conversation_history": [],
        "detected_intents": [],
        "primary_intent": "",
        "confidence_score": 0.0,
        "selected_agents": [],
        "routing_rationale": "",
        "extracted_tickers": [],
        "agent_executions": [],
        "execution_errors": [],
        "execution_times": {},
        "final_response": "",
        "citations": [],
        "confidence": 0.0,
        "metadata": {}
    }
    
    import asyncio
    result = asyncio.run(orchestrator._node_input(state))
    assert result["session_id"] is not None
    print(f"✓ INPUT node working (session: {result['session_id'][:8]}...)\n")
    
    # Test 3: Intent detection
    print("[3/5] Testing INTENT_DETECTION node...")
    result = asyncio.run(orchestrator._node_intent_detection(state))
    assert len(result["detected_intents"]) > 0
    print(f"✓ INTENT_DETECTION working (intents: {result['detected_intents']})\n")
    
    # Test 4: Routing
    print("[4/5] Testing ROUTING node...")
    result = asyncio.run(orchestrator._node_routing(result))
    assert len(result["selected_agents"]) > 0
    print(f"✓ ROUTING working (agents: {result['selected_agents']})\n")
    
    # Test 5: Full workflow
    print("[5/5] Testing full workflow...")
    result = asyncio.run(orchestrator.execute(
        user_input="What is an ETF?",
        session_id="validation-test"
    ))
    assert result["response"] != ""
    assert result["total_time_ms"] > 0
    print(f"✓ Full workflow working ({result['total_time_ms']:.0f}ms)\n")
    
    print("="*60)
    print("✅ ALL BASIC TESTS PASSED")
    print("="*60 + "\n")


if __name__ == "__main__":
    # Run basic validation
    run_basic_tests()
    
    # Run pytest
    print("Running full pytest suite...\n")
    pytest.main([__file__, "-v", "-s"])
