"""Error pattern data models."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List


@dataclass
class PatternExample:
    """Example of an error pattern occurrence."""

    wrong: str  # Problematic text
    correct: str  # Corrected text
    context: str  # Where/why it appears


@dataclass
class ErrorPattern:
    """Represents a recurring error pattern."""

    pattern_name: str  # Concise name
    category: str  # "linguistic" or "localization"
    subcategory: str  # Grammar, Cultural, etc.
    impact_level: str  # "HIGH", "MEDIUM", "LOW"
    frequency: str  # "very_common", "common", "occasional", "rare"
    frequency_count: int  # Number of occurrences
    description: str  # Explanation
    examples: List[PatternExample]
