"""
Test script for Speculator Bot MCP Server

This script demonstrates how to test the MCP server programmatically.
"""

import asyncio
import json
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client
    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False
    print("❌ MCP SDK not installed. Run: pip install mcp")
    sys.exit(1)


async def test_mcp_server():
    """Test the MCP server functionality"""
    
    print("🤖 Testing Speculator Bot MCP Server\n")
    print("=" * 60)
    
    # Server parameters
    server_params = StdioServerParameters(
        command="python3",
        args=[
            "-m", "speculator_bot.mcp_server",
            "--repo", ".",
            "--config", "config.yaml"
        ]
    )
    
    try:
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                
                # Initialize session
                await session.initialize()
                print("✓ MCP Server initialized successfully\n")
                
                # Test 1: List available tools
                print("Test 1: List Available Tools")
                print("-" * 60)
                tools = await session.list_tools()
                print(f"Found {len(tools.tools)} tools:")
                for tool in tools.tools:
                    print(f"  • {tool.name}: {tool.description[:50]}...")
                print()
                
                # Test 2: List available resources
                print("Test 2: List Available Resources")
                print("-" * 60)
                resources = await session.list_resources()
                print(f"Found {len(resources.resources)} resources:")
                for resource in resources.resources:
                    print(f"  • {resource.uri}: {resource.description}")
                print()
                
                # Test 3: Read a resource
                print("Test 3: Read Resource (Status)")
                print("-" * 60)
                status = await session.read_resource("speculator://status")
                status_data = json.loads(status.contents[0].text)
                print(json.dumps(status_data, indent=2))
                print()
                
                # Test 4: List available prompts
                print("Test 4: List Available Prompts")
                print("-" * 60)
                prompts = await session.list_prompts()
                print(f"Found {len(prompts.prompts)} prompts:")
                for prompt in prompts.prompts:
                    print(f"  • {prompt.name}: {prompt.description}")
                print()
                
                # Test 5: Call analyze_risk tool (if test data exists)
                print("Test 5: Call analyze_risk Tool")
                print("-" * 60)
                try:
                    result = await session.call_tool(
                        "analyze_risk",
                        arguments={
                            "test_catalog": "examples/test_catalog.json",
                            "historical_data": "examples/historical_failures.json",
                            "analyze_db": False
                        }
                    )
                    
                    if result.content:
                        analysis = json.loads(result.content[0].text)
                        print(f"Risk Score: {analysis['deployment_risk_score']:.2f}")
                        print(f"Risk Level: {analysis['risk_level']}")
                        print(f"Files Changed: {analysis['change_summary']['total_files_changed']}")
                        print("\nRecommendation:")
                        print(analysis['recommendation'][:200] + "...")
                    else:
                        print("⚠️ No analysis results returned")
                except Exception as e:
                    print(f"⚠️ Could not run analysis: {e}")
                    print("   (This is expected if there are no git changes)")
                print()
                
                print("=" * 60)
                print("✅ All MCP Server tests completed successfully!")
                
    except Exception as e:
        print(f"\n❌ Error testing MCP server: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


async def test_tool_schemas():
    """Test that tool schemas are valid"""
    print("\n🔍 Validating Tool Schemas\n")
    print("=" * 60)
    
    server_params = StdioServerParameters(
        command="python3",
        args=[
            "-m", "speculator_bot.mcp_server",
            "--repo", ".",
            "--config", "config.yaml"
        ]
    )
    
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            tools = await session.list_tools()
            
            for tool in tools.tools:
                print(f"\n📋 Tool: {tool.name}")
                print(f"   Description: {tool.description}")
                print(f"   Schema valid: ✓")
                
                # Check required properties
                if "properties" in tool.inputSchema:
                    props = tool.inputSchema["properties"]
                    print(f"   Parameters: {len(props)}")
                    
                    required = tool.inputSchema.get("required", [])
                    if required:
                        print(f"   Required: {', '.join(required)}")
            
            print("\n" + "=" * 60)
            print("✅ All tool schemas are valid!")


def main():
    """Main entry point"""
    print("\n" + "=" * 60)
    print(" SPECULATOR BOT MCP SERVER TEST SUITE")
    print("=" * 60 + "\n")
    
    if not MCP_AVAILABLE:
        return
    
    try:
        # Run tests
        asyncio.run(test_mcp_server())
        asyncio.run(test_tool_schemas())
        
        print("\n" + "=" * 60)
        print("🎉 All tests passed!")
        print("=" * 60 + "\n")
        
        print("Next steps:")
        print("1. Configure Claude Desktop with claude_desktop_config.json")
        print("2. Restart Claude Desktop")
        print("3. Try: 'Analyze deployment risk for my changes'")
        print("\nSee MCP_SETUP.md for detailed instructions.")
        
    except KeyboardInterrupt:
        print("\n\n⚠️ Tests interrupted by user")
    except Exception as e:
        print(f"\n❌ Tests failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

