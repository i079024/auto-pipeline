"""
Command Line Interface for Speculator Bot
"""

import click
import logging
import yaml
import sys
import os
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import print as rprint

from .bot import SpeculatorBot


console = Console()


def setup_logging(verbose: bool):
    """Setup logging configuration"""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('speculator_bot.log')
        ]
    )


def load_config(config_path: str) -> dict:
    """Load configuration from YAML file"""
    if not os.path.exists(config_path):
        console.print(f"[yellow]Warning: Config file not found at {config_path}, using defaults[/yellow]")
        return {}
    
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)


@click.group()
@click.version_option(version='1.0.0')
def cli():
    """
    🤖 Speculator Bot - AI-Assisted Predictive Analysis
    
    A sophisticated tool for predictive quality assurance and risk assessment.
    """
    pass


@cli.command()
@click.option('--repo', '-r', default='.', help='Path to git repository')
@click.option('--config', '-c', default='config.yaml', help='Path to configuration file')
@click.option('--commit', help='Specific commit hash to analyze')
@click.option('--test-catalog', help='Path to test catalog JSON file')
@click.option('--historical-data', help='Path to historical failure data JSON file')
@click.option('--output', '-o', help='Output file for report')
@click.option('--format', '-f', type=click.Choice(['json', 'text', 'html']), default='text', help='Output format')
@click.option('--no-db', is_flag=True, help='Skip database analysis')
@click.option('--no-drift', is_flag=True, help='Skip data drift detection')
@click.option('--verbose', '-v', is_flag=True, help='Verbose output')
def analyze(repo, config, commit, test_catalog, historical_data, output, format, no_db, no_drift, verbose):
    """
    Perform predictive analysis on code changes
    """
    setup_logging(verbose)
    
    console.print(Panel.fit(
        "[bold blue]🤖 Speculator Bot[/bold blue]\n"
        "[dim]AI-Assisted Predictive Analysis[/dim]",
        border_style="blue"
    ))
    
    # Load configuration
    config_data = load_config(config)
    
    # Initialize bot
    with console.status("[bold green]Initializing Speculator Bot..."):
        try:
            bot = SpeculatorBot(
                repo_path=repo,
                config=config_data,
                test_catalog_path=test_catalog,
                historical_data_path=historical_data
            )
            console.print("✓ Bot initialized successfully", style="green")
        except Exception as e:
            console.print(f"✗ Failed to initialize bot: {e}", style="red")
            sys.exit(1)
    
    # Perform speculation
    with console.status("[bold yellow]Analyzing changes and predicting risks..."):
        try:
            report = bot.speculate(
                commit_hash=commit,
                analyze_db=not no_db,
                check_drift=not no_drift
            )
            console.print("✓ Analysis complete", style="green")
        except Exception as e:
            console.print(f"✗ Analysis failed: {e}", style="red")
            sys.exit(1)
    
    # Display results
    _display_report(report)
    
    # Export if requested
    if output:
        bot.export_report(report, output, format)
        console.print(f"\n✓ Report exported to: {output}", style="green")


def _display_report(report):
    """Display report in terminal with rich formatting"""
    
    # Header
    console.print("\n")
    risk_color = "red" if report.deployment_risk_score > 0.6 else "yellow" if report.deployment_risk_score > 0.3 else "green"
    console.print(Panel(
        f"[bold]Deployment Risk Score:[/bold] [{risk_color}]{report.deployment_risk_score:.2f}[/{risk_color}]\n"
        f"[dim]{report.timestamp}[/dim]",
        title="📊 Analysis Summary",
        border_style=risk_color
    ))
    
    # Change Summary
    table = Table(title="📝 Change Summary", show_header=True)
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="magenta")
    
    table.add_row("Files Changed", str(report.change_summary['total_files_changed']))
    table.add_row("Lines Added", str(report.change_summary['total_lines_added']))
    table.add_row("Lines Removed", str(report.change_summary['total_lines_removed']))
    table.add_row("Critical Files", str(report.change_summary['critical_files_changed']))
    
    console.print(table)
    
    # Risk Analysis
    table = Table(title="⚠️ Risk Analysis", show_header=True)
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="magenta")
    
    avg_risk = report.risk_analysis['average_risk']
    risk_color = "red" if avg_risk > 0.6 else "yellow" if avg_risk > 0.3 else "green"
    table.add_row("Average Risk", f"[{risk_color}]{avg_risk:.2f}[/{risk_color}]")
    table.add_row("Max Risk", f"{report.risk_analysis['max_risk']:.2f}")
    
    risk_dist = report.risk_analysis['risk_distribution']
    table.add_row("High Risk Files", f"[red]{risk_dist.get('high', 0)}[/red]")
    table.add_row("Medium Risk Files", f"[yellow]{risk_dist.get('medium', 0)}[/yellow]")
    table.add_row("Low Risk Files", f"[green]{risk_dist.get('low', 0)}[/green]")
    
    console.print(table)
    
    # Test Selection
    table = Table(title="🧪 Test Selection", show_header=True)
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="magenta")
    
    table.add_row("Tests Selected", str(report.test_selection['total_tests_selected']))
    table.add_row("Estimated Time", f"{report.test_selection['estimated_execution_time_minutes']:.1f} min")
    table.add_row("Coverage Score", f"{report.test_selection['coverage_score']:.2%}")
    
    console.print(table)
    
    # Database Analysis
    if report.schema_analysis:
        table = Table(title="🗄️ Database Schema Analysis", show_header=True)
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="magenta")
        
        table.add_row("Total Changes", str(report.schema_analysis['total_changes']))
        table.add_row("Risk Level", report.schema_analysis['risk_level'])
        table.add_row("Affected Tables", str(len(report.schema_analysis['affected_tables'])))
        
        console.print(table)
    
    # Data Drift
    if report.drift_analysis and 'drift_detected_columns' in report.drift_analysis:
        table = Table(title="📈 Data Drift Analysis", show_header=True)
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="magenta")
        
        table.add_row("Columns with Drift", str(report.drift_analysis['drift_detected_columns']))
        table.add_row("Average Drift Score", f"{report.drift_analysis['average_drift_score']:.2f}")
        
        console.print(table)
    
    # Overall Recommendation
    console.print("\n")
    rec_color = "red" if report.deployment_risk_score > 0.7 else "yellow" if report.deployment_risk_score > 0.4 else "green"
    console.print(Panel(
        report.overall_recommendation,
        title="🎯 Overall Recommendation",
        border_style=rec_color
    ))


