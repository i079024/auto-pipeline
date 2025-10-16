"""
Model Context Protocol (MCP) Server for Speculator Bot

This MCP server exposes Speculator Bot's risk analysis, test selection,
and database validation capabilities to AI assistants via the MCP protocol.
"""

import asyncio
import json
import logging
from typing import Any, Sequence
from pathlib import Path

try:
    from mcp.server import Server
    from mcp.server.stdio import stdio_server
    from mcp.types import (
        Tool,
        TextContent,
        Resource,
        Prompt,
        GetPromptResult,
        PromptMessage,
        PromptArgument,
    )
    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False
    print("Warning: MCP SDK not installed. Run: pip install mcp")

from .bot import SpeculatorBot

logger = logging.getLogger(__name__)


class SpeculatorMCPServer:
    """MCP Server wrapper for Speculator Bot"""
    
    def __init__(self, repo_path: str = '.', config_path: str = 'config.yaml'):
        """
        Initialize the MCP server
        
        Args:
            repo_path: Path to git repository
            config_path: Path to configuration file
        """
        if not MCP_AVAILABLE:
            raise ImportError("MCP SDK not installed. Run: pip install mcp")
        
        self.repo_path = repo_path
        self.config_path = config_path
        self.server = Server("speculator-bot")
        self.bot = None
        
        # Register handlers
        self._register_tools()
        self._register_resources()
        self._register_prompts()
    
    def _initialize_bot(self, test_catalog: str = None, historical_data: str = None):
        """Initialize Speculator Bot with optional data sources"""
        if not self.bot:
            self.bot = SpeculatorBot(
                repo_path=self.repo_path,
                test_catalog_path=test_catalog,
                historical_data_path=historical_data
            )
        return self.bot
    
    def _register_tools(self):
        """Register MCP tools"""
        
        @self.server.list_tools()
        async def list_tools() -> list[Tool]:
            """List available tools"""
            return [
                Tool(
                    name="analyze_risk",
                    description=(
                        "Analyze code changes and predict deployment risk. "
                        "Returns risk score (0-1), risk factors, and recommendations."
                    ),
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "commit_hash": {
                                "type": "string",
                                "description": "Specific commit to analyze (optional, defaults to staged changes)"
                            },
                            "test_catalog": {
                                "type": "string",
                                "description": "Path to test catalog JSON file"
                            },
                            "historical_data": {
                                "type": "string",
                                "description": "Path to historical failure data JSON"
                            },
                            "analyze_db": {
                                "type": "boolean",
                                "description": "Whether to analyze database changes",
                                "default": True
                            }
                        }
                    }
                ),
                Tool(
                    name="select_tests",
                    description=(
                        "Intelligently select tests based on code changes and risk analysis. "
                        "Returns prioritized list of tests to run."
                    ),
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "commit_hash": {
                                "type": "string",
                                "description": "Commit to analyze for test selection"
                            },
                            "test_catalog": {
                                "type": "string",
                                "description": "Path to test catalog JSON file",
                                "required": True
                            },
                            "max_tests": {
                                "type": "integer",
                                "description": "Maximum number of tests to select",
                                "default": 50
                            }
                        },
                        "required": ["test_catalog"]
                    }
                ),
                Tool(
                    name="check_data_drift",
                    description=(
                        "Detect data drift in database tables by comparing current data "
                        "with baseline statistics."
                    ),
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "table_name": {
                                "type": "string",
                                "description": "Database table name to check",
                                "required": True
                            },
                            "columns": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Specific columns to check (optional)"
                            }
                        },
                        "required": ["table_name"]
                    }
                ),
                Tool(
                    name="export_report",
                    description=(
                        "Export analysis report in specified format (json, html, text)."
                    ),
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "output_path": {
                                "type": "string",
                                "description": "Path to save the report",
                                "required": True
                            },
                            "format": {
                                "type": "string",
                                "enum": ["json", "html", "text"],
                                "description": "Report format",
                                "default": "html"
                            }
                        },
                        "required": ["output_path"]
                    }
                )
            ]
        
        @self.server.call_tool()
        async def call_tool(name: str, arguments: Any) -> Sequence[TextContent]:
            """Handle tool calls"""
            try:
                if name == "analyze_risk":
                    return await self._handle_analyze_risk(arguments)
                elif name == "select_tests":
                    return await self._handle_select_tests(arguments)
                elif name == "check_data_drift":
                    return await self._handle_check_drift(arguments)
                elif name == "export_report":
                    return await self._handle_export_report(arguments)
                else:
                    raise ValueError(f"Unknown tool: {name}")
            except Exception as e:
                logger.error(f"Error calling tool {name}: {e}")
                return [TextContent(
                    type="text",
                    text=f"Error: {str(e)}"
                )]
    
    async def _handle_analyze_risk(self, args: dict) -> Sequence[TextContent]:
        """Handle risk analysis tool call"""
        commit_hash = args.get("commit_hash")
        test_catalog = args.get("test_catalog")
        historical_data = args.get("historical_data")
        analyze_db = args.get("analyze_db", True)
        
        bot = self._initialize_bot(test_catalog, historical_data)
        
        # Run analysis
        report = bot.speculate(
            commit_hash=commit_hash,
            analyze_db=analyze_db,
            check_drift=False  # Separate tool for drift
        )
        
        # Format response
        result = {
            "deployment_risk_score": report.deployment_risk_score,
            "risk_level": self._get_risk_level(report.deployment_risk_score),
            "recommendation": report.overall_recommendation,
            "change_summary": report.change_summary,
            "risk_analysis": {
                "average_risk": report.risk_analysis["average_risk"],
                "max_risk": report.risk_analysis["max_risk"],
                "risk_distribution": report.risk_analysis["risk_distribution"],
                "high_risk_files": report.risk_analysis.get("high_risk_files", [])
            },
            "test_selection": {
                "total_tests": report.test_selection["total_tests_selected"],
                "estimated_time_minutes": report.test_selection["estimated_execution_time_minutes"],
                "coverage_score": report.test_selection["coverage_score"]
            }
        }
        
        if report.schema_analysis:
            result["schema_analysis"] = report.schema_analysis
        
        return [TextContent(
            type="text",
            text=json.dumps(result, indent=2)
        )]
    
    async def _handle_select_tests(self, args: dict) -> Sequence[TextContent]:
        """Handle test selection tool call"""
        commit_hash = args.get("commit_hash")
        test_catalog = args.get("test_catalog")
        max_tests = args.get("max_tests", 50)
        
        if not test_catalog:
            return [TextContent(
                type="text",
                text="Error: test_catalog is required"
            )]
        
        # Update config with max_tests
        config = {"test_selection": {"max_tests": max_tests}}
        bot = SpeculatorBot(
            repo_path=self.repo_path,
            config=config,
            test_catalog_path=test_catalog
        )
        
        report = bot.speculate(commit_hash=commit_hash)
        
        # Extract test information
        result = {
            "selected_tests": [
                {
                    "test_id": test.test_id,
                    "test_name": test.test_name,
                    "test_path": test.test_path,
                    "criticality": test.criticality,
                    "execution_time_seconds": test.execution_time_seconds
                }
                for test in report.test_selection.get("selected_tests", [])
            ],
            "total_tests": report.test_selection["total_tests_selected"],
            "estimated_time_minutes": report.test_selection["estimated_execution_time_minutes"],
            "coverage_score": report.test_selection["coverage_score"]
        }
        
        return [TextContent(
            type="text",
            text=json.dumps(result, indent=2)
        )]
    
    async def _handle_check_drift(self, args: dict) -> Sequence[TextContent]:
        """Handle data drift detection tool call"""
        table_name = args.get("table_name")
        columns = args.get("columns")
        
        if not table_name:
            return [TextContent(
                type="text",
                text="Error: table_name is required"
            )]
        
        # Note: This requires database connection setup
        return [TextContent(
            type="text",
            text=json.dumps({
                "message": "Data drift detection requires database connection setup",
                "table": table_name,
                "note": "Use capture_baseline command first to establish baseline statistics"
            }, indent=2)
        )]
    
    async def _handle_export_report(self, args: dict) -> Sequence[TextContent]:
        """Handle report export tool call"""
        output_path = args.get("output_path")
        format_type = args.get("format", "html")
        
        if not hasattr(self, 'last_report') or not self.last_report:
            return [TextContent(
                type="text",
                text="Error: No report available to export. Run analyze_risk first."
            )]
        
        bot = self._initialize_bot()
        bot.export_report(self.last_report, output_path, format_type)
        
        return [TextContent(
            type="text",
            text=f"Report exported to: {output_path}"
        )]
    
    def _get_risk_level(self, score: float) -> str:
        """Convert risk score to level"""
        if score >= 0.8:
            return "CRITICAL"
        elif score >= 0.6:
            return "HIGH"
        elif score >= 0.4:
            return "MEDIUM"
        elif score >= 0.2:
            return "LOW"
        else:
            return "MINIMAL"
    
    def _register_resources(self):
        """Register MCP resources"""
        
        @self.server.list_resources()
        async def list_resources() -> list[Resource]:
            """List available resources"""
            return [
                Resource(
                    uri="speculator://config",
                    name="Configuration",
                    mimeType="application/json",
                    description="Current Speculator Bot configuration"
                ),
                Resource(
                    uri="speculator://status",
                    name="Status",
                    mimeType="application/json",
                    description="Current bot status and capabilities"
                )
            ]
        
        @self.server.read_resource()
        async def read_resource(uri: str) -> str:
            """Read resource content"""
            if uri == "speculator://config":
                import yaml
                if Path(self.config_path).exists():
                    with open(self.config_path) as f:
                        config = yaml.safe_load(f)
                    return json.dumps(config, indent=2)
                return json.dumps({"error": "Config file not found"})
            
            elif uri == "speculator://status":
                status = {
                    "name": "Speculator Bot",
                    "version": "1.0.0",
                    "status": "active",
                    "capabilities": [
                        "Risk Analysis",
                        "Test Selection",
                        "Database Validation",
                        "Data Drift Detection"
                    ],
                    "repo_path": self.repo_path
                }
                return json.dumps(status, indent=2)
            
            return json.dumps({"error": f"Unknown resource: {uri}"})
    
    def _register_prompts(self):
        """Register MCP prompts"""
        
        @self.server.list_prompts()
        async def list_prompts() -> list[Prompt]:
            """List available prompts"""
            return [
                Prompt(
                    name="analyze_deployment",
                    description="Analyze deployment readiness for current changes",
                    arguments=[
                        PromptArgument(
                            name="commit",
                            description="Commit hash to analyze (optional)",
                            required=False
                        )
                    ]
                ),
                Prompt(
                    name="review_risk",
                    description="Review risk factors and get recommendations",
                    arguments=[
                        PromptArgument(
                            name="file_path",
                            description="Specific file to review",
                            required=False
                        )
                    ]
                )
            ]
        
        @self.server.get_prompt()
        async def get_prompt(name: str, arguments: dict = None) -> GetPromptResult:
            """Get prompt content"""
            if name == "analyze_deployment":
                commit = arguments.get("commit", "staged changes") if arguments else "staged changes"
                return GetPromptResult(
                    messages=[
                        PromptMessage(
                            role="user",
                            content=TextContent(
                                type="text",
                                text=f"Please analyze the deployment risk for {commit}. "
                                     f"Provide a comprehensive risk assessment including:\n"
                                     f"1. Overall risk score and level\n"
                                     f"2. Key risk factors\n"
                                     f"3. Recommended tests to run\n"
                                     f"4. Deployment recommendation\n"
                                     f"Use the analyze_risk tool to get detailed information."
                            )
                        )
                    ]
                )
            
            elif name == "review_risk":
                file_path = arguments.get("file_path", "all files") if arguments else "all files"
                return GetPromptResult(
                    messages=[
                        PromptMessage(
                            role="user",
                            content=TextContent(
                                type="text",
                                text=f"Review risk factors for {file_path}. "
                                     f"Analyze:\n"
                                     f"1. Code complexity and maintainability\n"
                                     f"2. Historical failure patterns\n"
                                     f"3. Change magnitude and criticality\n"
                                     f"4. Potential impact on system\n"
                                     f"Provide specific recommendations for risk mitigation."
                            )
                        )
                    ]
                )
            
            raise ValueError(f"Unknown prompt: {name}")
    
    async def run(self):
        """Run the MCP server"""
        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                self.server.create_initialization_options()
            )


async def main():
    """Main entry point for MCP server"""
    import sys
    import argparse
    
    parser = argparse.ArgumentParser(description="Speculator Bot MCP Server")
    parser.add_argument("--repo", default=".", help="Repository path")
    parser.add_argument("--config", default="config.yaml", help="Config file path")
    
    args = parser.parse_args()
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        stream=sys.stderr  # MCP uses stdout for protocol
    )
    
    server = SpeculatorMCPServer(
        repo_path=args.repo,
        config_path=args.config
    )
    
    logger.info("Starting Speculator Bot MCP Server")
    await server.run()


if __name__ == "__main__":
    asyncio.run(main())

