#!/bin/bash

echo "Testing frontend at http://localhost:5173/"
echo ""

# Wait for server
sleep 2

# Test if server is responding
echo "1. Testing server connection..."
if curl -s -o /dev/null -w "%{http_code}" http://localhost:5173/ | grep -q "200"; then
  echo "   ✅ Server is responding with HTTP 200"
else
  echo "   ❌ Server not responding or returned error"
fi

echo ""
echo "2. Checking HTML content..."
HTML=$(curl -s http://localhost:5173/)

if echo "$HTML" | grep -q "<!doctype html"; then
  echo "   ✅ HTML doctype found"
else
  echo "   ❌ HTML doctype missing"
fi

if echo "$HTML" | grep -q "AI Finance Assistant"; then
  echo "   ✅ 'AI Finance Assistant' text found"
else
  echo "   ❌ 'AI Finance Assistant' text NOT found"
fi

if echo "$HTML" | grep -q "Frontend is working"; then
  echo "   ✅ 'Frontend is working' text found"
else
  echo "   ❌ 'Frontend is working' text NOT found"
fi

if echo "$HTML" | grep -q "<html"; then
  echo "   ✅ HTML tag found"
else
  echo "   ❌ HTML tag missing"
fi

if echo "$HTML" | grep -q "textarea"; then
  echo "   ✅ Textarea element found"
else
  echo "   ❌ Textarea element NOT found"
fi

echo ""
echo "3. HTML Length: $(echo "$HTML" | wc -c) bytes"
echo ""
echo "First 50 lines of HTML:"
echo "$HTML" | head -50
