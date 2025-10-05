"""Data models for evaluation system."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass(frozen=True)
class Issue:
    """Represents a single evaluation issue."""

    category: str
    subcategory: str
    original: str
    correction: str
    description: str
    severity: str

    @classmethod
    def from_dict(cls, data: dict) -> Issue:
        """Create Issue from dictionary."""
        return cls(
            category=data.get("category", "linguistic"),
            subcategory=data.get("subcategory", ""),
            original=data.get("original", ""),
            correction=data.get("correction", ""),
            description=data.get("description", ""),
            severity=data.get("severity", "MEDIUM"),
        )

    def to_dict(self) -> dict:
        """Convert Issue to dictionary."""
        return {
            "category": self.category,
            "subcategory": self.subcategory,
            "original": self.original,
            "correction": self.correction,
            "description": self.description,
            "severity": self.severity,
        }


@dataclass
class EvaluationMetadata:
    """Metadata for evaluation results."""

    file: str
    language: str
    timestamp: str
    model: str
    label: str

    @classmethod
    def from_dict(cls, data: dict) -> EvaluationMetadata:
        """Create EvaluationMetadata from dictionary."""
        return cls(
            file=data.get("file", ""),
            language=data.get("language", ""),
            timestamp=data.get("timestamp", ""),
            model=data.get("model", ""),
            label=data.get("label", ""),
        )

    def to_dict(self) -> dict:
        """Convert EvaluationMetadata to dictionary."""
        return {
            "file": self.file,
            "language": self.language,
            "timestamp": self.timestamp,
            "model": self.model,
            "label": self.label,
        }


@dataclass
class IssueBreakdown:
    """Breakdown of issues by category."""

    linguistic: int = 0
    localization: int = 0
    distractor_quality: int = 0

    @classmethod
    def from_dict(cls, data: dict) -> IssueBreakdown:
        """Create IssueBreakdown from dictionary."""
        return cls(
            linguistic=data.get("linguistic", 0),
            localization=data.get("localization", 0),
            distractor_quality=data.get("distractor_quality", 0),
        )

    def to_dict(self) -> dict:
        """Convert IssueBreakdown to dictionary."""
        return {
            "linguistic": self.linguistic,
            "localization": self.localization,
            "distractor_quality": self.distractor_quality,
        }


@dataclass
class PenaltyBreakdown:
    """Breakdown of penalties by category."""

    linguistic_penalty: float = 0.0
    localization_penalty: float = 0.0
    distractor_quality_penalty: float = 0.0

    @classmethod
    def from_dict(cls, data: dict) -> PenaltyBreakdown:
        """Create PenaltyBreakdown from dictionary."""
        return cls(
            linguistic_penalty=data.get("linguistic_penalty", 0.0),
            localization_penalty=data.get("localization_penalty", 0.0),
            distractor_quality_penalty=data.get("distractor_quality_penalty", 0.0),
        )

    def to_dict(self) -> dict:
        """Convert PenaltyBreakdown to dictionary."""
        return {
            "linguistic_penalty": self.linguistic_penalty,
            "localization_penalty": self.localization_penalty,
            "distractor_quality_penalty": self.distractor_quality_penalty,
        }


@dataclass
class Scores:
    """Quality scores for evaluation."""

    overall_quality_score: float
    classification: str
    total_issues: int
    total_penalty: float
    issue_breakdown: IssueBreakdown
    penalty_breakdown: PenaltyBreakdown

    @classmethod
    def from_dict(cls, data: dict) -> Scores:
        """Create Scores from dictionary."""
        return cls(
            overall_quality_score=data.get("overall_quality_score", 10.0),
            classification=data.get("classification", "NATIVE"),
            total_issues=data.get("total_issues", 0),
            total_penalty=data.get("total_penalty", 0.0),
            issue_breakdown=IssueBreakdown.from_dict(data.get("issue_breakdown", {})),
            penalty_breakdown=PenaltyBreakdown.from_dict(data.get("penalty_breakdown", {})),
        )

    def to_dict(self) -> dict:
        """Convert Scores to dictionary."""
        return {
            "overall_quality_score": self.overall_quality_score,
            "classification": self.classification,
            "total_issues": self.total_issues,
            "total_penalty": self.total_penalty,
            "issue_breakdown": self.issue_breakdown.to_dict(),
            "penalty_breakdown": self.penalty_breakdown.to_dict(),
        }


@dataclass
class EvaluationResult:
    """Complete evaluation result."""

    issues: List[Issue] = field(default_factory=list)
    metadata: Optional[EvaluationMetadata] = None
    scores: Optional[Scores] = None

    @classmethod
    def from_dict(cls, data: dict) -> EvaluationResult:
        """Create EvaluationResult from dictionary."""
        return cls(
            issues=[Issue.from_dict(issue) for issue in data.get("issues", [])],
            metadata=EvaluationMetadata.from_dict(data["metadata"]) if "metadata" in data else None,
            scores=Scores.from_dict(data["scores"]) if "scores" in data else None,
        )

    def to_dict(self) -> dict:
        """Convert EvaluationResult to dictionary."""
        result = {"issues": [issue.to_dict() for issue in self.issues]}
        if self.metadata:
            result["metadata"] = self.metadata.to_dict()
        if self.scores:
            result["scores"] = self.scores.to_dict()
        return result


@dataclass(frozen=True)
class ErrorPattern:
    """Represents an error pattern from analysis."""

    pattern_name: str
    category: str
    subcategory: str = ""
    impact_level: str = "MEDIUM"
    frequency: str = "common"
    frequency_count: int = 1
    description: str = ""
    examples: List[str] = field(default_factory=list)
    recommendations: str = ""

    @classmethod
    def from_dict(cls, data: dict) -> ErrorPattern:
        """Create ErrorPattern from dictionary."""
        return cls(
            pattern_name=data.get("pattern_name", ""),
            category=data.get("category", ""),
            subcategory=data.get("subcategory", ""),
            impact_level=data.get("impact_level", "MEDIUM"),
            frequency=data.get("frequency", "common"),
            frequency_count=data.get("frequency_count", 1),
            description=data.get("description", ""),
            examples=data.get("examples", []) or [],
            recommendations=data.get("recommendations", ""),
        )

    def to_dict(self) -> dict:
        """Convert ErrorPattern to dictionary."""
        return {
            "pattern_name": self.pattern_name,
            "category": self.category,
            "subcategory": self.subcategory,
            "impact_level": self.impact_level,
            "frequency": self.frequency,
            "frequency_count": self.frequency_count,
            "description": self.description,
            "examples": self.examples,
            "recommendations": self.recommendations,
        }
