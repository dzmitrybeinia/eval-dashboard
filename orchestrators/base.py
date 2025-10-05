"""Base orchestrator interface."""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Type

from config import SUPPORTED_LANGUAGES
from converters.base import AbstractConverter


class AbstractOrchestrator(ABC):
    """
    Defines the evaluation pipeline.

    Orchestrators control:
    1. Which converter to use
    2. How to build evaluation prompts
    3. How to build pattern analysis prompts
    4. Which post-processing steps to run
    """

    def __init__(self, prompts_dir: Path | str = Path("prompts")):
        """Initialize orchestrator with prompts directory."""
        self.prompts_dir = Path(prompts_dir)

    @abstractmethod
    def get_converter_class(self) -> Type[AbstractConverter]:
        """Return the converter class to use for this pipeline."""
        pass

    @abstractmethod
    def build_evaluation_prompt(self, content: str, language: str) -> str:
        """
        Build the complete prompt for evaluating markdown content.

        This replaces PromptBuilder - orchestrator now handles:
        - Loading base evaluation prompt
        - Loading language-specific instructions
        - Combining them with content

        Args:
            content: Markdown content to evaluate
            language: Target language (e.g., "french", "polish")

        Returns:
            Complete prompt string ready to send to LLM
        """
        pass

    @abstractmethod
    def build_pattern_analysis_prompt(
        self,
        issues: list,
        language: str,
        category: str,
        severity: str,
    ) -> str:
        """
        Build the prompt for analyzing error patterns.

        Args:
            issues: List of issue dictionaries from evaluation
            language: Target language
            category: Issue category (e.g., "linguistic", "localization")
            severity: Severity level (e.g., "HIGH", "MEDIUM", "MINOR")

        Returns:
            Complete prompt string for pattern analysis
        """
        pass

    @abstractmethod
    def should_run_issues_aggregation(self) -> bool:
        """Whether to run IssueAggregator after evaluation."""
        pass

    @abstractmethod
    def should_run_pattern_analysis(self) -> bool:
        """Whether to run ErrorPatternAnalyzer after aggregation."""
        pass

    @staticmethod
    def get_language_display_name(language: str) -> str:
        """
        Convert language code to display name.

        Uses SUPPORTED_LANGUAGES from config to dynamically generate mappings.
        This ensures consistency across all orchestrators and centralizes language configuration.

        Args:
            language: Language code (e.g., "polish", "french")

        Returns:
            Display name (e.g., "Polish", "French")
        """
        # Build mapping from SUPPORTED_LANGUAGES
        mapping = {lang.lower(): lang.title() for lang in SUPPORTED_LANGUAGES}
        return mapping.get(language.lower(), language.title())
