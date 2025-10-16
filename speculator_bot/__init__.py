"""
Speculator Bot - AI-Assisted Predictive Analysis Tool

A sophisticated tool for predictive quality assurance and risk assessment.
"""

__version__ = "1.0.0"
__author__ = "Speculator Bot Team"

from .core.risk_analyzer import RiskAnalyzer
from .core.test_selector import TestSelector
from .core.db_validator import DatabaseValidator
from .core.change_analyzer import ChangeAnalyzer

__all__ = [
    "RiskAnalyzer",
    "TestSelector",
    "DatabaseValidator",
    "ChangeAnalyzer",
]

