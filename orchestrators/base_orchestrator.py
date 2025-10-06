"""Base orchestrator with common prompt loading logic."""
from pathlib import Path
from typing import Type

from config import SUPPORTED_LANGUAGES
from converters.base import AbstractConverter
from orchestrators.base import AbstractOrchestrator


class BaseOrchestrator(AbstractOrchestrator):
    """Base orchestrator with common prompt loading logic."""

    def __init__(self, prompt_file: str, use_language_prompts: bool = True):
        super().__init__()
        self.prompt_file = prompt_file
        self.use_language_prompts = use_language_prompts

    def build_evaluation_prompt(self, content: str, language: str) -> str:
        base_prompt = self._load_prompt(self.prompt_file)
        language_name = self.get_language_display_name(language)
        base_prompt = base_prompt.replace("{LANGUAGE_NAME}", language_name)

        if self.use_language_prompts:
            lang_prompt = self._load_language_prompt(language)
            return f"{base_prompt}\n\n---\n\n{lang_prompt}\n\n---\n\n## CONTENT FOR EVALUATION\n\n{content}"

        return f"{base_prompt}\n\n---\n\n## CONTENT FOR EVALUATION\n\n{content}"

    def _load_prompt(self, filename: str) -> str:
        prompt_path = self.prompts_dir / "evaluation" / filename
        if not prompt_path.exists():
            raise FileNotFoundError(f"Prompt not found: {prompt_path}")
        return prompt_path.read_text(encoding="utf-8")

    def _load_language_prompt(self, language: str) -> str:
        lang_path = self.prompts_dir / "evaluation" / "languages" / f"{language.lower()}.md"
        if lang_path.exists():
            return lang_path.read_text(encoding="utf-8")

        language_name = self.get_language_display_name(language)
        return f"## LANGUAGE FOCUS: {language_name}\n\nFocus on {language_name} linguistic accuracy and localization quality."

    def build_pattern_analysis_prompt(self, issues: list, language: str, category: str, severity: str) -> str:
        import json
        template_path = self.prompts_dir / "pattern_analysis" / "error_pattern_analysis.md"
        if not template_path.exists():
            return ""

        template = template_path.read_text(encoding="utf-8")
        return (
            f"{template}\n\n"
            f"**Target language:** {language.title()}\n"
            f"**Pattern focus:** {category} issues with {severity} severity\n"
            f"**Issue count:** {len(issues)}\n\n"
            f"**Issues to analyse:**\n{json.dumps(issues, ensure_ascii=False, indent=2)}"
        )
