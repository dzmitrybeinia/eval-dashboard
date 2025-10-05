"""SLM orchestrator for questions/statements and feedback evaluation."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Type

from converters.base import AbstractConverter
from converters.yes_no_converter import YesNoConverter

from .base import AbstractOrchestrator


class YesNoOrchestrator(AbstractOrchestrator):
    """
    SLM (Statement-Level Model) evaluation flow:
    - Uses LessonConverterSLMPart (questions/feedback only, no content)
    - Linguistic-only evaluation prompt
    - Focuses on questions, statements, answers, and feedback
    - Runs full post-processing (aggregation + pattern analysis)
    """


    def get_converter_class(self) -> Type[AbstractConverter]:
        """Return LessonConverterSLMPart for SLM pipeline."""
        return YesNoConverter

    def build_evaluation_prompt(self, content: str, language: str) -> str:
        """
        Build linguistic-only evaluation prompt for questions/feedback.
        Uses the same linguistic-only prompt as LLM flow.
        """
        # Load linguistic-only prompt
        linguistic_prompt_path = self.prompts_dir / "evaluation" / "linguistic_only.md"
        try:
            linguistic_prompt = linguistic_prompt_path.read_text(encoding="utf-8")
        except FileNotFoundError:
            raise FileNotFoundError(
                f"Linguistic-only prompt not found: {linguistic_prompt_path}"
            )

        # Load language-specific prompt (optional)
        language_name = self.get_language_display_name(language)
        lang_path = (
            self.prompts_dir / "evaluation" / "languages" / f"{language.lower()}.md"
        )

        if lang_path.exists():
            lang_prompt = lang_path.read_text(encoding="utf-8")
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
        Build pattern analysis prompt for SLM issues.
        """
        template_path = (
            self.prompts_dir / "pattern_analysis" / "error_pattern_analysis.md"
        )
        try:
            template = template_path.read_text(encoding="utf-8")
        except FileNotFoundError:
            raise FileNotFoundError(
                f"Pattern analysis prompt not found: {template_path}"
            )

        return (
            f"{template}\n\n"
            f"**Target language:** {language.title()}\n"
            f"**Pattern focus:** {category} issues with {severity} severity in questions/feedback\n"
            f"**Issue count:** {len(issues)}\n\n"
            f"**Issues to analyse:**\n{json.dumps(issues, ensure_ascii=False, indent=2)}"
        )

    def should_run_issues_aggregation(self) -> bool:
        """Run issue aggregation for SLM evaluation."""
        return True

    def should_run_pattern_analysis(self) -> bool:
        """Run pattern analysis for SLM evaluation (enabled)."""
        return True
