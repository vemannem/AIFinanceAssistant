#!/usr/bin/env python3
"""Test Goal Planning endpoint for LangGraph metrics"""

import requests
import json
import time

print("\n🧪 TESTING GOAL PLANNING FLOW WITH LANGGRAPH STATE CAPTURE")
print("=" * 70)

# Test data matching the form
goal_data = {
    "current_value": 50000,
    "goal_amount": 100000,
    "time_horizon_years": 5,
    "risk_appetite": "moderate",
    "current_return": 6.0,
    "session_id": f"langgraph-state-test-{int(time.time())}"
}

print("\n📋 REQUEST DETAILS:")
print(f"   Endpoint: POST /api/agents/goal-planning")
print(f"   Current Value: ${goal_data['current_value']:,.0f}")
print(f"   Goal Amount: ${goal_data['goal_amount']:,.0f}")
print(f"   Time Horizon: {goal_data['time_horizon_years']} years")
print(f"   Risk Appetite: {goal_data['risk_appetite']}")
print(f"   Session ID: {goal_data['session_id']}")
print("\n⏳ Waiting for response (timeout: 60 seconds)...\n")

try:
    start = time.time()
    response = requests.post(
        "http://localhost:8000/api/agents/goal-planning",
        json=goal_data,
        timeout=60
    )
    elapsed = time.time() - start
    
    print(f"✅ Response received in {elapsed:.2f} seconds")
    print(f"   Status Code: {response.status_code}\n")
    
    if response.status_code == 200:
        data = response.json()
        
        print("📊 EXECUTION METRICS (These populate LangGraph State Tab):")
        print("   " + "-" * 60)
        
        metrics = {
            'confidence': data.get('confidence'),
            'intent': data.get('intent'),
            'agents_used': data.get('agents_used'),
            'execution_times': data.get('execution_times'),
            'total_time_ms': data.get('total_time_ms'),
        }
        
        for key, value in metrics.items():
            status = "✓" if value is not None else "✗"
            print(f"   {status} {key}: {value}")
        
        print("   " + "-" * 60)
        
        # Check for missing metrics
        missing = [k for k, v in metrics.items() if v is None]
        
        if missing:
            print(f"\n⚠️  MISSING METRICS: {missing}")
            print("🔴 LangGraph State Tab will NOT display properly!")
        else:
            print("\n✅ All required metrics present!")
            print("🟢 LangGraph State Tab SHOULD display properly")
        
        # Show response snippet
        print("\n📝 Response Message:")
        msg = data.get('message', '')
        print(f"   {msg[:120]}...")
        
        print("\n💾 Structured Data Available:")
        if data.get('structured_data'):
            keys = list(data['structured_data'].keys())[:5]
            for key in keys:
                print(f"   - {key}")
            if len(data['structured_data']) > 5:
                print(f"   ... and {len(data['structured_data']) - 5} more")
        
        print("\n" + "=" * 70)
        print("FULL RESPONSE (for debugging):")
        print(json.dumps(data, indent=2, default=str)[:1000])
        
    else:
        print(f"\n❌ Error: Status {response.status_code}")
        print(f"Response: {response.text[:300]}")
        
except requests.exceptions.Timeout:
    print("\n❌ TIMEOUT: Request exceeded 60 seconds")
    print("   Backend may be processing too slowly or not running")
    
except requests.exceptions.ConnectionError:
    print("\n❌ CONNECTION ERROR: Cannot reach http://localhost:8000")
    print("   Make sure backend is running: python -m src.web_app.main")
    
except Exception as e:
    print(f"\n❌ ERROR: {type(e).__name__}: {str(e)}")

print("\n" + "=" * 70)
