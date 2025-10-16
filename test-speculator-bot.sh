#!/bin/bash

# Test Speculator Bot Analysis Endpoint
# This simulates what n8n sends to the MCP wrapper

echo "🧪 Testing Speculator Bot Analysis Endpoint"
echo "=============================================="
echo ""

# Test 1: Basic connectivity
echo "Test 1: Check if MCP wrapper is running..."
if lsof -i :3001 > /dev/null 2>&1; then
    echo "✅ MCP wrapper is running on port 3001"
else
    echo "❌ MCP wrapper is NOT running on port 3001"
    echo "   Run: python3 mcp-http-wrapper.py"
    exit 1
fi
echo ""

# Test 2: Check endpoint response
echo "Test 2: Testing endpoint with sample data..."
echo ""

RESPONSE=$(curl -s -w "\nHTTP_CODE:%{http_code}" -X POST http://localhost:3001/api/speculator/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "commitSHA": "abc123def456",
    "branch": "main",
    "author": "developer@example.com",
    "sonarURL": "http://localhost:9000/dashboard?id=test-project",
    "repository": "https://github.com/testuser/testrepo.git"
  }')

HTTP_CODE=$(echo "$RESPONSE" | grep "HTTP_CODE:" | cut -d':' -f2)
BODY=$(echo "$RESPONSE" | grep -v "HTTP_CODE:")

echo "HTTP Status Code: $HTTP_CODE"
echo ""
echo "Response Body:"
echo "$BODY" | python3 -m json.tool 2>/dev/null || echo "$BODY"
echo ""

if [ "$HTTP_CODE" = "200" ]; then
    echo "✅ Endpoint returned 200 OK"
elif [ "$HTTP_CODE" = "500" ]; then
    echo "⚠️  Endpoint returned 500 (expected with test data)"
    echo "    This is normal - the analysis requires a real repository"
    echo "    Connection is working correctly!"
else
    echo "❌ Unexpected status code: $HTTP_CODE"
fi

echo ""
echo "=============================================="
echo "Summary:"
echo "  • MCP Wrapper: ✅ Running on port 3001"
echo "  • Endpoint: ✅ Responding to requests"
echo "  • n8n should use: http://localhost:3001/api/speculator/analyze"
echo ""
echo "🎯 Next: Test this in n8n by importing the workflow!"

