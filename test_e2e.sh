#!/bin/bash

echo "🔍 E2E Frontend Test"
echo "==================="
echo ""
echo "Status: Both servers should be running"
echo "Frontend: http://localhost:5173/"
echo "Backend:  http://localhost:8000"
echo ""

# Test frontend
echo "Testing Frontend..."
FRONTEND_RESPONSE=$(curl --max-time 3 -s http://localhost:5173/ 2>/dev/null)
FRONTEND_CODE=$?

if [ $FRONTEND_CODE -eq 0 ]; then
  SIZE=$(echo "$FRONTEND_RESPONSE" | wc -c)
  echo "✅ Frontend responding ($SIZE bytes)"
  
  if echo "$FRONTEND_RESPONSE" | grep -q "AI Finance Assistant"; then
    echo "✅ Contains 'AI Finance Assistant' text"
  else
    echo "❌ Missing 'AI Finance Assistant' text"
  fi
else
  echo "❌ Frontend not responding (curl code: $FRONTEND_CODE)"
fi

echo ""

# Test backend
echo "Testing Backend..."
BACKEND_RESPONSE=$(curl --max-time 3 -s http://localhost:8000/docs 2>/dev/null)
BACKEND_CODE=$?

if [ $BACKEND_CODE -eq 0 ]; then
  echo "✅ Backend responding"
  if echo "$BACKEND_RESPONSE" | grep -q "<!DOCTYPE"; then
    echo "✅ Backend serving HTML"
  fi
else
  echo "❌ Backend not responding (curl code: $BACKEND_CODE)"
fi

echo ""
echo "==================="
echo "Test Complete"
