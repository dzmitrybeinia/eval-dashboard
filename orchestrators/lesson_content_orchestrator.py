"""Linguistic-only orchestrator for content evaluation without questions."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Type

from converters.base import AbstractConverter
from converters.lesson_content_converter import LessonContentConverter

from .base import AbstractOrchestrator


class LessonContentOrchestrator(AbstractOrchestrator):
    """
    Linguistic-only evaluation flow:
    - Uses LessonConverterLLMPart (content only, no questions)
    - Simplified linguistic-only evaluation prompt
    - Skips localization issues entirely
    - Runs issue aggregation but skips pattern analysis
    """


    def get_converter_class(self) -> Type[AbstractConverter]:
        """Return LessonConverterLLMPart for linguistic-only pipeline."""
        return LessonContentConverter

    def build_evaluation_prompt(self, content: str, language: str) -> str:
        """
        Build linguistic-only evaluation prompt.
        Uses simplified prompt focused only on linguistic issues.
        """
        # Load linguistic-only prompt
        linguistic_prompt_path = self.prompts_dir / "evaluation" / "linguistic_only.md"
        try:
            linguistic_prompt = linguistic_prompt_path.read_text(encoding="utf-8")
        except FileNotFoundError:
            raise FileNotFoundError(
                f"Linguistic-only prompt not found: {linguistic_prompt_path}"
            )

        # Load language-specific prompt (optional, for language rules)
        language_name = self.get_language_display_name(language)
        lang_path = (
            self.prompts_dir / "evaluation" / "languages" / f"{language.lower()}.md"
        )

        if lang_path.exists():
            lang_prompt = lang_path.read_text(encoding="utf-8")
            # Extract only linguistic-specific rules from language prompt if available
            lang_section = f"\n\n## LANGUAGE-SPECIFIC RULES: {language_name}\n\n{lang_prompt}\n\n"
        else:
            lang_section = (
                f"\n\n## TARGET LANGUAGE: {language_name}\n\n"
                f"Evaluate linguistic accuracy for {language_name}.\n\n"
            )

        # Combine everything
        return (
            f"{linguistic_prompt}\n\n{lang_section}---\n\n"
            f"## CONTENT FOR EVALUATION\n\n{content}"
        )

    def build_pattern_analysis_prompt(
        self,
        issues: list,
        language: str,
        category: str,
        severity: str,
    ) -> str:
        """
        Build pattern analysis prompt.
        Not used since we skip pattern analysis for linguistic-only flow.
        """
        # Load standard pattern analysis prompt (in case it's needed later)
        template_path = (
            self.prompts_dir / "pattern_analysis" / "error_pattern_analysis.md"
        )
        try:
            template = template_path.read_text(encoding="utf-8")
        except FileNotFoundError:
            return ""

        return (
            f"{template}\n\n"
            f"**Target language:** {language.title()}\n"
            f"**Pattern focus:** {category} issues with {severity} severity\n"
            f"**Issue count:** {len(issues)}\n\n"
            f"**Issues to analyse:**\n{json.dumps(issues, ensure_ascii=False, indent=2)}"
        )

    def should_run_issues_aggregation(self) -> bool:
        """Run issue aggregation for linguistic-only evaluation."""
        return True

    def should_run_pattern_analysis(self) -> bool:
        """Skip pattern analysis for linguistic-only flow."""
        return True
