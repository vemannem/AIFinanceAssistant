"""
Test conversation manager - max history and rolling summary
"""

import asyncio
from src.core.conversation_manager import get_conversation_manager, ConversationManager
from src.orchestration.state import OrchestrationState


def test_conversation_manager_basic():
    """Test basic conversation manager functionality"""
    manager = ConversationManager(
        max_history=10,
        summary_threshold=5,
        summary_length=300
    )
    
    messages = [
        {"role": "user", "content": "What is portfolio diversification?"},
        {"role": "assistant", "content": "Diversification means spreading investments across different asset types..."},
        {"role": "user", "content": "Should I include bonds?"},
        {"role": "assistant", "content": "Yes, bonds provide stability..."},
    ]
    
    # Should not create summary for 4 messages
    assert not manager.should_create_summary(4)
    
    # Should create summary for 5+ messages
    assert manager.should_create_summary(5)
    
    # Trim should not affect small history
    trimmed, summary = manager.trim_history(messages)
    assert len(trimmed) == 4
    assert summary is None
    
    print("✅ Basic conversation manager test passed")


def test_conversation_summary_creation():
    """Test summary creation with key topics"""
    manager = ConversationManager(summary_length=200)
    
    messages = [
        {"role": "user", "content": "I have a portfolio with AAPL and bonds"},
        {"role": "assistant", "content": "Good diversification approach"},
        {"role": "user", "content": "What about ETFs for dividend yield?"},
        {"role": "assistant", "content": "ETFs are good for passive investing"},
        {"role": "user", "content": "How do I plan for retirement?"},
    ]
    
    summary = manager.create_summary(messages)
    
    # Check summary metadata
    assert summary.messages_included == 5
    assert len(summary.key_topics) > 0
    assert "Portfolio" in summary.key_topics or "Bonds" in summary.key_topics
    assert len(summary.summary_text) > 0
    assert len(summary.summary_text) <= manager.summary_length + 10  # Allow small overage for "..."
    
    print("✅ Summary creation test passed")
    print(f"   Topics: {summary.key_topics}")
    print(f"   Summary: {summary.summary_text[:100]}...")


def test_trim_history_creates_summary():
    """Test that trimming history creates summary when needed"""
    manager = ConversationManager(max_history=5)
    
    # Create 15 messages
    messages = [
        {"role": "user" if i % 2 == 0 else "assistant", "content": f"Message {i}: " + "about portfolio and diversification"}
        for i in range(15)
    ]
    
    trimmed, summary = manager.trim_history(messages)
    
    # Should trim to 5 messages
    assert len(trimmed) == 5
    
    # Should have created summary for the 10 trimmed messages
    assert summary is not None
    assert summary.messages_included == 10
    
    print("✅ Trim history test passed")
    print(f"   Original: {len(messages)}, Trimmed: {len(trimmed)}, Summary: {summary.messages_included} msgs")


def test_apply_summary_to_prompt():
    """Test applying summary to prompt context"""
    manager = ConversationManager()
    
    messages = [
        {"role": "user", "content": "What about portfolio diversification?"},
        {"role": "assistant", "content": "Diversification spreads risk across assets..."},
        {"role": "user", "content": "How much in stocks vs bonds?"},
        {"role": "assistant", "content": "This depends on your age and goals..."},
    ]
    
    # Without summary
    context = manager.apply_summary_to_prompt(messages, None)
    assert "Recent conversation:" in context
    assert len(context) > 0
    
    # With summary
    summary = manager.create_summary(messages[:2])
    context_with_summary = manager.apply_summary_to_prompt(messages[2:], summary)
    assert "Previous conversation summary:" in context_with_summary
    assert summary.summary_text in context_with_summary
    
    print("✅ Apply summary to prompt test passed")


def test_conversation_stats():
    """Test getting conversation statistics"""
    manager = ConversationManager()
    
    messages = [
        {"role": "user", "content": "Question 1"},
        {"role": "assistant", "content": "Answer 1"},
        {"role": "user", "content": "Question 2 is longer"},
        {"role": "assistant", "content": "Answer 2 is also longer"},
    ]
    
    stats = manager.get_stats(messages)
    
    assert stats["total_messages"] == 4
    assert stats["user_messages"] == 2
    assert stats["assistant_messages"] == 2
    assert stats["total_characters"] > 0
    assert not stats["needs_summary"]  # Only 4 messages
    
    print("✅ Conversation stats test passed")
    print(f"   Stats: {stats}")


async def test_orchestration_state_conversation():
    """Test conversation management in orchestration state"""
    state = OrchestrationState(user_input="What is portfolio diversification?")
    
    # Add messages
    state.add_message("user", "What is portfolio diversification?")
    state.add_message("assistant", "Diversification means spreading investments...")
    state.add_message("user", "Should I add bonds?")
    state.add_message("assistant", "Yes, bonds provide stability...")
    
    assert len(state.conversation_history) == 4
    
    # Get context (should work without error)
    context = state.get_conversation_context()
    assert len(context) > 0
    assert "Recent conversation" in context or "Previous conversation summary" in context
    
    print("✅ Orchestration state conversation test passed")
    print(f"   Context length: {len(context)} chars")


if __name__ == "__main__":
    print("Running Conversation Manager Tests...\n")
    
    test_conversation_manager_basic()
    test_conversation_summary_creation()
    test_trim_history_creates_summary()
    test_apply_summary_to_prompt()
    test_conversation_stats()
    
    print("\nRunning async tests...")
    asyncio.run(test_orchestration_state_conversation())
    
    print("\n✅ All conversation manager tests passed!")
