# 🤖 Speculator Bot - AI-Assisted Predictive Analysis

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A sophisticated tool for predictive quality assurance and risk assessment that helps teams deploy with confidence by predicting potential failures before they happen.

## 🎯 Features

### Infrastructure Validation (Risk Prediction)
- **Failure Speculation**: Analyzes code commits and configuration updates, correlating them with historical failure data
- **Predictive Test Selection**: Intelligently selects and prioritizes a minimal set of regression/performance tests most likely to fail
- **Risk Scoring**: Moves validation from simple pass/fail to risk scoring, allowing teams to deploy based on acceptable risk levels

### Database Validation (Schema/Data Drift)
- **Schema Prediction**: Predicts how new application features might affect database schema or query performance
- **Data Drift Detection**: Monitors data patterns and flags subtle, undesirable changes in data quality or distribution
- **Query Impact Analysis**: Estimates performance impact of schema changes on existing queries

### 🤖 Model Context Protocol (MCP) Server
- **AI Assistant Integration**: Connect Speculator Bot to Claude Desktop and other AI assistants
- **Tools**: Expose risk analysis, test selection, and drift detection as MCP tools
- **Resources**: Access configuration and status via MCP resources
- **Prompts**: Pre-built prompts for common analysis workflows
- **Secure**: Standardized protocol for safe AI-tool interaction

## 🚀 Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/speculator-bot.git
cd speculator-bot

# Install dependencies
pip install -r requirements.txt

# Or install as a package
pip install -e .
```

### Initialize Configuration

```bash
speculator init
```

This creates:
- `config.yaml` - Main configuration file
- `models/` - Directory for ML models
- `logs/` - Directory for log files
- `data/` - Directory for test catalogs and historical data

### Basic Usage

```bash
# Analyze current staged changes
speculator analyze

# Analyze a specific commit
speculator analyze --commit abc123

# Analyze with custom config and test catalog
speculator analyze --config my_config.yaml --test-catalog tests.json

# Export report to file
speculator analyze --output report.html --format html
```

## 📋 Configuration

Edit `config.yaml` to customize:

```yaml
# Risk Analysis Settings
risk_analysis:
  enabled: true
  historical_window_days: 90
  min_confidence_threshold: 0.6
  risk_levels:
    high: 0.7
    medium: 0.4
    low: 0.2

# Test Selection Settings
test_selection:
  enabled: true
  max_tests: 50
  prioritize_by_risk: true
  include_critical_tests: true

# Database Validation Settings
database_validation:
  enabled: true
  schema_analysis: true
  data_drift_detection: true
  drift_threshold: 0.15
  sample_size: 1000
```

## 🤖 MCP Server Integration

Speculator Bot includes a **Model Context Protocol (MCP)** server for seamless integration with AI assistants like Claude Desktop.

### Quick Setup

```bash
# 1. Install MCP SDK
pip install mcp

# 2. Test the MCP server
python examples/test_mcp_server.py

# 3. Configure Claude Desktop
cp claude_desktop_config.json ~/Library/Application\ Support/Claude/claude_desktop_config.json

# 4. Restart Claude Desktop and try:
#    "Analyze deployment risk for my changes"
```

### Available MCP Tools

- **analyze_risk**: Complete risk analysis with recommendations
- **select_tests**: Intelligent test selection based on changes  
- **check_data_drift**: Detect data quality issues
- **export_report**: Generate reports in various formats

### Example Usage in Claude

```
You: "Analyze the deployment risk for commit abc123"

Claude: [Uses MCP analyze_risk tool]
Analysis Results:
- Deployment Risk Score: 0.68 (HIGH)
- Files Changed: 5
- Recommendations: Run comprehensive testing, deploy to staging first

You: "Which tests should I run?"

Claude: [Uses MCP select_tests tool]
Selected 18 critical tests covering all changed files.
Estimated time: 6.5 minutes. Coverage: 92%
```

See **[MCP_SETUP.md](MCP_SETUP.md)** for complete setup guide and advanced features.

---

## 📊 Input Data Formats

### Test Catalog Format

Create a `test_catalog.json` file:

```json
[
  {
    "test_id": "test_001",
    "test_name": "User Authentication Test",
    "test_path": "tests/auth/test_login.py",
    "test_type": "integration",
    "execution_time_seconds": 12.5,
    "covered_files": [
      "src/auth/login.py",
      "src/auth/session.py"
    ],
    "criticality": "critical",
    "failure_count": 0,
    "dependencies": []
  }
]
```

### Historical Failure Data Format

Create a `historical_failures.json` file:

```json
[
  {
    "timestamp": "2024-10-01T10:30:00",
    "file_path": "src/payment/processor.py",
    "failure_type": "runtime_error",
    "severity": "high",
    "resolution_time_hours": 4.5,
    "related_commits": ["abc123", "def456"],
    "metadata": {
      "error_message": "Payment processing failed",
      "affected_users": 150
    }
  }
]
```

## 💡 Usage Examples

### Example 1: Pre-deployment Risk Check

```bash
# Run complete analysis before deployment
speculator analyze \
  --commit HEAD \
  --test-catalog data/tests.json \
  --historical-data data/failures.json \
  --output reports/pre-deploy-$(date +%Y%m%d).html \
  --format html
