#!/usr/bin/env python3
"""Test the backend RAG pipeline."""

import asyncio
import json
from src.core.config import Config
from src.agents.finance_qa import FinanceQAAgent

async def test_rag():
    """Test Finance Q&A agent with RAG."""
    print("\n🧪 Testing Finance Q&A Agent with RAG\n")
    
    # Validate config
    try:
        Config.validate()
        print("✅ Config validated")
    except Exception as e:
        print(f"❌ Config error: {e}")
        return
    
    # Create agent
    agent = FinanceQAAgent()
    print("✅ Agent initialized")
    
    # Test query
    test_queries = [
        "What is an ETF and how does it differ from a mutual fund?",
        "How do I calculate my portfolio allocation?",
        "What are capital gains taxes?",
    ]
    
    for query in test_queries:
        print(f"\n📝 Query: {query}")
        print("-" * 60)
        
        try:
            output = await agent.execute(query)
            
            print(f"✅ Answer: {output.answer_text[:200]}...")
            print(f"\n📚 Citations ({len(output.citations)}):")
            for i, cite in enumerate(output.citations, 1):
                print(f"   {i}. {cite['title']} (Category: {cite['category']})")
            
            print(f"\n🔧 Tools used: {', '.join(output.tool_calls_made)}")
            
        except Exception as e:
            print(f"❌ Error: {str(e)}")
    
    print("\n✅ Test complete!\n")


if __name__ == "__main__":
    asyncio.run(test_rag())