@cli.command()
@click.option('--repo', '-r', default='.', help='Path to git repository')
@click.option('--config', '-c', default='config.yaml', help='Path to configuration file')
@click.option('--historical-data', help='Path to historical failure data JSON file')
@click.option('--verbose', '-v', is_flag=True, help='Verbose output')
def train(repo, config, historical_data, verbose):
    """
    Train the risk prediction model with historical data
    """
    setup_logging(verbose)
    
    console.print("[bold blue]Training risk prediction model...[/bold blue]")
    
    if not historical_data or not os.path.exists(historical_data):
        console.print("[red]Error: Historical data file required for training[/red]")
        sys.exit(1)
    
    # Load configuration
    config_data = load_config(config)
    
    # Initialize bot
    bot = SpeculatorBot(
        repo_path=repo,
        config=config_data,
        historical_data_path=historical_data
    )
    
    # TODO: Implement training logic with historical data
    console.print("[yellow]Training functionality to be implemented with actual historical data[/yellow]")


@cli.command()
@click.option('--config', '-c', default='config.yaml', help='Path to configuration file')
@click.option('--db-connection', help='Database connection string')
@click.option('--tables', '-t', multiple=True, help='Specific tables to capture baseline for')
@click.option('--verbose', '-v', is_flag=True, help='Verbose output')
def capture_baseline(config, db_connection, tables, verbose):
    """
    Capture baseline statistics for data drift detection
    """
    setup_logging(verbose)
    
    console.print("[bold blue]Capturing baseline statistics...[/bold blue]")
    
    if not db_connection:
        console.print("[red]Error: Database connection string required[/red]")
        sys.exit(1)
    
    # Load configuration
    config_data = load_config(config)
    
    # Initialize database validator
    from .core.db_validator import DatabaseValidator
    validator = DatabaseValidator(config=config_data)
    
    # TODO: Implement baseline capture with actual DB connection
    console.print("[yellow]Baseline capture functionality to be implemented with actual DB connection[/yellow]")


@cli.command()
def init():
    """
    Initialize Speculator Bot configuration
    """
    console.print("[bold blue]Initializing Speculator Bot...[/bold blue]\n")
    
    # Create config file
    if not os.path.exists('config.yaml'):
        import shutil
        config_template = Path(__file__).parent.parent / 'config.yaml'
        if config_template.exists():
            shutil.copy(config_template, 'config.yaml')
            console.print("✓ Created config.yaml", style="green")
        else:
            console.print("[yellow]Warning: Could not find config template[/yellow]")
    else:
        console.print("[yellow]config.yaml already exists[/yellow]")
    
    # Create directories
    os.makedirs('models', exist_ok=True)
    os.makedirs('logs', exist_ok=True)
    os.makedirs('data', exist_ok=True)
    
    console.print("✓ Created directories: models/, logs/, data/", style="green")
    
    console.print("\n[bold green]Initialization complete![/bold green]")
    console.print("\nNext steps:")
    console.print("1. Edit config.yaml to customize settings")
    console.print("2. Prepare test catalog (JSON) if using test selection")
    console.print("3. Prepare historical failure data (JSON) for better predictions")
    console.print("4. Run: speculator analyze --help")


if __name__ == '__main__':
    cli()

