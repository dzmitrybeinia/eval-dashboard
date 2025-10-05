"""Minimal orchestrator example."""

from __future__ import annotations

from pathlib import Path
from typing import Type

from converters.base import AbstractConverter
from converters.lesson_yes_no_converter import LessonYesNoConverter
from orchestrators.base import AbstractOrchestrator


class MinimalOrchestrator(AbstractOrchestrator):
    """
    Minimal orchestrator example:
    - Uses standard converter
    - Simplified evaluation prompt
    - Skips pattern analysis
    """

    def get_converter_class(self) -> Type[AbstractConverter]:
        return LessonYesNoConverter

    def build_evaluation_prompt(self, content: str, language: str) -> str:
        """Minimal prompt - just content, no language-specific instructions."""
        return (
            "You are a localization quality evaluator. "
            "Analyze the following content and return issues in JSON format.\n\n"
            f"## Content to evaluate:\n\n{content}\n\n"
            "Return JSON with 'issues' array."
        )

    def build_pattern_analysis_prompt(
        self,
        issues: list,
        language: str,
        category: str,
        severity: str,
    ) -> str:
        """Not used since we skip pattern analysis."""
        return ""

    def should_run_issues_aggregation(self) -> bool:
        """Still aggregate issues."""
        return True

    def should_run_pattern_analysis(self) -> bool:
        """Skip pattern analysis in minimal mode."""
        return False
