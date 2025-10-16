"""
Change Analyzer - Analyzes code and configuration changes
"""

import os
import ast
from typing import Dict, List, Set, Optional
from dataclasses import dataclass
from pathlib import Path
import logging

try:
    from git import Repo, Diff
    from radon.complexity import cc_visit
    from radon.metrics import mi_visit
except ImportError:
    pass

logger = logging.getLogger(__name__)


@dataclass
class ChangeMetrics:
    """Metrics for a code change"""
    file_path: str
    lines_added: int
    lines_removed: int
    complexity_delta: float
    maintainability_index: float
    functions_modified: List[str]
    is_critical_file: bool
    change_type: str  # 'code', 'config', 'database'


class ChangeAnalyzer:
    """Analyzes changes in code, configuration, and database files"""
    
    CRITICAL_PATTERNS = [
        'auth', 'security', 'payment', 'user', 'admin',
        'database', 'migration', 'config', 'core'
    ]
    
    def __init__(self, repo_path: str, config: Optional[Dict] = None):
        """
        Initialize the change analyzer
        
        Args:
            repo_path: Path to the git repository
            config: Configuration dictionary
        """
        self.repo_path = repo_path
        self.config = config or {}
        self.repo = None
        
        if os.path.exists(repo_path):
            try:
                self.repo = Repo(repo_path)
            except Exception as e:
                logger.warning(f"Failed to initialize git repo: {e}")
    
    def analyze_commit(self, commit_hash: Optional[str] = None) -> List[ChangeMetrics]:
        """
        Analyze changes in a specific commit or current staged changes
        
        Args:
            commit_hash: Specific commit to analyze, or None for staged changes
            
        Returns:
            List of ChangeMetrics for each changed file
        """
        if not self.repo:
            logger.error("Git repository not initialized")
            return []
        
        changes = []
        
        try:
            if commit_hash:
                commit = self.repo.commit(commit_hash)
                diffs = commit.diff(commit.parents[0] if commit.parents else None)
            else:
                # Analyze staged changes
                diffs = self.repo.index.diff('HEAD')
            
            for diff in diffs:
                metrics = self._analyze_diff(diff)
                if metrics:
                    changes.append(metrics)
                    
        except Exception as e:
            logger.error(f"Error analyzing commit: {e}")
        
        return changes
    
    def _analyze_diff(self, diff: 'Diff') -> Optional[ChangeMetrics]:
        """
        Analyze a single file diff
        
        Args:
            diff: Git diff object
            
        Returns:
            ChangeMetrics for the file or None
        """
        file_path = diff.b_path or diff.a_path
        if not file_path:
            return None
        
        # Determine change type
        change_type = self._get_change_type(file_path)
        
        # Calculate basic metrics
        lines_added = 0
        lines_removed = 0
        
        if diff.diff:
            diff_text = diff.diff.decode('utf-8', errors='ignore')
            for line in diff_text.split('\n'):
                if line.startswith('+') and not line.startswith('+++'):
                    lines_added += 1
                elif line.startswith('-') and not line.startswith('---'):
                    lines_removed += 1
        
        # Analyze code complexity for Python files
        complexity_delta = 0.0
        maintainability_index = 100.0
        functions_modified = []
        
        if file_path.endswith('.py') and change_type == 'code':
            try:
                full_path = os.path.join(self.repo_path, file_path)
                if os.path.exists(full_path):
                    with open(full_path, 'r', encoding='utf-8') as f:
                        code = f.read()
                    
                    # Calculate complexity
                    complexity_results = cc_visit(code)
                    complexity_delta = sum(c.complexity for c in complexity_results)
                    
                    # Calculate maintainability index
                    mi_results = mi_visit(code, multi=True)
                    maintainability_index = mi_results
                    
                    # Extract modified functions
                    functions_modified = [c.name for c in complexity_results]
                    
            except Exception as e:
                logger.debug(f"Could not analyze complexity for {file_path}: {e}")
        
        # Check if file is critical
        is_critical = self._is_critical_file(file_path)
        
        return ChangeMetrics(
            file_path=file_path,
            lines_added=lines_added,
            lines_removed=lines_removed,
            complexity_delta=complexity_delta,
            maintainability_index=maintainability_index,
            functions_modified=functions_modified,
            is_critical_file=is_critical,
            change_type=change_type
        )
    
    def _get_change_type(self, file_path: str) -> str:
        """Determine the type of change based on file extension"""
        path_lower = file_path.lower()
        
        if any(path_lower.endswith(ext) for ext in ['.sql', '.ddl']) or \
           any(pattern in path_lower for pattern in ['migration', 'schema']):
            return 'database'
        
        if any(path_lower.endswith(ext) for ext in ['.yaml', '.yml', '.json', '.xml', '.conf', '.ini']):
            return 'config'
        
        return 'code'
    
    def _is_critical_file(self, file_path: str) -> bool:
        """Determine if a file is critical based on path patterns"""
        path_lower = file_path.lower()
        return any(pattern in path_lower for pattern in self.CRITICAL_PATTERNS)
    
    def get_change_summary(self, changes: List[ChangeMetrics]) -> Dict:
        """
        Generate a summary of changes
        
        Args:
            changes: List of ChangeMetrics
            
        Returns:
            Summary dictionary
        """
        total_lines_added = sum(c.lines_added for c in changes)
        total_lines_removed = sum(c.lines_removed for c in changes)
        
        by_type = {
            'code': [c for c in changes if c.change_type == 'code'],
            'config': [c for c in changes if c.change_type == 'config'],
            'database': [c for c in changes if c.change_type == 'database']
        }
        
        critical_files = [c for c in changes if c.is_critical_file]
        
        avg_complexity = sum(c.complexity_delta for c in changes) / len(changes) if changes else 0
        
        return {
            'total_files_changed': len(changes),
            'total_lines_added': total_lines_added,
            'total_lines_removed': total_lines_removed,
            'changes_by_type': {k: len(v) for k, v in by_type.items()},
            'critical_files_changed': len(critical_files),
            'average_complexity': avg_complexity,
            'critical_files': [c.file_path for c in critical_files]
        }

