"""
Test Selector - Intelligently selects tests based on risk analysis
"""

import logging
from typing import Dict, List, Set, Optional, Tuple
from dataclasses import dataclass
import json
import os
from collections import defaultdict

from .change_analyzer import ChangeMetrics
from .risk_analyzer import RiskScore

logger = logging.getLogger(__name__)


@dataclass
class TestCase:
    """Represents a test case"""
    test_id: str
    test_name: str
    test_path: str
    test_type: str  # 'unit', 'integration', 'e2e', 'performance'
    execution_time_seconds: float
    covered_files: List[str]
    criticality: str  # 'critical', 'high', 'medium', 'low'
    last_failure_date: Optional[str] = None
    failure_count: int = 0
    dependencies: List[str] = None


@dataclass
class TestSelection:
    """Results of test selection"""
    selected_tests: List[TestCase]
    reason_map: Dict[str, str]  # test_id -> reason for selection
    total_estimated_time: float
    coverage_score: float
    risk_coverage: Dict[str, List[str]]  # file -> tests covering it


class TestSelector:
    """
    Intelligently selects and prioritizes tests based on risk analysis
    """
    
    def __init__(self, config: Optional[Dict] = None, test_catalog_path: Optional[str] = None):
        """
        Initialize the test selector
        
        Args:
            config: Configuration dictionary
            test_catalog_path: Path to test catalog file
        """
        self.config = config or {}
        self.test_catalog_path = test_catalog_path
        self.test_catalog: List[TestCase] = []
        self.coverage_map: Dict[str, List[TestCase]] = defaultdict(list)
        
        # Configuration
        test_config = self.config.get('test_selection', {})
        self.max_tests = test_config.get('max_tests', 50)
        self.min_confidence = self.config.get('risk_analysis', {}).get('min_confidence_threshold', 0.6)
        self.prioritize_by_risk = test_config.get('prioritize_by_risk', True)
        self.include_critical = test_config.get('include_critical_tests', True)
        
        if test_catalog_path and os.path.exists(test_catalog_path):
            self.load_test_catalog(test_catalog_path)
    
    def load_test_catalog(self, catalog_path: str):
        """
        Load test catalog from file
        
        Args:
            catalog_path: Path to test catalog JSON file
        """
        try:
            with open(catalog_path, 'r') as f:
                data = json.load(f)
            
            for item in data:
                test = TestCase(
                    test_id=item['test_id'],
                    test_name=item['test_name'],
                    test_path=item['test_path'],
                    test_type=item['test_type'],
                    execution_time_seconds=item['execution_time_seconds'],
                    covered_files=item['covered_files'],
                    criticality=item.get('criticality', 'medium'),
                    last_failure_date=item.get('last_failure_date'),
                    failure_count=item.get('failure_count', 0),
                    dependencies=item.get('dependencies', [])
                )
                self.test_catalog.append(test)
                
                # Build coverage map
                for file_path in test.covered_files:
                    self.coverage_map[file_path].append(test)
            
            logger.info(f"Loaded {len(self.test_catalog)} tests from catalog")
        except Exception as e:
            logger.error(f"Error loading test catalog: {e}")
    
    def select_tests(
        self,
        risk_results: List[Tuple[ChangeMetrics, RiskScore]]
    ) -> TestSelection:
        """
        Select tests based on risk analysis
        
        Args:
            risk_results: List of (ChangeMetrics, RiskScore) tuples
            
        Returns:
            TestSelection with selected tests and metadata
        """
        if not self.test_catalog:
            logger.warning("No test catalog loaded. Cannot select tests.")
            return TestSelection(
                selected_tests=[],
                reason_map={},
                total_estimated_time=0.0,
                coverage_score=0.0,
                risk_coverage={}
            )
        
        # Track selected tests and reasons
        selected: Dict[str, Tuple[TestCase, str, float]] = {}  # test_id -> (test, reason, priority)
        
        # Step 1: Always include critical tests
        if self.include_critical:
            for test in self.test_catalog:
                if test.criticality == 'critical':
                    selected[test.test_id] = (
                        test,
                        "Critical test - always included",
                        1.0
                    )
        
        # Step 2: Select tests for changed files
        for change, risk_score in risk_results:
            file_tests = self.coverage_map.get(change.file_path, [])
            
            for test in file_tests:
                priority = self._calculate_test_priority(test, change, risk_score)
                
                if test.test_id not in selected or priority > selected[test.test_id][2]:
                    reason = self._generate_selection_reason(test, change, risk_score)
                    selected[test.test_id] = (test, reason, priority)
        
        # Step 3: Add tests for historically problematic areas
        for change, risk_score in risk_results:
            if risk_score.risk_factors.get('historical_risk', 0) > 0.7:
                # Find related tests
                related_tests = self._find_related_tests(change.file_path)
                for test in related_tests:
                    if test.test_id not in selected:
                        selected[test.test_id] = (
                            test,
                            f"Historical failures in {change.file_path}",
                            0.8
                        )
        
        # Step 4: Sort by priority and limit
        sorted_tests = sorted(
            selected.values(),
            key=lambda x: x[2],
            reverse=True
        )[:self.max_tests]
        
        # Step 5: Add dependencies
        final_tests = self._add_dependencies(sorted_tests)
        
        # Build result
        test_list = [t[0] for t in final_tests]
        reason_map = {t[0].test_id: t[1] for t in final_tests}
        
        # Calculate metrics
        total_time = sum(t.execution_time_seconds for t in test_list)
        coverage_score = self._calculate_coverage_score(test_list, risk_results)
        risk_coverage = self._build_risk_coverage_map(test_list, risk_results)
        
        return TestSelection(
            selected_tests=test_list,
            reason_map=reason_map,
            total_estimated_time=total_time,
            coverage_score=coverage_score,
            risk_coverage=risk_coverage
        )
    
    def _calculate_test_priority(
        self,
        test: TestCase,
        change: ChangeMetrics,
        risk_score: RiskScore
    ) -> float:
        """
        Calculate priority score for a test
        
        Args:
            test: TestCase to score
            change: ChangeMetrics for the file
            risk_score: RiskScore for the change
            
        Returns:
            Priority score (0-1)
        """
        priority = 0.0
        
        # Factor 1: Risk level of changed file
        priority += risk_score.overall_risk * 0.4
        
        # Factor 2: Test criticality
        criticality_weights = {
            'critical': 1.0,
            'high': 0.8,
            'medium': 0.5,
            'low': 0.3
        }
        priority += criticality_weights.get(test.criticality, 0.5) * 0.3
        
        # Factor 3: Historical failure rate
        if test.failure_count > 0:
            failure_score = min(test.failure_count / 10.0, 1.0)
            priority += failure_score * 0.2
        
        # Factor 4: Test type (prefer faster tests for similar coverage)
        type_weights = {
            'unit': 0.9,
            'integration': 0.7,
            'e2e': 0.5,
            'performance': 0.6
        }
        priority += type_weights.get(test.test_type, 0.5) * 0.1
        
        return min(priority, 1.0)
    
    def _generate_selection_reason(
        self,
        test: TestCase,
        change: ChangeMetrics,
        risk_score: RiskScore
    ) -> str:
        """Generate human-readable reason for test selection"""
        reasons = []
        
        if risk_score.risk_level in ['high', 'critical']:
            reasons.append(f"{risk_score.risk_level.upper()} risk in {change.file_path}")
        
        if change.is_critical_file:
            reasons.append("covers critical file")
        
        if test.failure_count > 3:
            reasons.append(f"historically unstable ({test.failure_count} failures)")
        
        if change.change_type == 'database' and 'database' in test.test_path.lower():
            reasons.append("database change detected")
        
        if not reasons:
            reasons.append(f"covers modified file {change.file_path}")
        
        return "; ".join(reasons)
    
    def _find_related_tests(self, file_path: str) -> List[TestCase]:
        """Find tests related to a file path"""
        related = []
        
        # Direct coverage
        related.extend(self.coverage_map.get(file_path, []))
        
        # Tests in same directory
        dir_path = os.path.dirname(file_path)
        for test in self.test_catalog:
            if dir_path in test.test_path:
                related.append(test)
        
        # Remove duplicates
        seen = set()
        unique_related = []
        for test in related:
            if test.test_id not in seen:
                seen.add(test.test_id)
                unique_related.append(test)
        
        return unique_related
    
    def _add_dependencies(
        self,
        tests: List[Tuple[TestCase, str, float]]
    ) -> List[Tuple[TestCase, str, float]]:
        """Add test dependencies to selection"""
        result = list(tests)
        added_ids = {t[0].test_id for t in tests}
        
        for test, reason, priority in tests:
            if test.dependencies:
                for dep_id in test.dependencies:
                    if dep_id not in added_ids:
                        dep_test = next((t for t in self.test_catalog if t.test_id == dep_id), None)
                        if dep_test:
                            result.append((
                                dep_test,
                                f"Dependency of {test.test_name}",
                                priority * 0.8
                            ))
                            added_ids.add(dep_id)
        
        return result
    
    def _calculate_coverage_score(
        self,
        selected_tests: List[TestCase],
        risk_results: List[Tuple[ChangeMetrics, RiskScore]]
    ) -> float:
        """Calculate how well selected tests cover the changed files"""
        if not risk_results:
            return 1.0
        
        covered_files = set()
        for test in selected_tests:
            covered_files.update(test.covered_files)
        
        changed_files = {change.file_path for change, _ in risk_results}
        
        if not changed_files:
            return 1.0
        
        coverage = len(covered_files & changed_files) / len(changed_files)
        return coverage
    
    def _build_risk_coverage_map(
        self,
        selected_tests: List[TestCase],
        risk_results: List[Tuple[ChangeMetrics, RiskScore]]
    ) -> Dict[str, List[str]]:
        """Build a map of which files are covered by which tests"""
        coverage_map = defaultdict(list)
        
        changed_files = {change.file_path for change, _ in risk_results}
        
        for test in selected_tests:
            for file_path in test.covered_files:
                if file_path in changed_files:
                    coverage_map[file_path].append(test.test_name)
        
        return dict(coverage_map)
    
    def get_selection_summary(self, selection: TestSelection) -> Dict:
        """
        Generate a summary of test selection
        
        Args:
            selection: TestSelection object
            
        Returns:
            Summary dictionary
        """
        if not selection.selected_tests:
            return {'message': 'No tests selected'}
        
        by_type = defaultdict(int)
        by_criticality = defaultdict(int)
        
        for test in selection.selected_tests:
            by_type[test.test_type] += 1
            by_criticality[test.criticality] += 1
        
        return {
            'total_tests_selected': len(selection.selected_tests),
            'estimated_execution_time_minutes': selection.total_estimated_time / 60,
            'coverage_score': selection.coverage_score,
            'tests_by_type': dict(by_type),
            'tests_by_criticality': dict(by_criticality),
            'files_with_coverage': len(selection.risk_coverage),
            'recommendation': self._get_test_recommendation(selection)
        }
    
    def _get_test_recommendation(self, selection: TestSelection) -> str:
        """Generate recommendation based on test selection"""
        if selection.coverage_score >= 0.9:
            return "✓ Excellent test coverage for changed files."
        elif selection.coverage_score >= 0.7:
            return "✓ Good test coverage. Consider adding tests for uncovered files."
        elif selection.coverage_score >= 0.5:
            return "⚠️ Moderate coverage. Some changed files lack test coverage."
        else:
            return "⚠️ Low test coverage. Many changed files are not covered by tests."

