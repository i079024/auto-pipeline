#!/bin/bash
# AI-Enhanced DevSecOps Pipeline - Startup Script
# This script starts all required services for the pipeline

set -e

echo "╔════════════════════════════════════════════════════════╗"
echo "║   AI-Enhanced DevSecOps Pipeline - Starting Services  ║"
echo "╚════════════════════════════════════════════════════════╝"
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Function to check if a service is running
check_service() {
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓${NC} $1"
    else
        echo -e "${RED}✗${NC} $1"
        return 1
    fi
}

# 1. Start Jenkins
echo "1. Starting Jenkins..."
brew services start jenkins-lts
sleep 3
curl -s http://localhost:8080 > /dev/null 2>&1
check_service "Jenkins is running on http://localhost:8080"
echo ""

# 2. Start n8n
echo "2. Starting n8n..."
if pgrep -f "n8n" > /dev/null; then
    echo -e "${YELLOW}⚠${NC} n8n is already running"
else
    n8n start --tunnel > /dev/null 2>&1 &
    sleep 5
    check_service "n8n is running on http://localhost:5678"
fi
echo ""

# 3. Start MCP HTTP Wrapper
echo "3. Starting MCP HTTP Wrapper..."
if pgrep -f "mcp-http-wrapper" > /dev/null; then
    echo -e "${YELLOW}⚠${NC} MCP HTTP Wrapper is already running"
else
    python3 mcp-http-wrapper.py > logs/mcp-wrapper.log 2>&1 &
    sleep 3
    curl -s http://localhost:3000/health > /dev/null 2>&1
    check_service "MCP HTTP Wrapper is running on http://localhost:3000"
fi
echo ""

# 4. Start ngrok (for GitHub webhooks)
echo "4. Starting ngrok tunnel..."
if pgrep -f "ngrok" > /dev/null; then
    echo -e "${YELLOW}⚠${NC} ngrok is already running"
    echo "   Check tunnel URL at: http://127.0.0.1:4040"
else
    ngrok http 8080 > /dev/null 2>&1 &
    sleep 3
    NGROK_URL=$(curl -s http://127.0.0.1:4040/api/tunnels | jq -r '.tunnels[0].public_url')
    check_service "ngrok tunnel created"
    echo -e "${GREEN}   Public URL: ${NGROK_URL}${NC}"
    echo -e "${YELLOW}   ⚠ Update GitHub webhook to: ${NGROK_URL}/github-webhook/${NC}"
fi
echo ""

# 5. Check SonarQube (optional)
echo "5. Checking SonarQube..."
if curl -s http://localhost:9000 > /dev/null 2>&1; then
    check_service "SonarQube is running on http://localhost:9000"
else
    echo -e "${YELLOW}⚠${NC} SonarQube is not running (optional)"
    echo "   Start with: docker run -d -p 9000:9000 sonarqube:latest"
fi
echo ""

# 6. Summary
echo "════════════════════════════════════════════════════════"
echo "Service Status Summary"
echo "════════════════════════════════════════════════════════"
echo ""
echo "✓ Jenkins:        http://localhost:8080"
echo "✓ n8n:            http://localhost:5678"
echo "✓ MCP Wrapper:    http://localhost:3000"
echo "✓ ngrok Dashboard: http://127.0.0.1:4040"
if [ -n "$NGROK_URL" ]; then
    echo "✓ Public URL:     ${NGROK_URL}"
fi
echo ""
echo "════════════════════════════════════════════════════════"
echo "Next Steps:"
echo "════════════════════════════════════════════════════════"
echo ""
echo "1. Configure GitHub Webhook:"
echo "   URL: ${NGROK_URL}/github-webhook/"
echo "   Content type: application/json"
echo "   Events: Just the push event"
echo ""
echo "2. Access Jenkins and create pipeline job"
echo "   URL: http://localhost:8080"
echo ""
echo "3. Import n8n workflow"
echo "   URL: http://localhost:5678"
echo "   File: n8n-ai-devsecops-workflow.json"
echo ""
echo "4. Test the pipeline:"
echo "   git commit -m 'test' && git push"
echo ""
echo "════════════════════════════════════════════════════════"
echo "To stop all services, run:"
echo "  ./stop-devsecops-pipeline.sh"
echo "════════════════════════════════════════════════════════"

