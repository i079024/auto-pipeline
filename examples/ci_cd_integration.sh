#!/bin/bash
# Example CI/CD integration script for Speculator Bot
# This script can be used in Jenkins, GitLab CI, GitHub Actions, etc.

set -e

echo "🤖 Starting Speculator Bot Analysis"
echo "======================================"

# Configuration
REPO_PATH="${REPO_PATH:-.}"
CONFIG_FILE="${CONFIG_FILE:-config.yaml}"
TEST_CATALOG="${TEST_CATALOG:-examples/test_catalog.json}"
HISTORICAL_DATA="${HISTORICAL_DATA:-examples/historical_failures.json}"
REPORT_DIR="${REPORT_DIR:-reports}"
MAX_RISK_SCORE="${MAX_RISK_SCORE:-0.7}"

# Create report directory
mkdir -p "$REPORT_DIR"

# Generate timestamp for report
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
REPORT_FILE="$REPORT_DIR/speculator_report_${TIMESTAMP}.json"
HTML_REPORT="$REPORT_DIR/speculator_report_${TIMESTAMP}.html"

echo "Configuration:"
echo "  Repository: $REPO_PATH"
echo "  Config: $CONFIG_FILE"
echo "  Test Catalog: $TEST_CATALOG"
echo "  Max Risk Score: $MAX_RISK_SCORE"
echo ""

# Run Speculator Bot analysis
echo "Running analysis..."
speculator analyze \
  --repo "$REPO_PATH" \
  --config "$CONFIG_FILE" \
  --test-catalog "$TEST_CATALOG" \
  --historical-data "$HISTORICAL_DATA" \
  --output "$REPORT_FILE" \
  --format json

# Also generate HTML report for viewing
speculator analyze \
  --repo "$REPO_PATH" \
  --config "$CONFIG_FILE" \
  --test-catalog "$TEST_CATALOG" \
  --historical-data "$HISTORICAL_DATA" \
  --output "$HTML_REPORT" \
  --format html

echo ""
echo "✓ Analysis complete"
echo "  JSON Report: $REPORT_FILE"
echo "  HTML Report: $HTML_REPORT"
echo ""

# Parse results
if command -v jq &> /dev/null; then
    RISK_SCORE=$(jq -r '.deployment_risk_score' "$REPORT_FILE")
    RECOMMENDATION=$(jq -r '.overall_recommendation' "$REPORT_FILE" | head -n 1)
    TESTS_SELECTED=$(jq -r '.test_selection.total_tests_selected' "$REPORT_FILE")
    COVERAGE=$(jq -r '.test_selection.coverage_score' "$REPORT_FILE")
    
    echo "Results:"
    echo "  Deployment Risk Score: $RISK_SCORE"
    echo "  Tests Selected: $TESTS_SELECTED"
    echo "  Coverage Score: $COVERAGE"
    echo ""
    echo "Recommendation:"
    echo "  $RECOMMENDATION"
    echo ""
    
    # Decision logic
    if (( $(echo "$RISK_SCORE >= 0.8" | bc -l) )); then
        echo "❌ DEPLOYMENT BLOCKED"
        echo "   Risk score ($RISK_SCORE) exceeds critical threshold (0.8)"
        echo "   Please address high-risk changes before proceeding."
        exit 1
    elif (( $(echo "$RISK_SCORE >= $MAX_RISK_SCORE" | bc -l) )); then
        echo "⚠️ MANUAL APPROVAL REQUIRED"
        echo "   Risk score ($RISK_SCORE) exceeds threshold ($MAX_RISK_SCORE)"
        echo "   Review the report and approve manually if acceptable."
        exit 2
    else
        echo "✅ DEPLOYMENT APPROVED"
        echo "   Risk score ($RISK_SCORE) is within acceptable range."
    fi
else
    echo "⚠️ Warning: jq not installed. Cannot parse JSON results."
    echo "   Install jq for automated decision making."
    exit 0
fi

# Optional: Send notification to Slack, email, etc.
# if [ -n "$SLACK_WEBHOOK" ]; then
#     curl -X POST "$SLACK_WEBHOOK" \
#         -H 'Content-Type: application/json' \
#         -d "{\"text\":\"Speculator Bot: Risk Score $RISK_SCORE for commit $CI_COMMIT_SHA\"}"
# fi

# Optional: Upload report to artifact storage
# aws s3 cp "$HTML_REPORT" "s3://your-bucket/reports/"

echo ""
echo "🎉 Analysis complete!"

