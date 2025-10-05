"""Evaluation data models."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List


@dataclass
class Issue:
    """Represents a single localization issue."""

    category: str  # e.g., "linguistic", "localization"
    subcategory: str  # e.g., "Grammar", "Cultural", "Terminology"
    original: str  # Original problematic text
    correction: str  # Corrected text
    description: str  # Explanation in English
    severity: str  # e.g., "HIGH", "MEDIUM", "MINOR"


@dataclass
class EvaluationMetadata:
    """Metadata about an evaluation run."""

    file: str  # Source markdown filename
    language: str  # Target language
    timestamp: str  # ISO format timestamp
    model: str  # LLM model used (e.g., "gpt-4.1")
    label: str  # Version label


@dataclass
class EvaluationResult:
    """Complete evaluation result."""

    metadata: EvaluationMetadata
    issues: List[Issue]
    scores: Dict  # From SimpleScorer
