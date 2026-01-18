#!/usr/bin/env python3
"""
Frontend Chat E2E Testing Script
Tests chat features: different queries, citations, error handling, session management
"""

import requests
import json
import time
import uuid
from datetime import datetime

BASE_URL = "http://localhost:8000/api"
SESSION_ID = str(uuid.uuid4())

def print_header(title):
    """Print formatted header"""
    print(f"\n{'='*60}")
    print(f"📋 {title}")
    print(f"{'='*60}")

def print_test(test_name, status, details=""):
    """Print test result"""
    emoji = "✅" if status else "❌"
    print(f"{emoji} {test_name}")
    if details:
        print(f"   {details}")

def test_finance_qa_query(query, description):
    """Test finance Q&A endpoint"""
    try:
        response = requests.post(
            f"{BASE_URL}/chat/finance-qa",
            json={
                "message": query,
                "session_id": SESSION_ID
            },
            timeout=30
        )
        
        if response.status_code != 200:
            print_test(description, False, f"Status: {response.status_code}")
            return False
        
        data = response.json()
        
        # Validate response structure
        required_fields = ["session_id", "message", "citations", "timestamp"]
        missing = [f for f in required_fields if f not in data]
        
        if missing:
            print_test(description, False, f"Missing fields: {missing}")
            return False
        
        # Display response
        print_test(description, True)
        print(f"   Query: {query}")
        print(f"   Response: {data['message'][:100]}...")
        print(f"   Citations: {len(data.get('citations', []))}")
        if data.get('citations'):
            for i, citation in enumerate(data['citations'][:2], 1):
                print(f"     {i}. {citation.get('title', 'N/A')}")
        
        return True
    
    except requests.exceptions.Timeout:
        print_test(description, False, "Request timeout (30s)")
        return False
    except Exception as e:
        print_test(description, False, str(e))
        return False

def test_error_handling():
    """Test error handling"""
    print_header("Error Handling Tests")
    
    # Test 1: Empty message
    try:
        response = requests.post(
            f"{BASE_URL}/chat/finance-qa",
            json={"message": "", "session_id": SESSION_ID},
            timeout=5
        )
        # Backend may accept empty or reject - check behavior
        print_test("Empty message handling", response.status_code in [200, 400, 422])
    except Exception as e:
        print_test("Empty message handling", False, str(e))
    
    # Test 2: Missing session_id
    try:
        response = requests.post(
            f"{BASE_URL}/chat/finance-qa",
            json={"message": "test"},
            timeout=5
        )
        print_test("Missing session_id handling", response.status_code in [200, 400])
    except Exception as e:
        print_test("Missing session_id handling", False, str(e))
    
    # Test 3: Very long message
    try:
        long_msg = "a" * 10000
        response = requests.post(
            f"{BASE_URL}/chat/finance-qa",
            json={"message": long_msg, "session_id": SESSION_ID},
            timeout=30
        )
        print_test("Very long message", response.status_code == 200)
    except requests.exceptions.Timeout:
        print_test("Very long message", False, "Timeout")
    except Exception as e:
        print_test("Very long message", False, str(e))

def test_session_management():
    """Test session management"""
    print_header("Session Management Tests")
    
    session1 = str(uuid.uuid4())
    session2 = str(uuid.uuid4())
    
    # Send message in session 1
    try:
        r1 = requests.post(
            f"{BASE_URL}/chat/finance-qa",
            json={"message": "What is inflation?", "session_id": session1},
            timeout=30
        )
        
        # Send different message in session 2
        r2 = requests.post(
            f"{BASE_URL}/chat/finance-qa",
            json={"message": "What is deflation?", "session_id": session2},
            timeout=30
        )
        
        if r1.status_code == 200 and r2.status_code == 200:
            data1 = r1.json()
            data2 = r2.json()
            
            # Verify different sessions
            same_response = data1["message"] == data2["message"]
            print_test("Different sessions get different responses", not same_response)
            print(f"   Session 1: {data1['message'][:80]}...")
            print(f"   Session 2: {data2['message'][:80]}...")
            
            # Verify session IDs in response
            print_test("Session IDs preserved in response", 
                      data1["session_id"] == session1 and data2["session_id"] == session2)
        else:
            print_test("Session management", False, f"Status: {r1.status_code}, {r2.status_code}")
    
    except Exception as e:
        print_test("Session management", False, str(e))

