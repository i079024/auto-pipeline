#!/bin/bash
# Troubleshooting script for Speculator Bot MCP Server
# Run this if you're having issues with the MCP integration

set -e

echo "🔍 SPECULATOR BOT MCP TROUBLESHOOTING"
echo "======================================"
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to check status
check() {
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓${NC} $1"
        return 0
    else
        echo -e "${RED}✗${NC} $1"
        return 1
    fi
}

# Check 1: Python Installation
echo "1. Checking Python installation..."
python3 --version > /dev/null 2>&1
check "Python 3 is installed"
PYTHON_VERSION=$(python3 --version)
echo "   Version: $PYTHON_VERSION"
echo ""

# Check 2: MCP SDK
echo "2. Checking MCP SDK..."
python3 -c "import mcp" > /dev/null 2>&1
if check "MCP SDK is installed"; then
    MCP_VERSION=$(python3 -c "import mcp; print(getattr(mcp, '__version__', 'unknown'))")
    echo "   Version: $MCP_VERSION"
else
    echo -e "   ${YELLOW}→ Run: pip3 install mcp${NC}"
fi
echo ""

# Check 3: Speculator Bot Dependencies
echo "3. Checking Speculator Bot dependencies..."
MISSING_DEPS=()

for dep in sklearn pandas numpy git yaml; do
    python3 -c "import $dep" > /dev/null 2>&1
    if check "$dep"; then
        :
    else
        MISSING_DEPS+=($dep)
    fi
done

