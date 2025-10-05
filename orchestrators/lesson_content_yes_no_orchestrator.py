"""Standard evaluation orchestrator that reproduces current behavior."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Type

from converters.base import AbstractConverter
from converters.lesson_yes_no_converter import LessonYesNoConverter

from .base import AbstractOrchestrator


class LessonContentYesNoOrchestrator(AbstractOrchestrator):
    """
    Standard evaluation flow that reproduces current behavior:
    - Uses YesNoQuestionConverter
    - Combines base + language evaluation prompts
    - Uses standard pattern analysis prompt
    - Runs full post-processing (aggregation + patterns)
    """

    def get_converter_class(self) -> Type[AbstractConverter]:
        """Return YesNoQuestionConverter for standard pipeline."""
        return LessonYesNoConverter

    def build_evaluation_prompt(self, content: str, language: str) -> str:
        """
        Build complete evaluation prompt by combining:
        - Base combined expert prompt
        - Language-specific instructions
        - Content to evaluate
        """
        # Load base combined expert prompt
        base_path = self.prompts_dir / "evaluation" / "combined_expert.md"
        try:
            base_prompt = base_path.read_text(encoding="utf-8")
        except FileNotFoundError:
            raise FileNotFoundError(
                f"Combined expert prompt not found: {base_path}"
            )

        # Replace {LANGUAGE_NAME} placeholder
        language_name = self.get_language_display_name(language)
        base_prompt = base_prompt.replace("{LANGUAGE_NAME}", language_name)

        # Load language-specific prompt
        lang_path = self.prompts_dir / "evaluation" / "languages" / f"{language.lower()}.md"
        if lang_path.exists():
            lang_prompt = lang_path.read_text(encoding="utf-8")
        else:
            # Fallback for languages without specific prompt
            lang_prompt = (
                f"## LANGUAGE FOCUS: {language_name}\n\n"
                f"Focus on {language_name} linguistic accuracy and localization quality."
            )

        # Combine everything
        return (
            f"{base_prompt}\n\n---\n\n{lang_prompt}\n\n---\n\n"
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
        Build pattern analysis prompt from template.
        """
        # Load pattern analysis prompt template
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
            f"**Pattern focus:** {category} issues with {severity} severity\n"
            f"**Issue count:** {len(issues)}\n\n"
            f"**Issues to analyse:**\n{json.dumps(issues, ensure_ascii=False, indent=2)}"
        )

    def should_run_issues_aggregation(self) -> bool:
        """Standard orchestrator runs full aggregation."""
        return True

    def should_run_pattern_analysis(self) -> bool:
        """Standard orchestrator runs full pattern analysis."""
        return True
