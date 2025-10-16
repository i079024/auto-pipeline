#!/bin/bash

# Test n8n Webhook with Real Repository Data
# This script sends a webhook to n8n using actual commit data from your GitHub repository

echo "🧪 Testing n8n Webhook Integration"
echo "===================================="
echo ""

# Fetch latest commit from repository
echo "📡 Fetching latest commit from GitHub..."
COMMIT_DATA=$(curl -s "https://api.github.com/repos/i079024/AI-DevSecOps-Pipeline/commits?per_page=1")
COMMIT_SHA=$(echo "$COMMIT_DATA" | python3 -c "import sys, json; commits = json.load(sys.stdin); print(commits[0]['sha'])" 2>/dev/null)
COMMIT_AUTHOR=$(echo "$COMMIT_DATA" | python3 -c "import sys, json; commits = json.load(sys.stdin); print(commits[0]['commit']['author']['email'])" 2>/dev/null)
COMMIT_MSG=$(echo "$COMMIT_DATA" | python3 -c "import sys, json; commits = json.load(sys.stdin); print(commits[0]['commit']['message'][:60])" 2>/dev/null)

if [ -z "$COMMIT_SHA" ]; then
    echo "❌ Failed to fetch commit data from GitHub"
    echo "   Using test data instead..."
    COMMIT_SHA="test123"
    COMMIT_AUTHOR="sagar.maddali@sap.com"
fi

echo "✅ Latest commit found:"
echo "   SHA: $COMMIT_SHA"
echo "   Author: $COMMIT_AUTHOR"
echo "   Message: $COMMIT_MSG"
echo ""

# Send webhook to n8n
echo "📤 Sending webhook to n8n..."
RESPONSE=$(curl -s -w "\nHTTP_CODE:%{http_code}" -X POST http://localhost:5678/webhook-test/jenkins-trigger \
  -H "Content-Type: application/json" \
  -d "{
    \"commitSHA\": \"$COMMIT_SHA\",
    \"branch\": \"main\",
    \"author\": \"$COMMIT_AUTHOR\",
    \"sonarURL\": \"http://localhost:9000/dashboard?id=ai-devsecops-pipeline\",
    \"buildNumber\": \"1\",
    \"jenkinsURL\": \"http://localhost:8080/job/ai-devsecops-pipeline/1/\",
    \"repository\": \"https://github.com/i079024/AI-DevSecOps-Pipeline.git\"
  }")

HTTP_CODE=$(echo "$RESPONSE" | grep "HTTP_CODE:" | cut -d':' -f2)
BODY=$(echo "$RESPONSE" | grep -v "HTTP_CODE:")

echo ""
echo "📊 Response from n8n:"
echo "   HTTP Status: $HTTP_CODE"
echo "   Body: $BODY"
echo ""

if [ "$HTTP_CODE" = "200" ]; then
    echo "✅ Webhook received successfully!"
    echo ""
    echo "🔍 Next Steps:"
    echo "   1. Open n8n: http://localhost:5678"
    echo "   2. Click 'Executions' tab"
    echo "   3. View the latest execution"
    echo "   4. Check each node's output"
else
    echo "⚠️  Unexpected status code: $HTTP_CODE"
fi

echo ""
echo "===================================="

