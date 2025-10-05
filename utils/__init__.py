"""Core services for the language evaluation CLI."""

from models import (
    ErrorPattern,
    EvaluationMetadata,
    EvaluationResult,
    Issue,
    IssueBreakdown,
    PenaltyBreakdown,
    Scores,
)

from .cleaner import DirectoryCleaner
from .error_patterns import ErrorPatternAnalyzer
from .evaluator import QuizEvaluator, SimpleScorer
from .issues import IssueAggregator
from .servers import serve_dashboard
from .static_export import StaticExporter

__all__ = [
    "DirectoryCleaner",
    "SimpleScorer",
    "QuizEvaluator",
    "IssueAggregator",
    "ErrorPatternAnalyzer",
    "serve_dashboard",
    "StaticExporter",
    # Models
    "Issue",
    "EvaluationMetadata",
    "EvaluationResult",
    "Scores",
    "IssueBreakdown",
    "PenaltyBreakdown",
    "ErrorPattern",
]
