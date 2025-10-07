"""Core business logic for evaluation system."""

from .aggregator import aggregate_issues
from .analyzer import analyze_patterns
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
from .scoring import SEVERITY_MULTIPLIERS, calculate_quality_score
