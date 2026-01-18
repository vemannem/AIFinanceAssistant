#!/bin/bash
# Test portfolio tab by simulating browser JavaScript execution

echo "🧪 Testing Portfolio Tab Functionality"
echo "======================================"
echo ""

# Check if components exist in built files
echo "✓ Checking if components are bundled..."
for component in "PortfolioForm" "PortfolioDisplay" "PortfolioHistory"; do
  count=$(grep -c "$component" /Users/yuvan/Documents/agentic/AIFinanceAssistent/frontend/dist/assets/*.js 2>/dev/null || echo 0)
  if [ "$count" -gt 0 ]; then
    echo "  ✅ $component: Found in bundle"
  else
    echo "  ❌ $component: NOT found in bundle"
  fi
done

echo ""
echo "✓ Checking imports..."
for file in ChatInterface ConversationHistory PortfolioForm PortfolioDisplay; do
  path="/Users/yuvan/Documents/agentic/AIFinanceAssistent/frontend/src/components"
  if [[ "$file" == *"History" ]]; then
    filepath="$path/Chat/${file}.tsx"
  elif [[ "$file" == *"Form" ]] || [[ "$file" == *"Display" ]]; then
    filepath="$path/Portfolio/${file}.tsx"
  else
    filepath="$path/Chat/${file}.tsx"
  fi
  
  if [ -f "$filepath" ]; then
    echo "  ✅ $file exists"
  else
    echo "  ❌ $file MISSING: $filepath"
  fi
done

echo ""
echo "✓ Checking App.tsx imports..."
grep -q "PortfolioForm\|PortfolioDisplay" /Users/yuvan/Documents/agentic/AIFinanceAssistent/frontend/src/App.tsx && echo "  ✅ Portfolio components imported" || echo "  ❌ Portfolio imports MISSING"

echo ""
echo "✓ Build info..."
ls -lh /Users/yuvan/Documents/agentic/AIFinanceAssistent/frontend/dist/assets/index-*.js | tail -1 | awk '{print "  Size:", $5}'

echo ""
echo "🔍 Likely issues:"
echo "1. Open http://localhost:5173 in browser"
echo "2. Press F12 to open DevTools"
echo "3. Go to Console tab"
echo "4. Click Portfolio tab"
echo "5. Look for red error messages"
echo "6. Report any errors"