def test_citations():
    """Test citations in responses"""
    print_header("Citations Tests")
    
    queries = [
        ("Tell me about stock market investing", "Market investing query"),
        ("What is portfolio diversification?", "Portfolio query"),
        ("Explain risk management in finance", "Risk management query")
    ]
    
    citation_count = 0
    queries_with_citations = 0
    
    for query, desc in queries:
        try:
            response = requests.post(
                f"{BASE_URL}/chat/finance-qa",
                json={"message": query, "session_id": SESSION_ID},
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                citations = data.get("citations", [])
                
                if citations:
                    queries_with_citations += 1
                    citation_count += len(citations)
                
                print_test(desc, True, f"{len(citations)} citations")
                for citation in citations[:2]:
                    print(f"     - {citation.get('title', 'N/A')}")
        
        except Exception as e:
            print_test(desc, False, str(e))
    
    print(f"\n📊 Citation Summary: {queries_with_citations}/{len(queries)} queries had citations")
    print(f"   Total citations: {citation_count}")

def test_diverse_queries():
    """Test different types of queries"""
    print_header("Diverse Query Tests")
    
    queries = [
        ("What is the current market trend?", "Market trend query"),
        ("How do I start investing?", "Investment beginner query"),
        ("Explain dividend reinvestment", "Specific finance concept"),
        ("What are ETFs?", "Finance terminology"),
        ("How do I build a portfolio?", "Portfolio building query"),
    ]
    
    success_count = 0
    for query, desc in queries:
        if test_finance_qa_query(query, desc):
            success_count += 1
        time.sleep(0.5)  # Small delay between requests
    
    print(f"\n📊 Query Success Rate: {success_count}/{len(queries)}")

def test_performance():
    """Test response times"""
    print_header("Performance Tests")
    
    queries = [
        "Hi",
        "What is a stock?",
        "Explain compound interest in detail with examples",
    ]
    
    times = []
    for i, query in enumerate(queries, 1):
        try:
            start = time.time()
            response = requests.post(
                f"{BASE_URL}/chat/finance-qa",
                json={"message": query, "session_id": SESSION_ID},
                timeout=30
            )
            elapsed = time.time() - start
            times.append(elapsed)
            
            status = "✅" if elapsed < 5 else "⚠️"
            print_test(f"Query {i} response time", elapsed < 10, f"{elapsed:.2f}s")
        
        except requests.exceptions.Timeout:
            print_test(f"Query {i} response time", False, "Timeout (>30s)")
    
    if times:
        print(f"\n📊 Performance Summary:")
        print(f"   Average: {sum(times)/len(times):.2f}s")
        print(f"   Min: {min(times):.2f}s")
        print(f"   Max: {max(times):.2f}s")

def main():
    """Run all tests"""
    print(f"\n🧪 Starting Frontend Chat E2E Tests")
    print(f"⏰ Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🔑 Session ID: {SESSION_ID}")
    
    # Check backend health
    try:
        response = requests.get(f"{BASE_URL.replace('/api', '')}/health", timeout=5)
        if response.status_code == 200:
            print("✅ Backend is healthy")
        else:
            print(f"⚠️  Backend status: {response.status_code}")
    except Exception as e:
        print(f"❌ Backend unreachable: {e}")
        return
    
    # Run test suites
    test_diverse_queries()
    test_error_handling()
    test_session_management()
    test_citations()
    test_performance()
    
    print(f"\n{'='*60}")
    print("✅ Testing Complete!")
    print(f"{'='*60}\n")

if __name__ == "__main__":
    main()
