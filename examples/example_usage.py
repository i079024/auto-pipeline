"""
Example usage of Speculator Bot Python API
"""

from speculator_bot import SpeculatorBot
import json


def example_basic_analysis():
    """Basic example: Analyze current changes"""
    print("=" * 80)
    print("EXAMPLE 1: Basic Analysis")
    print("=" * 80)
    
    # Initialize bot
    bot = SpeculatorBot(
        repo_path='.',
        config=None,  # Uses default config
        test_catalog_path='examples/test_catalog.json',
        historical_data_path='examples/historical_failures.json'
    )
    
    # Run analysis
    report = bot.speculate()
    
    # Print results
    print(f"\nDeployment Risk Score: {report.deployment_risk_score:.2f}")
    print(f"Files Changed: {report.change_summary['total_files_changed']}")
    print(f"Average Risk: {report.risk_analysis['average_risk']:.2f}")
    print(f"Tests Selected: {report.test_selection['total_tests_selected']}")
    print(f"\nRecommendation:\n{report.overall_recommendation}")


def example_specific_commit():
    """Example: Analyze a specific commit"""
    print("\n" + "=" * 80)
    print("EXAMPLE 2: Analyze Specific Commit")
    print("=" * 80)
    
    bot = SpeculatorBot(
        repo_path='.',
        test_catalog_path='examples/test_catalog.json',
        historical_data_path='examples/historical_failures.json'
    )
    
    # Analyze specific commit
    report = bot.speculate(commit_hash='HEAD~1')
    
    print(f"\nCommit: {report.commit_hash}")
    print(f"Deployment Risk: {report.deployment_risk_score:.2f}")
    
    # Export to JSON
    bot.export_report(report, 'output/analysis_report.json', format='json')
    print("\nReport exported to: output/analysis_report.json")


def example_custom_config():
    """Example: Use custom configuration"""
    print("\n" + "=" * 80)
    print("EXAMPLE 3: Custom Configuration")
    print("=" * 80)
    
    # Custom configuration
    custom_config = {
        'risk_analysis': {
            'enabled': True,
            'risk_levels': {
                'high': 0.8,  # Stricter high-risk threshold
                'medium': 0.5,
                'low': 0.3
            }
        },
        'test_selection': {
            'enabled': True,
            'max_tests': 30,  # Run fewer tests
            'prioritize_by_risk': True
        },
        'feature_weights': {
            'code_complexity': 0.2,
            'historical_failures': 0.5,  # Emphasize history
            'change_magnitude': 0.15,
            'file_criticality': 0.15
        }
    }
    
    bot = SpeculatorBot(
        repo_path='.',
        config=custom_config,
        test_catalog_path='examples/test_catalog.json',
        historical_data_path='examples/historical_failures.json'
    )
    
    report = bot.speculate()
    
    print(f"\nDeployment Risk: {report.deployment_risk_score:.2f}")
    print(f"Risk Distribution: {report.risk_analysis['risk_distribution']}")


def example_export_formats():
    """Example: Export reports in different formats"""
    print("\n" + "=" * 80)
    print("EXAMPLE 4: Export Reports")
    print("=" * 80)
    
    bot = SpeculatorBot(
        repo_path='.',
        test_catalog_path='examples/test_catalog.json',
        historical_data_path='examples/historical_failures.json'
    )
    
    report = bot.speculate()
    
    # Export in different formats
    bot.export_report(report, 'output/report.json', format='json')
    print("✓ JSON report: output/report.json")
    
    bot.export_report(report, 'output/report.txt', format='text')
    print("✓ Text report: output/report.txt")
    
    bot.export_report(report, 'output/report.html', format='html')
    print("✓ HTML report: output/report.html")


def example_access_detailed_results():
    """Example: Access detailed analysis results"""
    print("\n" + "=" * 80)
    print("EXAMPLE 5: Detailed Results Access")
    print("=" * 80)
    
    bot = SpeculatorBot(
        repo_path='.',
        test_catalog_path='examples/test_catalog.json',
        historical_data_path='examples/historical_failures.json'
    )
    
    report = bot.speculate()
    
    # Access change summary details
    print("\nChange Summary:")
    for key, value in report.change_summary.items():
        print(f"  {key}: {value}")
    
    # Access risk analysis details
    print("\nRisk Analysis:")
    print(f"  Average Risk: {report.risk_analysis['average_risk']:.2f}")
    print(f"  Max Risk: {report.risk_analysis['max_risk']:.2f}")
    print(f"  High Risk Files: {report.risk_analysis.get('high_risk_files', [])}")
    
    # Access test selection details
    print("\nTest Selection:")
    print(f"  Total Tests: {report.test_selection['total_tests_selected']}")
    print(f"  Coverage Score: {report.test_selection['coverage_score']:.2%}")
    print(f"  Tests by Type: {report.test_selection.get('tests_by_type', {})}")


def example_ci_cd_integration():
    """Example: CI/CD pipeline integration pattern"""
    print("\n" + "=" * 80)
    print("EXAMPLE 6: CI/CD Integration")
    print("=" * 80)
    
    bot = SpeculatorBot(
        repo_path='.',
        test_catalog_path='examples/test_catalog.json',
        historical_data_path='examples/historical_failures.json'
    )
    
    report = bot.speculate()
    
    # Decision logic for CI/CD
    risk_score = report.deployment_risk_score
    
    if risk_score >= 0.8:
        print("❌ BLOCK DEPLOYMENT")
        print("   Reason: Critical risk detected")
        return 1  # Exit code 1 for CI/CD failure
    elif risk_score >= 0.6:
        print("⚠️ REQUIRE APPROVAL")
        print("   Reason: High risk - manual review needed")
        # Could trigger manual approval workflow
    else:
        print("✅ APPROVE DEPLOYMENT")
        print("   Reason: Risk acceptable")
    
    # Export report for artifact storage
    bot.export_report(report, 'output/ci_report.json', format='json')
    
    # Return appropriate exit code
    return 0 if risk_score < 0.6 else 2  # 2 for manual approval needed


def main():
    """Run all examples"""
    import os
    
    # Create output directory
    os.makedirs('output', exist_ok=True)
    
    try:
        # Run examples
        example_basic_analysis()
        example_specific_commit()
        example_custom_config()
        example_export_formats()
        example_access_detailed_results()
        example_ci_cd_integration()
        
        print("\n" + "=" * 80)
        print("✅ All examples completed successfully!")
        print("=" * 80)
        
    except Exception as e:
        print(f"\n❌ Error running examples: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()

