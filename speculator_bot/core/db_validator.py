"""
Database Validator - Analyzes schema changes and detects data drift
"""

import logging
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from datetime import datetime, timedelta
from collections import defaultdict
import json
import re

import numpy as np
import pandas as pd
from scipy import stats

logger = logging.getLogger(__name__)


@dataclass
class SchemaChange:
    """Represents a database schema change"""
    change_type: str  # 'add_table', 'drop_table', 'add_column', 'drop_column', 'modify_column', 'add_index'
    table_name: str
    column_name: Optional[str] = None
    old_definition: Optional[str] = None
    new_definition: Optional[str] = None
    impact_level: str = 'medium'  # 'low', 'medium', 'high', 'critical'


@dataclass
class DataDriftReport:
    """Report on data drift detection"""
    table_name: str
    column_name: str
    drift_detected: bool
    drift_score: float  # 0-1 scale
    drift_type: str  # 'distribution', 'missing_values', 'range', 'categorical'
    baseline_stats: Dict[str, Any]
    current_stats: Dict[str, Any]
    recommendation: str


@dataclass
class QueryPerformanceImpact:
    """Predicted impact on query performance"""
    query_pattern: str
    tables_affected: List[str]
    estimated_impact: str  # 'positive', 'negative', 'neutral'
    impact_percentage: float
    recommendation: str


