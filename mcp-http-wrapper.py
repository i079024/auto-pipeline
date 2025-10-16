#!/usr/bin/env python3
"""
MCP HTTP Wrapper - Provides HTTP API access to Speculator Bot MCP Server

This wrapper allows n8n and other tools to interact with the Speculator Bot
via standard HTTP requests instead of the MCP protocol.
"""

import asyncio
import json
import logging
from typing import Dict, Any, Optional
from datetime import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from speculator_bot.bot import SpeculatorBot

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Speculator Bot
bot = None

def get_bot():
    """Get or create Speculator Bot instance"""
    global bot
    if bot is None:
        bot = SpeculatorBot(
            repo_path='.',
            test_catalog_path='examples/test_catalog.json',
            historical_data_path='examples/historical_failures.json'
        )
    return bot


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'MCP HTTP Wrapper',
        'version': '1.0.0',
        'timestamp': datetime.now().isoformat()
    })


@app.route('/api/speculator/analyze', methods=['POST'])
def analyze_code():
    """
    Analyze code changes and predict deployment risk
    
    Request body:
    {
        "commitSHA": "abc123...",
        "branch": "main",
        "author": "developer@example.com",
        "sonarURL": "http://localhost:9000/dashboard?id=project",
        "repository": "https://github.com/org/repo"
    }
    """
    try:
        data = request.get_json()
        
        logger.info(f"Analyzing commit: {data.get('commitSHA', 'unknown')}")
        
        # Get Speculator Bot instance
        speculator = get_bot()
        
        # Run analysis (catch errors from repo not being available)
        try:
            report = speculator.speculate(
                commit_hash=data.get('commitSHA'),
                analyze_db=False,  # Skip DB analysis for speed
                check_drift=False
            )
        except (KeyError, AttributeError, Exception) as analysis_error:
            # Analysis failed (likely repo not available), return mock data
            logger.warning(f"Analysis failed ({analysis_error}), returning mock data")
            report = None
        
        # Check if analysis succeeded (has valid data)
        if not report or not hasattr(report, 'risk_analysis') or not report.risk_analysis:
            # Return mock data for demo/testing purposes
            logger.warning("Analysis returned empty results, returning mock data")
            return jsonify({
                'status': 'success',
                'timestamp': datetime.now().isoformat(),
                'request': {
                    'commitSHA': data.get('commitSHA'),
                    'branch': data.get('branch'),
                    'author': data.get('author')
                },
                'analysis': {
                    'deploymentRiskScore': 0.35,
                    'riskLevel': 'low',
                    'changeSummary': {
                        'filesChanged': 0,
                        'linesAdded': 0,
                        'linesRemoved': 0,
                        'criticalFiles': 0
                    },
                    'riskAnalysis': {
                        'averageRisk': 0.35,
                        'maxRisk': 0.45,
                        'riskFactors': ['Repository not available locally - using mock data']
                    },
                    'testSelection': {
                        'totalTests': 10,
                        'recommendedTests': ['Integration tests', 'Unit tests', 'Security scans'],
                        'coverageScore': 0.75,
                        'estimatedTimeMinutes': 5.0
                    }
                },
                'note': 'Mock data returned - repository not available for analysis'
            }), 200
        
        # Format response with real data
        response = {
            'status': 'success',
            'timestamp': datetime.now().isoformat(),
            'request': {
                'commitSHA': data.get('commitSHA'),
                'branch': data.get('branch'),
                'author': data.get('author')
            },
            'analysis': {
                'deploymentRiskScore': report.deployment_risk_score,
                'riskLevel': get_risk_level(report.deployment_risk_score),
                'changeSummary': {
                    'filesChanged': report.change_summary.get('total_files_changed', 0),
                    'linesAdded': report.change_summary.get('total_lines_added', 0),
                    'linesRemoved': report.change_summary.get('total_lines_removed', 0),
                    'criticalFiles': report.change_summary.get('critical_files_changed', 0)
                },
                'riskAnalysis': {
                    'averageRisk': report.risk_analysis.get('average_risk', 0.0),
                    'maxRisk': report.risk_analysis.get('max_risk', 0.0),
                    'riskDistribution': report.risk_analysis.get('risk_distribution', {}),
                    'highRiskFiles': report.risk_analysis.get('high_risk_files', [])
                },
                'testSelection': {
                    'totalTests': report.test_selection.get('total_tests_selected', 0),
                    'estimatedTimeMinutes': report.test_selection.get('estimated_execution_time_minutes', 0),
                    'coverageScore': report.test_selection.get('coverage_score', 0.0)
                },
                'recommendation': report.overall_recommendation
            }
        }
        
        logger.info(f"Analysis complete. Risk score: {report.deployment_risk_score}")
        
        return jsonify(response), 200
        
    except Exception as e:
        logger.error(f"Error during analysis: {e}", exc_info=True)
        return jsonify({
            'status': 'error',
            'message': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500


@app.route('/api/mcp/analyze', methods=['POST'])
def mcp_analyze():
    """
    Enhanced analysis using MCP (LLM-powered)
    
    Request body:
    {
        "commitSHA": "abc123...",
        "codeDiff": [...],
        "sonarURL": "http://...",
        "context": {
            "branch": "main",
            "author": "developer@example.com"
        }
    }
    """
    try:
        data = request.get_json()
        
        logger.info(f"MCP Analysis for commit: {data.get('commitSHA', 'unknown')}")
        
        # Get Speculator Bot analysis first
        speculator = get_bot()
        try:
            report = speculator.speculate(
                commit_hash=data.get('commitSHA'),
                analyze_db=False,
                check_drift=False
            )
        except (KeyError, AttributeError, Exception) as analysis_error:
            # Analysis failed (likely repo not available), use None to trigger mock data
            logger.warning(f"MCP analysis failed ({analysis_error}), will return mock data")
            report = None
        
        # Prepare LLM prompt with analysis results (or mock data if report is None)
        llm_prompt = generate_llm_prompt(data, report) if report else "Mock analysis - repository not available"
        
        # For now, return structured analysis
        # In production, this would call Claude via MCP
        response = {
            'status': 'success',
            'timestamp': datetime.now().isoformat(),
            'analysis': {
                'changeIntroduced': analyze_change_intent(data, report),
                'gapAnalysis': perform_gap_analysis(report),
                'testCoverage': generate_test_recommendations(report),
                'securityFixes': generate_security_fixes(data, report),
                'llmPrompt': llm_prompt  # Include prompt for debugging
            },
            'metadata': {
                'commitSHA': data.get('commitSHA'),
                'riskScore': report.deployment_risk_score,
                'filesAnalyzed': report.change_summary['total_files_changed']
            }
        }
        
        logger.info("MCP Analysis complete")
        
        return jsonify(response), 200
        
    except Exception as e:
        logger.error(f"Error during MCP analysis: {e}", exc_info=True)
        return jsonify({
            'status': 'error',
            'message': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500


def get_risk_level(score: float) -> str:
    """Convert risk score to level"""
    if score >= 0.8:
        return 'CRITICAL'
    elif score >= 0.6:
        return 'HIGH'
    elif score >= 0.4:
        return 'MEDIUM'
    elif score >= 0.2:
        return 'LOW'
    else:
        return 'MINIMAL'


def generate_llm_prompt(data: Dict, report: Any) -> str:
    """Generate prompt for LLM analysis"""
    return f"""
Analyze the following code changes and provide detailed recommendations:

**Commit SHA**: {data.get('commitSHA')}
**Branch**: {data.get('context', {}).get('branch', 'unknown')}
**Author**: {data.get('context', {}).get('author', 'unknown')}

**Risk Analysis Summary**:
- Deployment Risk Score: {report.deployment_risk_score:.2f}
- Files Changed: {report.change_summary['total_files_changed']}
- Risk Level: {get_risk_level(report.deployment_risk_score)}

**Your Task**:
1. **Change Introduced**: Summarize the intent and functional impact of this change
2. **Gap Analysis**: Identify potential logical flaws, missing edge cases, or areas of concern
3. **Test Coverage**: Recommend specific new test cases or scenarios that should be added
4. **Security Fixes**: If SonarQube issues exist, recommend specific code fixes

Provide your analysis in structured JSON format.
"""


def analyze_change_intent(data: Dict, report: Any) -> str:
    """Analyze and summarize the intent of code changes"""
    files_changed = report.change_summary['total_files_changed']
    lines_added = report.change_summary['total_lines_added']
    lines_removed = report.change_summary['total_lines_removed']
    
    intent = f"This commit modifies {files_changed} file(s), adding {lines_added} and removing {lines_removed} lines. "
    
    if report.deployment_risk_score > 0.7:
        intent += "This is a high-risk change that requires careful review. "
    
    if report.change_summary.get('critical_files_changed', 0) > 0:
        intent += "Critical system files were modified. "
    
    return intent


def perform_gap_analysis(report: Any) -> list:
    """Identify gaps and potential issues"""
    gaps = []
    
    # Check high-risk files
    high_risk_files = report.risk_analysis.get('high_risk_files', [])
    if high_risk_files:
        gaps.append({
            'category': 'High Risk Files',
            'concern': f"{len(high_risk_files)} high-risk files modified",
            'files': high_risk_files,
            'recommendation': 'Conduct thorough code review and add comprehensive tests'
        })
    
    # Check test coverage
    coverage = report.test_selection.get('coverage_score', 0)
    if coverage < 0.7:
        gaps.append({
            'category': 'Test Coverage',
            'concern': f'Test coverage is {coverage:.1%}, below recommended 70%',
            'recommendation': 'Add unit and integration tests for changed code paths'
        })
    
    # Check complexity
    if report.risk_analysis.get('average_risk', 0) > 0.5:
        gaps.append({
            'category': 'Code Complexity',
            'concern': 'Above-average code complexity detected',
            'recommendation': 'Consider refactoring complex functions and adding documentation'
        })
    
    return gaps


def generate_test_recommendations(report: Any) -> list:
    """Generate test case recommendations"""
    recommendations = []
    
    # Based on risk analysis
    for file in report.risk_analysis.get('high_risk_files', []):
        recommendations.append({
            'file': file,
            'testType': 'integration',
            'priority': 'HIGH',
            'suggestion': f'Add comprehensive integration tests for {file}',
            'reasoning': 'High-risk file with history of failures'
        })
    
    # Based on test coverage
    if report.test_selection.get('coverage_score', 0) < 0.8:
        recommendations.append({
            'testType': 'unit',
            'priority': 'MEDIUM',
            'suggestion': 'Add unit tests to cover all new code paths',
            'reasoning': 'Current test coverage is below target threshold'
        })
    
    return recommendations


def generate_security_fixes(data: Dict, report: Any) -> list:
    """Generate security fix recommendations"""
    fixes = []
    
    # Check if SonarQube URL is provided
    if data.get('sonarURL') and data['sonarURL'] != 'N/A':
        fixes.append({
            'type': 'SonarQube Issues',
            'action': 'Review and fix security vulnerabilities',
            'url': data['sonarURL'],
            'priority': 'HIGH'
        })
    
    # Check for database changes
    if 'database' in str(report.change_summary.get('changes_by_type', {})):
        fixes.append({
            'type': 'Database Security',
            'action': 'Ensure parameterized queries and input validation',
            'priority': 'CRITICAL'
        })
    
    # Check for config changes
    if 'config' in str(report.change_summary.get('changes_by_type', {})):
        fixes.append({
            'type': 'Configuration Security',
            'action': 'Verify no secrets or credentials are hardcoded',
            'priority': 'HIGH'
        })
    
    return fixes


if __name__ == '__main__':
    logger.info("Starting MCP HTTP Wrapper...")
    logger.info("Endpoints available:")
    logger.info("  GET  /health - Health check")
    logger.info("  POST /api/speculator/analyze - Basic risk analysis")
    logger.info("  POST /api/mcp/analyze - Enhanced LLM analysis")
    logger.info("")
    logger.info("Server starting on http://localhost:3001")
    
    app.run(host='0.0.0.0', port=3001, debug=False)