```

### Example 2: CI/CD Pipeline Integration

```bash
#!/bin/bash
# In your CI/CD pipeline

# Run speculation
speculator analyze --output report.json --format json

# Parse results and fail build if risk is too high
RISK_SCORE=$(jq '.deployment_risk_score' report.json)

if (( $(echo "$RISK_SCORE > 0.7" | bc -l) )); then
  echo "❌ Deployment blocked: Risk score too high ($RISK_SCORE)"
  exit 1
else
  echo "✅ Risk acceptable: $RISK_SCORE"
fi
```

### Example 3: Database Migration Safety Check

```bash
# Analyze database migration files
speculator analyze \
  --repo /path/to/repo \
  --commit migration-branch \
  --output migration-analysis.txt \
  --format text
```

### Example 4: Capture Baseline for Drift Detection

```bash
# Capture current data state as baseline
speculator capture-baseline \
  --db-connection "postgresql://user:pass@localhost/db" \
  --tables users payments orders
```

## 🏗️ Architecture

```
speculator_bot/
├── core/
│   ├── change_analyzer.py    # Analyzes Git changes
│   ├── risk_analyzer.py       # Predicts failure risk
│   ├── test_selector.py       # Selects optimal tests
│   └── db_validator.py        # Database validation & drift detection
├── bot.py                     # Main orchestrator
├── cli.py                     # Command-line interface
└── __init__.py
```

## 🔧 Advanced Features

### Machine Learning Model Training

```bash
# Train risk prediction model with historical data
speculator train \
  --historical-data data/failures.json \
  --repo /path/to/repo
```

### Custom Risk Weights

Adjust feature weights in `config.yaml`:

```yaml
feature_weights:
  code_complexity: 0.25      # Weight for code complexity
  historical_failures: 0.35   # Weight for past failures
  change_magnitude: 0.20      # Weight for size of change
  file_criticality: 0.20      # Weight for critical files
```

### Integration with Monitoring Tools

```python
from speculator_bot import SpeculatorBot

# Initialize bot
bot = SpeculatorBot(
    repo_path='.',
    test_catalog_path='tests.json',
    historical_data_path='failures.json'
)

# Run analysis
report = bot.speculate(commit_hash='HEAD')

# Send to monitoring system
send_to_datadog({
    'deployment_risk': report.deployment_risk_score,
    'tests_selected': len(report.test_selection['selected_tests']),
    'risk_level': report.risk_analysis['risk_distribution']
})
```

## 📈 Output Reports

### Text Report
```
================================================================================
SPECULATOR BOT - PREDICTIVE ANALYSIS REPORT
================================================================================

Timestamp: 2024-10-10T14:30:00
Deployment Risk Score: 0.45

--------------------------------------------------------------------------------
CHANGE SUMMARY
--------------------------------------------------------------------------------
total_files_changed: 5
total_lines_added: 120
total_lines_removed: 45
critical_files_changed: 1

--------------------------------------------------------------------------------
RISK ANALYSIS
--------------------------------------------------------------------------------
Average Risk: 0.42
Max Risk: 0.68
Risk Distribution: {'high': 1, 'medium': 2, 'low': 2}

Deployment Recommendation: ✓ PROCEED WITH CARE
```

### HTML Report
Beautiful, interactive HTML reports with charts and detailed breakdowns.

### JSON Report
Machine-readable format for integration with other tools.

## 🎯 Use Cases

1. **Pre-Deployment Risk Assessment**: Evaluate risk before merging PRs
2. **Intelligent Test Selection**: Save CI/CD time by running only relevant tests
3. **Database Migration Safety**: Predict schema change impacts
4. **Data Quality Monitoring**: Detect data drift early
5. **Technical Debt Tracking**: Identify high-risk areas needing refactoring

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- Built with Python, scikit-learn, pandas, and rich
- Inspired by modern DevOps and SRE practices
- Designed for teams who value proactive quality assurance

## 📞 Support

For issues, questions, or suggestions:
- Open an issue on GitHub
- Contact: speculator-bot@example.com

---

**Made with ❤️ by the Speculator Bot Team**

