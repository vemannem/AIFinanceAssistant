#!/usr/bin/env python3
"""Test Goal Planning endpoint for LangGraph metrics - with longer timeout"""

import requests
import json
import time

print("\n" + "="*70)
print("🧪 TESTING GOAL PLANNING + LANGGRAPH STATE")
print("="*70)

# Test data
goal_data = {
    "current_value": 50000,
    "goal_amount": 100000,
    "time_horizon_years": 5,
    "risk_appetite": "moderate",
    "current_return": 6.0,
    "session_id": f"langgraph-test-{int(time.time())}"
}

print("\n📋 REQUEST:")
print(f"   Endpoint: POST /api/agents/goal-planning")
print(f"   Session: {goal_data['session_id']}")

print("\n⏳ Sending request (timeout: 120 seconds)...")

try:
    start = time.time()
    response = requests.post(
        "http://localhost:8000/api/agents/goal-planning",
        json=goal_data,
        timeout=120  # 2 minute timeout for LLM processing
    )
    elapsed = time.time() - start
    
    print(f"\n✅ Response received in {elapsed:.1f}s (Status: {response.status_code})\n")
    
    if response.status_code == 200:
        data = response.json()
        
        # Check execution metrics
        print("📊 LANGGRAPH EXECUTION METRICS:")
        print("-" * 70)
        
        metrics = {
            'confidence': data.get('confidence'),
            'intent': data.get('intent'),
            'agents_used': data.get('agents_used'),
            'execution_times': data.get('execution_times'),
            'total_time_ms': data.get('total_time_ms'),
        }
        
        for key, value in metrics.items():
            status = "✓" if value is not None else "✗ MISSING"
            print(f"   {status} {key:20s}: {value}")
        
        print("-" * 70)
        
        # Validate
        missing = [k for k, v in metrics.items() if v is None]
        
        if missing:
            print(f"\n⚠️  MISSING: {missing}")
            print("🔴 Frontend LangGraph State Tab will NOT work")
        else:
            print("\n✅ All metrics present!")
            print("🟢 Frontend will populate LangGraph State Tab correctly")
        
        # Show response content
        print(f"\n📝 Response message length: {len(data.get('message', ''))} chars")
        print(f"📦 Structured data keys: {list(data.get('structured_data', {}).keys())}")
        
    else:
        print(f"❌ Error {response.status_code}:")
        print(response.text[:500])
        
except requests.exceptions.Timeout:
    print(f"\n❌ TIMEOUT after 120 seconds")
except requests.exceptions.ConnectionError as e:
    print(f"\n❌ CONNECTION ERROR: {e}")
except Exception as e:
    print(f"\n❌ ERROR: {type(e).__name__}: {e}")

print("\n" + "="*70)