class DatabaseValidator:
    """
    Validates database changes and detects data drift
    """
    
    # SQL patterns for schema analysis
    CREATE_TABLE_PATTERN = r'CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?(\w+)'
    DROP_TABLE_PATTERN = r'DROP\s+TABLE\s+(?:IF\s+EXISTS\s+)?(\w+)'
    ALTER_TABLE_PATTERN = r'ALTER\s+TABLE\s+(\w+)\s+(ADD|DROP|MODIFY|ALTER)\s+(?:COLUMN\s+)?(\w+)?'
    CREATE_INDEX_PATTERN = r'CREATE\s+(?:UNIQUE\s+)?INDEX\s+(\w+)\s+ON\s+(\w+)'
    
    def __init__(self, config: Optional[Dict] = None, db_connection: Optional[Any] = None):
        """
        Initialize the database validator
        
        Args:
            config: Configuration dictionary
            db_connection: Database connection object (SQLAlchemy engine)
        """
        self.config = config or {}
        self.db_connection = db_connection
        
        # Configuration
        db_config = self.config.get('database_validation', {})
        self.drift_threshold = db_config.get('drift_threshold', 0.15)
        self.sample_size = db_config.get('sample_size', 1000)
        
        # Baseline data statistics
        self.baseline_stats: Dict[str, Dict[str, Dict]] = {}  # table -> column -> stats
    
    def analyze_schema_changes(self, sql_content: str) -> List[SchemaChange]:
        """
        Analyze SQL schema changes
        
        Args:
            sql_content: SQL migration or schema definition content
            
        Returns:
            List of SchemaChange objects
        """
        changes = []
        
        # Detect CREATE TABLE
        for match in re.finditer(self.CREATE_TABLE_PATTERN, sql_content, re.IGNORECASE):
            table_name = match.group(1)
            changes.append(SchemaChange(
                change_type='add_table',
                table_name=table_name,
                impact_level='high'
            ))
        
        # Detect DROP TABLE
        for match in re.finditer(self.DROP_TABLE_PATTERN, sql_content, re.IGNORECASE):
            table_name = match.group(1)
            changes.append(SchemaChange(
                change_type='drop_table',
                table_name=table_name,
                impact_level='critical'
            ))
        
        # Detect ALTER TABLE
        for match in re.finditer(self.ALTER_TABLE_PATTERN, sql_content, re.IGNORECASE):
            table_name = match.group(1)
            operation = match.group(2).upper()
            column_name = match.group(3) if match.group(3) else None
            
            change_type_map = {
                'ADD': 'add_column',
                'DROP': 'drop_column',
                'MODIFY': 'modify_column',
                'ALTER': 'modify_column'
            }
            
            impact_map = {
                'ADD': 'low',
                'DROP': 'critical',
                'MODIFY': 'high',
                'ALTER': 'high'
            }
            
            changes.append(SchemaChange(
                change_type=change_type_map.get(operation, 'modify_column'),
                table_name=table_name,
                column_name=column_name,
                impact_level=impact_map.get(operation, 'medium')
            ))
        
        # Detect CREATE INDEX
        for match in re.finditer(self.CREATE_INDEX_PATTERN, sql_content, re.IGNORECASE):
            index_name = match.group(1)
            table_name = match.group(2)
            changes.append(SchemaChange(
                change_type='add_index',
                table_name=table_name,
                column_name=index_name,
                impact_level='medium'
            ))
        
        return changes
    
    def predict_query_impact(
        self,
        schema_changes: List[SchemaChange],
        query_patterns: Optional[List[str]] = None
    ) -> List[QueryPerformanceImpact]:
        """
        Predict how schema changes will impact query performance
        
        Args:
            schema_changes: List of schema changes
            query_patterns: Optional list of query patterns to analyze
            
        Returns:
            List of QueryPerformanceImpact predictions
        """
        impacts = []
        
        for change in schema_changes:
            if change.change_type == 'add_index':
                impacts.append(QueryPerformanceImpact(
                    query_pattern=f"SELECT with WHERE on {change.table_name}",
                    tables_affected=[change.table_name],
                    estimated_impact='positive',
                    impact_percentage=30.0,
                    recommendation=f"Index on {change.column_name} should improve query performance"
                ))
            
            elif change.change_type == 'drop_column':
                impacts.append(QueryPerformanceImpact(
                    query_pattern=f"SELECT * FROM {change.table_name}",
                    tables_affected=[change.table_name],
                    estimated_impact='positive',
                    impact_percentage=5.0,
                    recommendation=f"Removing column may slightly improve table scan performance"
                ))
            
            elif change.change_type == 'add_column':
                impacts.append(QueryPerformanceImpact(
                    query_pattern=f"INSERT INTO {change.table_name}",
                    tables_affected=[change.table_name],
                    estimated_impact='negative',
                    impact_percentage=-5.0,
                    recommendation=f"Adding column may slightly slow down inserts. Consider default values."
                ))
            
            elif change.change_type == 'drop_table':
                impacts.append(QueryPerformanceImpact(
                    query_pattern=f"Any query on {change.table_name}",
                    tables_affected=[change.table_name],
                    estimated_impact='negative',
                    impact_percentage=-100.0,
                    recommendation=f"⚠️ CRITICAL: Dropping table will break queries. Ensure no dependencies."
                ))
            
            elif change.change_type == 'modify_column':
                impacts.append(QueryPerformanceImpact(
                    query_pattern=f"Queries using {change.table_name}.{change.column_name}",
                    tables_affected=[change.table_name],
                    estimated_impact='neutral',
                    impact_percentage=0.0,
                    recommendation=f"Column modification may affect queries. Verify data type compatibility."
                ))
        
        return impacts
    
    def capture_baseline_stats(self, table_name: str, columns: Optional[List[str]] = None):
        """
        Capture baseline statistics for a table
        
        Args:
            table_name: Name of the table
            columns: Optional list of specific columns to analyze
        """
        if not self.db_connection:
            logger.warning("No database connection available for baseline capture")
            return
        
        try:
            # Sample data from table
            query = f"SELECT * FROM {table_name} LIMIT {self.sample_size}"
            df = pd.read_sql(query, self.db_connection)
            
            if df.empty:
                logger.warning(f"Table {table_name} is empty")
                return
            
            # Calculate statistics for each column
            self.baseline_stats[table_name] = {}
            
            for column in (columns or df.columns):
                if column not in df.columns:
                    continue
                
                col_data = df[column]
                stats_dict = {
                    'timestamp': datetime.now().isoformat(),
                    'sample_size': len(col_data),
                    'missing_count': col_data.isna().sum(),
                    'missing_percentage': col_data.isna().sum() / len(col_data) * 100
                }
                
                # Numeric columns
                if pd.api.types.is_numeric_dtype(col_data):
                    stats_dict.update({
                        'type': 'numeric',
                        'mean': float(col_data.mean()),
                        'std': float(col_data.std()),
                        'min': float(col_data.min()),
                        'max': float(col_data.max()),
                        'median': float(col_data.median()),
                        'q25': float(col_data.quantile(0.25)),
                        'q75': float(col_data.quantile(0.75))
                    })
                
                # Categorical columns
                elif pd.api.types.is_string_dtype(col_data) or pd.api.types.is_object_dtype(col_data):
                    value_counts = col_data.value_counts()
                    stats_dict.update({
                        'type': 'categorical',
                        'unique_count': col_data.nunique(),
                        'top_values': value_counts.head(10).to_dict(),
                        'cardinality': col_data.nunique() / len(col_data)
                    })
                
                # Datetime columns
                elif pd.api.types.is_datetime64_any_dtype(col_data):
                    stats_dict.update({
                        'type': 'datetime',
                        'min_date': str(col_data.min()),
                        'max_date': str(col_data.max()),
                        'date_range_days': (col_data.max() - col_data.min()).days
                    })
                
                self.baseline_stats[table_name][column] = stats_dict
            
            logger.info(f"Captured baseline stats for {table_name}: {len(self.baseline_stats[table_name])} columns")
            
        except Exception as e:
            logger.error(f"Error capturing baseline stats for {table_name}: {e}")
    
    def detect_data_drift(
        self,
        table_name: str,
        columns: Optional[List[str]] = None
    ) -> List[DataDriftReport]:
        """
        Detect data drift by comparing current data to baseline
        
        Args:
            table_name: Name of the table
            columns: Optional list of specific columns to check
            
        Returns:
            List of DataDriftReport objects
        """
        if not self.db_connection:
            logger.warning("No database connection available for drift detection")
            return []
        
        if table_name not in self.baseline_stats:
            logger.warning(f"No baseline stats available for {table_name}")
            return []
        
        drift_reports = []
        
        try:
            # Sample current data
            query = f"SELECT * FROM {table_name} LIMIT {self.sample_size}"
            df = pd.read_sql(query, self.db_connection)
            
            for column in (columns or self.baseline_stats[table_name].keys()):
                if column not in df.columns:
                    continue
                
                baseline = self.baseline_stats[table_name][column]
                drift_report = self._analyze_column_drift(table_name, column, df[column], baseline)
                
                if drift_report:
                    drift_reports.append(drift_report)
            
        except Exception as e:
            logger.error(f"Error detecting drift for {table_name}: {e}")
        
        return drift_reports
    
    def _analyze_column_drift(
        self,
        table_name: str,
        column_name: str,
        current_data: pd.Series,
        baseline: Dict
    ) -> Optional[DataDriftReport]:
        """
        Analyze drift for a single column
        
        Args:
            table_name: Table name
            column_name: Column name
            current_data: Current column data
            baseline: Baseline statistics
            
        Returns:
            DataDriftReport if drift detected, None otherwise
        """
        current_stats = {}
        drift_score = 0.0
        drift_type = 'none'
        drift_detected = False
        recommendation = ""
        
        # Missing values drift
        current_missing_pct = current_data.isna().sum() / len(current_data) * 100
        baseline_missing_pct = baseline['missing_percentage']
        missing_drift = abs(current_missing_pct - baseline_missing_pct)
        
        if missing_drift > 10.0:  # More than 10% change in missing values
            drift_detected = True
            drift_type = 'missing_values'
            drift_score = max(drift_score, min(missing_drift / 50.0, 1.0))
            recommendation = f"Missing value rate changed by {missing_drift:.1f}%"
        
        current_stats['missing_percentage'] = current_missing_pct
        
        # Numeric column drift
        if baseline.get('type') == 'numeric' and pd.api.types.is_numeric_dtype(current_data):
            current_mean = float(current_data.mean())
            current_std = float(current_data.std())
            
            current_stats.update({
                'mean': current_mean,
                'std': current_std,
                'min': float(current_data.min()),
                'max': float(current_data.max())
            })
            
            # Distribution drift using Kolmogorov-Smirnov test
            # (In production, you'd compare with actual baseline data)
            mean_change = abs(current_mean - baseline['mean']) / (baseline['mean'] + 1e-10)
            std_change = abs(current_std - baseline['std']) / (baseline['std'] + 1e-10)
            
            if mean_change > self.drift_threshold:
                drift_detected = True
                drift_type = 'distribution'
                drift_score = max(drift_score, min(mean_change, 1.0))
                recommendation = f"Mean shifted by {mean_change*100:.1f}%"
            
            if std_change > self.drift_threshold:
                drift_detected = True
                drift_type = 'distribution'
                drift_score = max(drift_score, min(std_change, 1.0))
                recommendation += f" Std deviation changed by {std_change*100:.1f}%"
            
            # Range drift
            current_range = current_data.max() - current_data.min()
            baseline_range = baseline['max'] - baseline['min']
            range_change = abs(current_range - baseline_range) / (baseline_range + 1e-10)
            
            if range_change > 0.5:  # 50% change in range
                drift_detected = True
                drift_type = 'range'
                drift_score = max(drift_score, min(range_change, 1.0))
                recommendation += f" Data range changed significantly"
        
        # Categorical column drift
        elif baseline.get('type') == 'categorical':
            current_unique = current_data.nunique()
            baseline_unique = baseline['unique_count']
            
            current_stats['unique_count'] = current_unique
            current_stats['cardinality'] = current_unique / len(current_data)
            
            cardinality_change = abs(current_unique - baseline_unique) / (baseline_unique + 1e-10)
            
            if cardinality_change > self.drift_threshold:
                drift_detected = True
                drift_type = 'categorical'
                drift_score = max(drift_score, min(cardinality_change, 1.0))
                recommendation = f"Number of unique values changed by {cardinality_change*100:.1f}%"
            
            # Check if top values changed
            current_top = current_data.value_counts().head(5).index.tolist()
            baseline_top = list(baseline.get('top_values', {}).keys())[:5]
            
            overlap = len(set(current_top) & set(baseline_top))
            if overlap < 3:  # Less than 3 common values in top 5
                drift_detected = True
                drift_type = 'categorical'
                drift_score = max(drift_score, 0.7)
                recommendation += " Top categories have changed"
        
        if not drift_detected:
            return None
        
        if not recommendation:
            recommendation = "Data distribution has changed"
        
        return DataDriftReport(
            table_name=table_name,
            column_name=column_name,
            drift_detected=drift_detected,
            drift_score=drift_score,
            drift_type=drift_type,
            baseline_stats=baseline,
            current_stats=current_stats,
            recommendation=recommendation
        )
    
    def get_schema_impact_summary(
        self,
        schema_changes: List[SchemaChange],
        query_impacts: List[QueryPerformanceImpact]
    ) -> Dict:
        """
        Generate summary of schema changes and their impact
        
        Args:
            schema_changes: List of schema changes
            query_impacts: List of query performance impacts
            
        Returns:
            Summary dictionary
        """
        by_type = defaultdict(int)
        by_impact = defaultdict(int)
        
        for change in schema_changes:
            by_type[change.change_type] += 1
            by_impact[change.impact_level] += 1
        
        has_critical = any(c.impact_level == 'critical' for c in schema_changes)
        has_high = any(c.impact_level == 'high' for c in schema_changes)
        
        if has_critical:
            risk_level = "CRITICAL"
            recommendation = "⛔ Review required before deployment. Breaking changes detected."
        elif has_high:
            risk_level = "HIGH"
            recommendation = "⚠️ Careful review recommended. Significant schema changes."
        else:
            risk_level = "MODERATE"
            recommendation = "✓ Schema changes appear manageable. Standard review process."
        
        return {
            'total_changes': len(schema_changes),
            'changes_by_type': dict(by_type),
            'changes_by_impact': dict(by_impact),
            'risk_level': risk_level,
            'affected_tables': list(set(c.table_name for c in schema_changes)),
            'query_impacts': len(query_impacts),
            'recommendation': recommendation
        }
    
    def get_drift_summary(self, drift_reports: List[DataDriftReport]) -> Dict:
        """
        Generate summary of data drift detection
        
        Args:
            drift_reports: List of drift reports
            
        Returns:
            Summary dictionary
        """
        if not drift_reports:
            return {
                'message': 'No data drift detected',
                'recommendation': '✓ Data quality appears stable'
            }
        
        by_type = defaultdict(int)
        high_drift = []
        
        for report in drift_reports:
            by_type[report.drift_type] += 1
            if report.drift_score > 0.5:
                high_drift.append(f"{report.table_name}.{report.column_name}")
        
        avg_drift_score = np.mean([r.drift_score for r in drift_reports])
        
        if avg_drift_score > 0.7:
            recommendation = "⛔ Significant data drift detected. Investigate before deployment."
        elif avg_drift_score > 0.4:
            recommendation = "⚠️ Moderate data drift. Review data quality."
        else:
            recommendation = "⚠️ Minor data drift detected. Monitor closely."
        
        return {
            'drift_detected_columns': len(drift_reports),
            'average_drift_score': avg_drift_score,
            'drift_by_type': dict(by_type),
            'high_drift_columns': high_drift,
            'recommendation': recommendation
        }

