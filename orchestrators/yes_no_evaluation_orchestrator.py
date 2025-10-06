"""SLM orchestrator for questions/statements and feedback evaluation."""

from typing import Type

from converters.base import AbstractConverter
from converters.yes_no_converter import YesNoConverter

from .base_orchestrator import BaseOrchestrator


class YesNoEvaluationOrchestrator(BaseOrchestrator):
    """SLM evaluation flow."""

    def __init__(self):
        super().__init__(prompt_file="linguistic_only.md", use_language_prompts=True)

    def get_converter_class(self) -> Type[AbstractConverter]:
        return YesNoConverter

    def build_evaluation_prompt(self, content: str, language: str) -> str:
        """Override to use different language section format."""
        linguistic_prompt = self._load_prompt(self.prompt_file)
        language_name = self.get_language_display_name(language)

        if self.use_language_prompts:
            lang_path = self.prompts_dir / "evaluation" / "languages" / f"{language.lower()}.md"
            if lang_path.exists():
                lang_prompt = lang_path.read_text(encoding="utf-8")
                lang_section = f"\n\n## LANGUAGE-SPECIFIC RULES: {language_name}\n\n{lang_prompt}\n\n"
            else:
                lang_section = f"\n\n## TARGET LANGUAGE: {language_name}\n\nEvaluate linguistic accuracy for {language_name}.\n\n"
        else:
            lang_section = f"\n\n## TARGET LANGUAGE: {language_name}\n\nEvaluate linguistic accuracy for {language_name}.\n\n"

        return f"{linguistic_prompt}\n\n{lang_section}---\n\n## CONTENT FOR EVALUATION\n\n{content}"

    def should_run_issues_aggregation(self) -> bool:
        return True

    def should_run_pattern_analysis(self) -> bool:
        return True
