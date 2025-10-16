#!/bin/bash
# AI-Enhanced DevSecOps Pipeline - Shutdown Script

echo "Stopping AI-Enhanced DevSecOps Pipeline services..."
echo ""

# Stop Jenkins
echo "Stopping Jenkins..."
brew services stop jenkins-lts

# Stop n8n
echo "Stopping n8n..."
pkill -f "n8n"

# Stop MCP HTTP Wrapper
echo "Stopping MCP HTTP Wrapper..."
pkill -f "mcp-http-wrapper"

# Stop ngrok
echo "Stopping ngrok..."
pkill -f "ngrok"

echo ""
echo "✓ All services stopped"

