#!/usr/bin/env python3
"""
Quick Analysis Script - Test Speculator Bot without MCP

This script lets you quickly test Speculator Bot functionality
without needing Claude Desktop or MCP setup.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from speculator_bot import SpeculatorBot
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

console = Console()


def quick_risk_analysis():
    """Quick risk analysis of current changes"""
    console.print(Panel.fit(
        "[bold blue]🤖 Speculator Bot - Quick Analysis[/bold blue]",
        border_style="blue"
    ))
    
    try:
        # Initialize bot
        console.print("\n[yellow]Initializing bot...[/yellow]")
        bot = SpeculatorBot(
            repo_path='.',
            test_catalog_path='examples/test_catalog.json',
            historical_data_path='examples/historical_failures.json'
        )
        
        # Run analysis
        console.print("[yellow]Analyzing changes...[/yellow]\n")
        report = bot.speculate(analyze_db=False, check_drift=False)
        
        # Display results
        display_results(report)
        
        # Offer to export
        export = input("\nExport report? (y/n): ").strip().lower()
        if export == 'y':
            format_choice = input("Format (html/json/text): ").strip().lower()
            if format_choice in ['html', 'json', 'text']:
                output_path = f"quick_analysis_report.{format_choice}"
                bot.export_report(report, output_path, format_choice)
                console.print(f"\n✅ [green]Report exported to: {output_path}[/green]")
        
    except Exception as e:
        console.print(f"\n❌ [red]Error: {e}[/red]")
        import traceback
        traceback.print_exc()


def display_results(report):
    """Display analysis results in a nice format"""
    
    # Risk Score
    risk_color = "red" if report.deployment_risk_score > 0.6 else "yellow" if report.deployment_risk_score > 0.3 else "green"
    console.print(Panel(
        f"[bold]Deployment Risk Score:[/bold] [{risk_color}]{report.deployment_risk_score:.2f}[/{risk_color}]",
        title="📊 Risk Assessment",
        border_style=risk_color
    ))
    
    # Change Summary
    table = Table(title="\n📝 Changes", show_header=True)
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="magenta")
    
    table.add_row("Files Changed", str(report.change_summary['total_files_changed']))
    table.add_row("Lines Added", str(report.change_summary['total_lines_added']))
    table.add_row("Lines Removed", str(report.change_summary['total_lines_removed']))
    table.add_row("Critical Files", str(report.change_summary.get('critical_files_changed', 0)))
    
    console.print(table)
    
    # Risk Details
    table = Table(title="\n⚠️ Risk Analysis", show_header=True)
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="magenta")
    
    table.add_row("Average Risk", f"{report.risk_analysis['average_risk']:.2f}")
    table.add_row("Max Risk", f"{report.risk_analysis['max_risk']:.2f}")
    
    risk_dist = report.risk_analysis.get('risk_distribution', {})
    table.add_row("High Risk Files", f"[red]{risk_dist.get('high', 0)}[/red]")
    table.add_row("Medium Risk Files", f"[yellow]{risk_dist.get('medium', 0)}[/yellow]")
    table.add_row("Low Risk Files", f"[green]{risk_dist.get('low', 0)}[/green]")
    
    console.print(table)
    
    # Test Selection
    table = Table(title="\n🧪 Test Selection", show_header=True)
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="magenta")
    
    table.add_row("Tests Selected", str(report.test_selection['total_tests_selected']))
    table.add_row("Estimated Time", f"{report.test_selection['estimated_execution_time_minutes']:.1f} min")
    table.add_row("Coverage Score", f"{report.test_selection['coverage_score']:.2%}")
    
    console.print(table)
    
    # Recommendation
    console.print("\n")
    rec_color = "red" if report.deployment_risk_score > 0.7 else "yellow" if report.deployment_risk_score > 0.4 else "green"
    console.print(Panel(
        report.overall_recommendation,
        title="🎯 Recommendation",
        border_style=rec_color
    ))


if __name__ == "__main__":
    console.print("\n" + "=" * 70)
    console.print("  SPECULATOR BOT - QUICK ANALYSIS")
    console.print("=" * 70 + "\n")
    
    try:
        quick_risk_analysis()
    except KeyboardInterrupt:
        console.print("\n\n⚠️ [yellow]Analysis interrupted[/yellow]")
    except Exception as e:
        console.print(f"\n❌ [red]Fatal error: {e}[/red]")

