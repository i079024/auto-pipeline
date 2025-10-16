"""
Risk Analyzer - Predicts failure risk based on changes and historical data
"""

import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
import json
import os

import numpy as np
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.preprocessing import StandardScaler
import pandas as pd

from .change_analyzer import ChangeMetrics

logger = logging.getLogger(__name__)


@dataclass
class RiskScore:
    """Risk score for a change"""
    overall_risk: float  # 0-1 scale
    risk_level: str  # 'low', 'medium', 'high', 'critical'
    confidence: float  # 0-1 scale
    risk_factors: Dict[str, float]
    recommendations: List[str]
    predicted_failure_probability: float


@dataclass
class HistoricalFailure:
    """Historical failure data"""
    timestamp: datetime
    file_path: str
    failure_type: str
    severity: str
    resolution_time_hours: float
    related_commits: List[str]
    metadata: Dict


class RiskAnalyzer:
    """
    Analyzes changes and predicts failure risk using ML and historical data
    """
    
    def __init__(self, config: Optional[Dict] = None, model_path: Optional[str] = None):
        """
        Initialize the risk analyzer
        
        Args:
            config: Configuration dictionary
            model_path: Path to trained models
        """
        self.config = config or {}
        self.model_path = model_path or './models'
        self.scaler = StandardScaler()
        self.classifier = None
        self.historical_data: List[HistoricalFailure] = []
        
        # Feature weights from config
        self.feature_weights = self.config.get('feature_weights', {
            'code_complexity': 0.25,
            'historical_failures': 0.35,
            'change_magnitude': 0.20,
            'file_criticality': 0.20
        })
        
        # Risk thresholds
        risk_config = self.config.get('risk_analysis', {})
        self.thresholds = risk_config.get('risk_levels', {
            'high': 0.7,
            'medium': 0.4,
            'low': 0.2
        })
        
        self._initialize_model()
    
    def _initialize_model(self):
        """Initialize or load the ML model"""
        model_file = os.path.join(self.model_path, 'risk_model.pkl')
        
        if os.path.exists(model_file):
            try:
                import joblib
                self.classifier = joblib.load(model_file)
                logger.info("Loaded existing risk prediction model")
            except Exception as e:
                logger.warning(f"Could not load model: {e}. Using default model.")
                self.classifier = GradientBoostingClassifier(
                    n_estimators=100,
                    learning_rate=0.1,
                    max_depth=5,
                    random_state=42
                )
        else:
            # Initialize default model
            self.classifier = GradientBoostingClassifier(
                n_estimators=100,
                learning_rate=0.1,
                max_depth=5,
                random_state=42
            )
    
    def load_historical_data(self, data_source: str):
        """
        Load historical failure data
        
        Args:
            data_source: Path to historical data file or database connection
        """
        try:
            if os.path.exists(data_source):
                with open(data_source, 'r') as f:
                    data = json.load(f)
                
                for item in data:
                    failure = HistoricalFailure(
                        timestamp=datetime.fromisoformat(item['timestamp']),
                        file_path=item['file_path'],
                        failure_type=item['failure_type'],
                        severity=item['severity'],
                        resolution_time_hours=item['resolution_time_hours'],
                        related_commits=item.get('related_commits', []),
                        metadata=item.get('metadata', {})
                    )
                    self.historical_data.append(failure)
                
                logger.info(f"Loaded {len(self.historical_data)} historical failure records")
        except Exception as e:
            logger.error(f"Error loading historical data: {e}")
    
    def analyze_risk(self, changes: List[ChangeMetrics]) -> List[Tuple[ChangeMetrics, RiskScore]]:
        """
        Analyze risk for a list of changes
        
        Args:
            changes: List of ChangeMetrics
            
        Returns:
            List of tuples (ChangeMetrics, RiskScore)
        """
        results = []
        
        for change in changes:
            risk_score = self._calculate_risk(change)
            results.append((change, risk_score))
        
        return results
    
    def _calculate_risk(self, change: ChangeMetrics) -> RiskScore:
        """
        Calculate risk score for a single change
        
        Args:
            change: ChangeMetrics for the change
            
        Returns:
            RiskScore
        """
        # Extract features
        features = self._extract_features(change)
        
        # Calculate individual risk factors
        risk_factors = {
            'complexity_risk': self._calculate_complexity_risk(change),
            'historical_risk': self._calculate_historical_risk(change),
            'magnitude_risk': self._calculate_magnitude_risk(change),
            'criticality_risk': 1.0 if change.is_critical_file else 0.2
        }
        
        # Calculate weighted overall risk
        overall_risk = sum(
            risk_factors[f'{key}_risk'] * self.feature_weights.get(key, 0.25)
            for key in ['complexity', 'historical_failures', 'change_magnitude', 'file_criticality']
            if f'{key}_risk' in risk_factors
        )
        
        # Use ML model if trained and has sufficient historical data
        ml_prediction = 0.5  # default
        confidence = 0.6
        
        if self.classifier and len(self.historical_data) > 10:
            try:
                feature_vector = np.array([list(features.values())]).reshape(1, -1)
                ml_prediction = self.classifier.predict_proba(feature_vector)[0][1]
                
                # Blend rule-based and ML-based predictions
                overall_risk = 0.6 * overall_risk + 0.4 * ml_prediction
                confidence = 0.8
            except Exception as e:
                logger.debug(f"ML prediction failed: {e}")
        
        # Determine risk level
        risk_level = self._determine_risk_level(overall_risk)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(change, risk_factors, risk_level)
        
        return RiskScore(
            overall_risk=overall_risk,
            risk_level=risk_level,
            confidence=confidence,
            risk_factors=risk_factors,
            recommendations=recommendations,
            predicted_failure_probability=ml_prediction
        )
    
    def _extract_features(self, change: ChangeMetrics) -> Dict[str, float]:
        """Extract features for ML model"""
        return {
            'lines_added': change.lines_added,
            'lines_removed': change.lines_removed,
            'total_lines_changed': change.lines_added + change.lines_removed,
            'complexity': change.complexity_delta,
            'maintainability': change.maintainability_index,
            'is_critical': 1.0 if change.is_critical_file else 0.0,
            'functions_count': len(change.functions_modified),
            'is_database': 1.0 if change.change_type == 'database' else 0.0,
            'is_config': 1.0 if change.change_type == 'config' else 0.0
        }
    
    def _calculate_complexity_risk(self, change: ChangeMetrics) -> float:
        """Calculate risk based on code complexity"""
        if change.complexity_delta == 0:
            return 0.1
        
        # Normalize complexity (higher = riskier)
        complexity_score = min(change.complexity_delta / 20.0, 1.0)
        
        # Factor in maintainability index (lower = riskier)
        maintainability_score = 1.0 - (change.maintainability_index / 100.0)
        
        return (complexity_score * 0.6 + maintainability_score * 0.4)
    
    def _calculate_historical_risk(self, change: ChangeMetrics) -> float:
        """Calculate risk based on historical failures"""
        if not self.historical_data:
            return 0.3  # moderate risk when no history
        
        # Count failures in this file in the last 90 days
        cutoff_date = datetime.now() - timedelta(days=90)
        relevant_failures = [
            f for f in self.historical_data
            if f.file_path == change.file_path and f.timestamp > cutoff_date
        ]
        
        if not relevant_failures:
            return 0.1
        
        # Calculate risk based on failure frequency and severity
        failure_count = len(relevant_failures)
        high_severity_count = sum(1 for f in relevant_failures if f.severity == 'high')
        
        frequency_risk = min(failure_count / 10.0, 1.0)
        severity_risk = high_severity_count / max(failure_count, 1)
        
        return 0.7 * frequency_risk + 0.3 * severity_risk
    
    def _calculate_magnitude_risk(self, change: ChangeMetrics) -> float:
        """Calculate risk based on change magnitude"""
        total_lines = change.lines_added + change.lines_removed
        
        # Normalize (larger changes = riskier)
        magnitude_score = min(total_lines / 500.0, 1.0)
        
        # Database and config changes are inherently riskier
        if change.change_type == 'database':
            magnitude_score *= 1.5
        elif change.change_type == 'config':
            magnitude_score *= 1.3
        
        return min(magnitude_score, 1.0)
    
    def _determine_risk_level(self, risk_score: float) -> str:
        """Determine risk level from score"""
        if risk_score >= self.thresholds['high']:
            return 'high'
        elif risk_score >= self.thresholds['medium']:
            return 'medium'
        elif risk_score >= self.thresholds['low']:
            return 'low'
        else:
            return 'minimal'
    
    def _generate_recommendations(
        self,
        change: ChangeMetrics,
        risk_factors: Dict[str, float],
        risk_level: str
    ) -> List[str]:
        """Generate recommendations based on risk analysis"""
        recommendations = []
        
        if risk_level in ['high', 'critical']:
            recommendations.append("⚠️ High-risk change detected. Consider thorough code review.")
            recommendations.append("Run full test suite before deployment.")
        
        if risk_factors['complexity_risk'] > 0.6:
            recommendations.append("High complexity detected. Consider refactoring for maintainability.")
        
        if risk_factors['historical_risk'] > 0.7:
            recommendations.append("This file has a history of failures. Extra scrutiny recommended.")
        
        if change.is_critical_file:
            recommendations.append("Critical file modified. Ensure comprehensive testing.")
        
        if change.change_type == 'database':
            recommendations.append("Database change detected. Test rollback procedures.")
            recommendations.append("Verify schema compatibility and data migration.")
        
        if change.change_type == 'config':
            recommendations.append("Configuration change. Test in staging environment first.")
        
        if risk_factors['magnitude_risk'] > 0.7:
            recommendations.append("Large change detected. Consider breaking into smaller commits.")
        
        if change.maintainability_index < 50:
            recommendations.append("Low maintainability index. Code may be difficult to maintain.")
        
        if not recommendations:
            recommendations.append("✓ Change appears low-risk. Standard review process recommended.")
        
        return recommendations
    
    def train_model(self, training_data: pd.DataFrame, labels: np.ndarray):
        """
        Train the risk prediction model with historical data
        
        Args:
            training_data: DataFrame with features
            labels: Array of binary labels (0=no failure, 1=failure)
        """
        try:
            # Scale features
            X_scaled = self.scaler.fit_transform(training_data)
            
            # Train model
            self.classifier.fit(X_scaled, labels)
            
            logger.info(f"Model trained with {len(training_data)} samples")
            
            # Save model
            os.makedirs(self.model_path, exist_ok=True)
            import joblib
            joblib.dump(self.classifier, os.path.join(self.model_path, 'risk_model.pkl'))
            joblib.dump(self.scaler, os.path.join(self.model_path, 'scaler.pkl'))
            
        except Exception as e:
            logger.error(f"Error training model: {e}")
    
    def get_risk_summary(self, risk_results: List[Tuple[ChangeMetrics, RiskScore]]) -> Dict:
        """
        Generate a summary of risk analysis
        
        Args:
            risk_results: List of (ChangeMetrics, RiskScore) tuples
            
        Returns:
            Summary dictionary
        """
        if not risk_results:
            return {'error': 'No results to summarize'}
        
        overall_risks = [score.overall_risk for _, score in risk_results]
        risk_levels = [score.risk_level for _, score in risk_results]
        
        return {
            'total_changes': len(risk_results),
            'average_risk': np.mean(overall_risks),
            'max_risk': np.max(overall_risks),
            'risk_distribution': {
                'high': risk_levels.count('high'),
                'medium': risk_levels.count('medium'),
                'low': risk_levels.count('low'),
                'minimal': risk_levels.count('minimal')
            },
            'high_risk_files': [
                change.file_path for change, score in risk_results
                if score.risk_level == 'high'
            ],
            'deployment_recommendation': self._get_deployment_recommendation(overall_risks)
        }
    
    def _get_deployment_recommendation(self, risks: List[float]) -> str:
        """Generate deployment recommendation based on risks"""
        avg_risk = np.mean(risks)
        max_risk = np.max(risks)
        
        if max_risk > 0.8:
            return "⛔ HALT - Critical risk detected. Do not deploy until addressed."
        elif avg_risk > 0.6:
            return "⚠️ CAUTION - High average risk. Thorough testing required."
        elif max_risk > 0.6:
            return "⚠️ REVIEW - Some high-risk changes. Focus testing on flagged areas."
        elif avg_risk > 0.4:
            return "✓ PROCEED WITH CARE - Moderate risk. Standard testing recommended."
        else:
            return "✓ PROCEED - Low risk. Standard deployment process."

