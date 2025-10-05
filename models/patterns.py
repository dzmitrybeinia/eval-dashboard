"""Error pattern data models."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List


@dataclass
class PatternExample:
    """Example of an error pattern occurrence."""

    wrong: str
    correct: str
    context: str


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