if [ ${#MISSING_DEPS[@]} -gt 0 ]; then
    echo -e "   ${YELLOW}→ Missing dependencies: ${MISSING_DEPS[*]}${NC}"
    echo -e "   ${YELLOW}→ Run: pip3 install -r requirements.txt${NC}"
fi
echo ""

# Check 4: Speculator Bot Installation
echo "4. Checking Speculator Bot installation..."
python3 -c "from speculator_bot import SpeculatorBot" > /dev/null 2>&1
if check "Speculator Bot is importable"; then
    :
else
    echo -e "   ${YELLOW}→ Run: pip3 install -e .${NC}"
fi
echo ""

# Check 5: Git Repository
echo "5. Checking Git repository..."
if [ -d ".git" ]; then
    check "Git repository found"
    REPO_PATH=$(git rev-parse --show-toplevel)
    echo "   Path: $REPO_PATH"
else
    echo -e "${YELLOW}⚠${NC} Not a git repository"
    echo "   MCP server will work with limited functionality"
fi
echo ""

# Check 6: Configuration Files
echo "6. Checking configuration files..."

if [ -f "config.yaml" ]; then
    check "config.yaml exists"
else
    echo -e "${YELLOW}⚠${NC} config.yaml not found"
    echo -e "   ${YELLOW}→ Run: speculator init${NC}"
fi

if [ -f "examples/test_catalog.json" ]; then
    check "test_catalog.json exists"
else
    echo -e "${YELLOW}⚠${NC} test_catalog.json not found"
fi

if [ -f "examples/historical_failures.json" ]; then
    check "historical_failures.json exists"
else
    echo -e "${YELLOW}⚠${NC} historical_failures.json not found"
fi
echo ""

# Check 7: Claude Desktop Configuration
echo "7. Checking Claude Desktop configuration..."
CLAUDE_CONFIG="$HOME/Library/Application Support/Claude/claude_desktop_config.json"

if [ -f "$CLAUDE_CONFIG" ]; then
    check "Claude Desktop config exists"
    
    # Check if speculator-bot is configured
    if grep -q "speculator-bot" "$CLAUDE_CONFIG"; then
        check "Speculator Bot MCP server is configured"
        
        # Check command
        COMMAND=$(cat "$CLAUDE_CONFIG" | python3 -c "import json,sys; data=json.load(sys.stdin); print(data.get('mcpServers',{}).get('speculator-bot',{}).get('command',''))")
        if [ "$COMMAND" = "python3" ]; then
            check "Python command is correct (python3)"
        else
            echo -e "${YELLOW}⚠${NC} Command should be 'python3', found: $COMMAND"
        fi
    else
        echo -e "${YELLOW}⚠${NC} Speculator Bot not configured in Claude Desktop"
        echo -e "   ${YELLOW}→ Run: cp claude_desktop_config.json \"$CLAUDE_CONFIG\"${NC}"
    fi
else
    echo -e "${RED}✗${NC} Claude Desktop config not found"
    echo -e "   ${YELLOW}→ Create directory: mkdir -p \"$HOME/Library/Application Support/Claude\"${NC}"
    echo -e "   ${YELLOW}→ Copy config: cp claude_desktop_config.json \"$CLAUDE_CONFIG\"${NC}"
fi
echo ""

# Check 8: MCP Server Test
echo "8. Testing MCP Server..."
echo "   Running test script..."

if python3 examples/test_mcp_server.py > /tmp/mcp_test_output.txt 2>&1; then
    check "MCP Server test passed"
    
    # Check for specific success indicators
    if grep -q "All MCP Server tests completed successfully" /tmp/mcp_test_output.txt; then
        check "All tests completed successfully"
    fi
    
    if grep -q "Found 4 tools" /tmp/mcp_test_output.txt; then
        check "All 4 tools are available"
    fi
    
    if grep -q "Found 2 resources" /tmp/mcp_test_output.txt; then
        check "All 2 resources are available"
    fi
else
    echo -e "${RED}✗${NC} MCP Server test failed"
    echo "   Check /tmp/mcp_test_output.txt for details"
    echo ""
    echo "   Last 10 lines of error:"
    tail -10 /tmp/mcp_test_output.txt | sed 's/^/   /'
fi
echo ""

# Check 9: Claude Desktop Logs
echo "9. Checking Claude Desktop logs..."
CLAUDE_LOGS="$HOME/Library/Logs/Claude"

if [ -d "$CLAUDE_LOGS" ]; then
    check "Claude Desktop logs directory exists"
    
    # Find recent MCP logs
    RECENT_MCP_LOGS=$(find "$CLAUDE_LOGS" -name "mcp*.log" -mtime -1 2>/dev/null | head -5)
    
    if [ -n "$RECENT_MCP_LOGS" ]; then
        echo "   Recent MCP log files:"
        echo "$RECENT_MCP_LOGS" | while read log; do
            echo "   - $log"
        done
        echo ""
        echo "   To view logs: tail -f $CLAUDE_LOGS/mcp*.log"
    else
        echo -e "   ${YELLOW}⚠${NC} No recent MCP logs found"
        echo "   (This is normal if you haven't used Claude Desktop yet)"
    fi
else
    echo -e "   ${YELLOW}⚠${NC} Claude Desktop logs directory not found"
fi
echo ""

# Summary and Recommendations
echo "======================================"
echo "SUMMARY & RECOMMENDATIONS"
echo "======================================"
echo ""

# Collect issues
ISSUES=()

python3 -c "import mcp" > /dev/null 2>&1 || ISSUES+=("Install MCP SDK: pip3 install mcp")
python3 -c "from speculator_bot import SpeculatorBot" > /dev/null 2>&1 || ISSUES+=("Install Speculator Bot: pip3 install -e .")
[ ! -f "$CLAUDE_CONFIG" ] && ISSUES+=("Configure Claude Desktop: cp claude_desktop_config.json \"$CLAUDE_CONFIG\"")

if [ ${#ISSUES[@]} -eq 0 ]; then
    echo -e "${GREEN}✅ All checks passed!${NC}"
    echo ""
    echo "Your Speculator Bot MCP Server should be working."
    echo ""
    echo "Next steps:"
    echo "1. Restart Claude Desktop"
    echo "2. Ask Claude: 'What is the status of Speculator Bot?'"
    echo "3. Try: 'Analyze deployment risk for my changes'"
else
    echo -e "${YELLOW}⚠️ Issues found:${NC}"
    echo ""
    for issue in "${ISSUES[@]}"; do
        echo "   → $issue"
    done
fi

echo ""
echo "For more help, see:"
echo "  - MCP_SETUP.md (full setup guide)"
echo "  - MCP_QUICKSTART.md (5-minute quick start)"
echo "  - MCP_SETUP_COMPLETE.md (setup summary)"
echo ""
echo "======================================"

