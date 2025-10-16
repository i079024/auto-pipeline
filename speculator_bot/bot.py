"""
Speculator Bot - Main orchestrator
"""

import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import json
import os

from .core.change_analyzer import ChangeAnalyzer, ChangeMetrics
from .core.risk_analyzer import RiskAnalyzer, RiskScore
from .core.test_selector import TestSelector, TestSelection
from .core.db_validator import DatabaseValidator, SchemaChange, DataDriftReport

logger = logging.getLogger(__name__)


@dataclass
class SpeculationReport:
    """Complete speculation report"""
    timestamp: str
    commit_hash: Optional[str]
    change_summary: Dict
    risk_analysis: Dict
    test_selection: Dict
    schema_analysis: Optional[Dict] = None
    drift_analysis: Optional[Dict] = None
    overall_recommendation: str = ""
    deployment_risk_score: float = 0.0


class SpeculatorBot:
    """
    Main orchestrator for predictive analysis
    """
    
    def __init__(
        self,
        repo_path: str,
        config: Optional[Dict] = None,
        test_catalog_path: Optional[str] = None,
        historical_data_path: Optional[str] = None,
        db_connection: Optional[any] = None
    ):
        """
        Initialize Speculator Bot
        
        Args:
            repo_path: Path to git repository
            config: Configuration dictionary
            test_catalog_path: Path to test catalog
            historical_data_path: Path to historical failure data
            db_connection: Database connection for drift detection
        """
        self.config = config or {}
        self.repo_path = repo_path
        
        # Initialize components
        self.change_analyzer = ChangeAnalyzer(repo_path, config)
        self.risk_analyzer = RiskAnalyzer(config)
        self.test_selector = TestSelector(config, test_catalog_path)
        self.db_validator = DatabaseValidator(config, db_connection)
        
        # Load historical data if available
        if historical_data_path and os.path.exists(historical_data_path):
            self.risk_analyzer.load_historical_data(historical_data_path)
        
        logger.info("Speculator Bot initialized")
    
    def speculate(
        self,
        commit_hash: Optional[str] = None,
        analyze_db: bool = True,
        check_drift: bool = True
    ) -> SpeculationReport:
        """
        Perform complete speculative analysis
        
        Args:
            commit_hash: Specific commit to analyze, or None for staged changes
            analyze_db: Whether to analyze database schema changes
            check_drift: Whether to check for data drift
            
        Returns:
            SpeculationReport with complete analysis
        """
        from datetime import datetime
        
        logger.info(f"Starting speculation for {'commit ' + commit_hash if commit_hash else 'staged changes'}")
        
        # Step 1: Analyze changes
        logger.info("Analyzing code changes...")
        changes = self.change_analyzer.analyze_commit(commit_hash)
        change_summary = self.change_analyzer.get_change_summary(changes)
        
        logger.info(f"Analyzed {len(changes)} changed files")
        
        # Step 2: Analyze risk
        logger.info("Performing risk analysis...")
        risk_results = self.risk_analyzer.analyze_risk(changes)
        risk_summary = self.risk_analyzer.get_risk_summary(risk_results)
        
        logger.info(f"Risk analysis complete. Average risk: {risk_summary['average_risk']:.2f}")
        
        # Step 3: Select tests
        logger.info("Selecting tests...")
        test_selection = self.test_selector.select_tests(risk_results)
        test_summary = self.test_selector.get_selection_summary(test_selection)
        
        logger.info(f"Selected {len(test_selection.selected_tests)} tests")
        
        # Step 4: Database analysis (if applicable)
        schema_summary = None
        drift_summary = None
        
        if analyze_db:
            db_changes = [c for c in changes if c.change_type == 'database']
            
            if db_changes:
                logger.info("Analyzing database schema changes...")
                schema_changes = []
                
                for change in db_changes:
                    try:
                        file_path = os.path.join(self.repo_path, change.file_path)
                        if os.path.exists(file_path):
                            with open(file_path, 'r', encoding='utf-8') as f:
                                sql_content = f.read()
                            
                            file_schema_changes = self.db_validator.analyze_schema_changes(sql_content)
                            schema_changes.extend(file_schema_changes)
                    except Exception as e:
                        logger.warning(f"Could not analyze {change.file_path}: {e}")
                
                if schema_changes:
                    query_impacts = self.db_validator.predict_query_impact(schema_changes)
                    schema_summary = self.db_validator.get_schema_impact_summary(
                        schema_changes,
                        query_impacts
                    )
                    logger.info(f"Found {len(schema_changes)} schema changes")
        
        # Step 5: Data drift detection (if enabled)
        if check_drift and self.db_validator.db_connection:
            logger.info("Checking for data drift...")
            drift_reports = []
            
            # Check drift for tables that have baseline stats
            for table_name in self.db_validator.baseline_stats.keys():
                table_drift = self.db_validator.detect_data_drift(table_name)
                drift_reports.extend(table_drift)
            
            if drift_reports:
                drift_summary = self.db_validator.get_drift_summary(drift_reports)
                logger.info(f"Detected drift in {len(drift_reports)} columns")
        
        # Step 6: Generate overall recommendation
        overall_recommendation, deployment_risk = self._generate_overall_recommendation(
            risk_summary,
            test_summary,
            schema_summary,
            drift_summary
        )
        
        # Create report
        report = SpeculationReport(
            timestamp=datetime.now().isoformat(),
            commit_hash=commit_hash,
            change_summary=change_summary,
            risk_analysis=risk_summary,
            test_selection=test_summary,
            schema_analysis=schema_summary,
            drift_analysis=drift_summary,
            overall_recommendation=overall_recommendation,
            deployment_risk_score=deployment_risk
        )
        
        logger.info("Speculation complete")
        
        return report
    
    def _generate_overall_recommendation(
        self,
        risk_summary: Dict,
        test_summary: Dict,
        schema_summary: Optional[Dict],
        drift_summary: Optional[Dict]
    ) -> Tuple[str, float]:
        """
        Generate overall deployment recommendation
        
        Args:
            risk_summary: Risk analysis summary
            test_summary: Test selection summary
            schema_summary: Schema analysis summary
            drift_summary: Drift detection summary
            
        Returns:
            Tuple of (recommendation string, risk score)
        """
        risk_score = risk_summary['average_risk']
        recommendations = []
        
        # Factor in code risk
        if risk_score > 0.7:
            recommendations.append("⛔ CRITICAL CODE RISK")
            deployment_risk = 0.9
        elif risk_score > 0.5:
            recommendations.append("⚠️ HIGH CODE RISK")
            deployment_risk = 0.7
        else:
            deployment_risk = risk_score
        
        # Factor in test coverage
        coverage = test_summary.get('coverage_score', 0)
        if coverage < 0.5:
            recommendations.append("⚠️ LOW TEST COVERAGE")
            deployment_risk += 0.2
        
        # Factor in schema changes
        if schema_summary:
            if schema_summary.get('risk_level') == 'CRITICAL':
                recommendations.append("⛔ CRITICAL SCHEMA CHANGES")
                deployment_risk += 0.3
            elif schema_summary.get('risk_level') == 'HIGH':
                recommendations.append("⚠️ HIGH-RISK SCHEMA CHANGES")
                deployment_risk += 0.15
        
        # Factor in data drift
        if drift_summary:
            avg_drift = drift_summary.get('average_drift_score', 0)
            if avg_drift > 0.7:
                recommendations.append("⛔ SIGNIFICANT DATA DRIFT")
                deployment_risk += 0.25
            elif avg_drift > 0.4:
                recommendations.append("⚠️ MODERATE DATA DRIFT")
                deployment_risk += 0.1
        
        # Cap deployment risk at 1.0
        deployment_risk = min(deployment_risk, 1.0)
        
        # Generate final recommendation
        if deployment_risk >= 0.8:
            final = "🛑 DO NOT DEPLOY - Critical issues detected. Address all high-risk items before proceeding."
        elif deployment_risk >= 0.6:
            final = "⚠️ DEPLOY WITH EXTREME CAUTION - Multiple risk factors present. Ensure comprehensive testing and monitoring."
        elif deployment_risk >= 0.4:
            final = "⚠️ PROCEED CAREFULLY - Moderate risk detected. Follow standard testing procedures and monitor closely."
        elif deployment_risk >= 0.2:
            final = "✓ SAFE TO DEPLOY - Low risk. Standard deployment process recommended."
        else:
            final = "✅ SAFE TO DEPLOY - Minimal risk detected. Changes appear safe."
        
        if recommendations:
            final = "\n".join(recommendations) + "\n\n" + final
        
        return final, deployment_risk
    
    def export_report(self, report: SpeculationReport, output_path: str, format: str = 'json'):
        """
        Export speculation report to file
        
        Args:
            report: SpeculationReport to export
            output_path: Path to output file
            format: Output format ('json', 'text', 'html')
        """
        os.makedirs(os.path.dirname(output_path) or '.', exist_ok=True)
        
        if format == 'json':
            with open(output_path, 'w') as f:
                json.dump(report.__dict__, f, indent=2, default=str)
        
        elif format == 'text':
            self._export_text_report(report, output_path)
        
        elif format == 'html':
            self._export_html_report(report, output_path)
        
        logger.info(f"Report exported to {output_path}")
    
    def _export_text_report(self, report: SpeculationReport, output_path: str):
        """Export report as formatted text"""
        with open(output_path, 'w') as f:
            f.write("=" * 80 + "\n")
            f.write("SPECULATOR BOT - PREDICTIVE ANALYSIS REPORT\n")
            f.write("=" * 80 + "\n\n")
            
            f.write(f"Timestamp: {report.timestamp}\n")
            if report.commit_hash:
                f.write(f"Commit: {report.commit_hash}\n")
            f.write(f"Deployment Risk Score: {report.deployment_risk_score:.2f}\n\n")
            
            f.write("-" * 80 + "\n")
            f.write("CHANGE SUMMARY\n")
            f.write("-" * 80 + "\n")
            for key, value in report.change_summary.items():
                f.write(f"{key}: {value}\n")
            f.write("\n")
            
            f.write("-" * 80 + "\n")
            f.write("RISK ANALYSIS\n")
            f.write("-" * 80 + "\n")
            f.write(f"Average Risk: {report.risk_analysis['average_risk']:.2f}\n")
            f.write(f"Max Risk: {report.risk_analysis['max_risk']:.2f}\n")
            f.write(f"Risk Distribution: {report.risk_analysis['risk_distribution']}\n")
            f.write(f"\nDeployment Recommendation: {report.risk_analysis['deployment_recommendation']}\n\n")
            
            f.write("-" * 80 + "\n")
            f.write("TEST SELECTION\n")
            f.write("-" * 80 + "\n")
            f.write(f"Tests Selected: {report.test_selection['total_tests_selected']}\n")
            f.write(f"Estimated Time: {report.test_selection['estimated_execution_time_minutes']:.1f} minutes\n")
            f.write(f"Coverage Score: {report.test_selection['coverage_score']:.2f}\n\n")
            
            if report.schema_analysis:
                f.write("-" * 80 + "\n")
                f.write("DATABASE SCHEMA ANALYSIS\n")
                f.write("-" * 80 + "\n")
                for key, value in report.schema_analysis.items():
                    f.write(f"{key}: {value}\n")
                f.write("\n")
            
            if report.drift_analysis:
                f.write("-" * 80 + "\n")
                f.write("DATA DRIFT ANALYSIS\n")
                f.write("-" * 80 + "\n")
                for key, value in report.drift_analysis.items():
                    f.write(f"{key}: {value}\n")
                f.write("\n")
            
            f.write("=" * 80 + "\n")
            f.write("OVERALL RECOMMENDATION\n")
            f.write("=" * 80 + "\n")
            f.write(report.overall_recommendation + "\n")
            f.write("=" * 80 + "\n")
    
    def _export_html_report(self, report: SpeculationReport, output_path: str):
        """Export report as HTML"""
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Speculator Bot Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 30px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        h1 {{ color: #2c3e50; border-bottom: 3px solid #3498db; padding-bottom: 10px; }}
        h2 {{ color: #34495e; border-left: 4px solid #3498db; padding-left: 10px; margin-top: 30px; }}
        .metric {{ display: inline-block; margin: 10px 20px 10px 0; padding: 15px; background: #ecf0f1; border-radius: 5px; }}
        .metric-label {{ font-weight: bold; color: #7f8c8d; font-size: 0.9em; }}
        .metric-value {{ font-size: 1.5em; color: #2c3e50; }}
        .risk-high {{ color: #e74c3c; font-weight: bold; }}
        .risk-medium {{ color: #f39c12; font-weight: bold; }}
        .risk-low {{ color: #27ae60; font-weight: bold; }}
        .recommendation {{ padding: 20px; background: #fff3cd; border-left: 5px solid #ffc107; margin: 20px 0; }}
        .critical {{ background: #f8d7da; border-left: 5px solid #dc3545; }}
        table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
        th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }}
        th {{ background-color: #3498db; color: white; }}
        tr:hover {{ background-color: #f5f5f5; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🤖 Speculator Bot - Predictive Analysis Report</h1>
        <p><strong>Timestamp:</strong> {report.timestamp}</p>
        {f'<p><strong>Commit:</strong> {report.commit_hash}</p>' if report.commit_hash else ''}
        <p><strong>Deployment Risk Score:</strong> <span class="risk-{'high' if report.deployment_risk_score > 0.6 else 'medium' if report.deployment_risk_score > 0.3 else 'low'}">{report.deployment_risk_score:.2f}</span></p>
        
        <h2>📊 Change Summary</h2>
        <div class="metric">
            <div class="metric-label">Files Changed</div>
            <div class="metric-value">{report.change_summary['total_files_changed']}</div>
        </div>
        <div class="metric">
            <div class="metric-label">Lines Added</div>
            <div class="metric-value">{report.change_summary['total_lines_added']}</div>
        </div>
        <div class="metric">
            <div class="metric-label">Lines Removed</div>
            <div class="metric-value">{report.change_summary['total_lines_removed']}</div>
        </div>
        
        <h2>⚠️ Risk Analysis</h2>
        <div class="metric">
            <div class="metric-label">Average Risk</div>
            <div class="metric-value">{report.risk_analysis['average_risk']:.2f}</div>
        </div>
        <div class="metric">
            <div class="metric-label">Max Risk</div>
            <div class="metric-value">{report.risk_analysis['max_risk']:.2f}</div>
        </div>
        <p><strong>Deployment Recommendation:</strong> {report.risk_analysis['deployment_recommendation']}</p>
        
        <h2>🧪 Test Selection</h2>
        <div class="metric">
            <div class="metric-label">Tests Selected</div>
            <div class="metric-value">{report.test_selection['total_tests_selected']}</div>
        </div>
        <div class="metric">
            <div class="metric-label">Est. Time (min)</div>
            <div class="metric-value">{report.test_selection['estimated_execution_time_minutes']:.1f}</div>
        </div>
        <div class="metric">
            <div class="metric-label">Coverage Score</div>
            <div class="metric-value">{report.test_selection['coverage_score']:.2f}</div>
        </div>
        
        {'<h2>🗄️ Database Schema Analysis</h2>' + self._format_dict_to_html(report.schema_analysis) if report.schema_analysis else ''}
        {'<h2>📈 Data Drift Analysis</h2>' + self._format_dict_to_html(report.drift_analysis) if report.drift_analysis else ''}
        
        <h2>🎯 Overall Recommendation</h2>
        <div class="recommendation {'critical' if report.deployment_risk_score > 0.7 else ''}">
            <pre>{report.overall_recommendation}</pre>
        </div>
    </div>
</body>
</html>
"""
        with open(output_path, 'w') as f:
            f.write(html)
    
    def _format_dict_to_html(self, data: Dict) -> str:
        """Format dictionary as HTML"""
        html = "<table><tr><th>Key</th><th>Value</th></tr>"
        for key, value in data.items():
            html += f"<tr><td>{key}</td><td>{value}</td></tr>"
        html += "</table>"
        return html

