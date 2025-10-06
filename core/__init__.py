"""Core business logic for evaluation system."""

from .aggregator import IssueAggregator
from .analyzer import ErrorPatternAnalyzer
from .evaluator import Evaluator
from .models import (
    ErrorPattern,
    EvaluationMetadata,
    EvaluationResult,
    Issue,
    IssueBreakdown,
    PatternExample,
    PenaltyBreakdown,
    Scores,
)
from .scoring import SEVERITY_MULTIPLIERS, calculate_quality_score, classify_score
