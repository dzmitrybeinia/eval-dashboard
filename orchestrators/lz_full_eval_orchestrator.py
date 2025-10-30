from pathlib import Path
from typing import Type

from config import SUPPORTED_LANGUAGES
from converters.base_converter import BaseConverter
from converters.lz_full_content_converter import LZFullContentConverter

from .base_orchestrator import BaseOrchestrator


class LZFullEvalOrchestrator(BaseOrchestrator):
    def __init__(self, prompts_dir: Path | str = Path("prompts")):
        self.prompts_dir = Path(prompts_dir)

    def get_converter_class(self) -> Type[BaseConverter]:
        return LZFullContentConverter

    def get_prompt(self, content: str, language: str) -> str:
        base_prompt = self._load_prompt("combined_expert.md")
        language_name = self._get_language_display_name(language)
        base_prompt = base_prompt.replace("{LANGUAGE_NAME}", language_name)
        lang_prompt = self._load_language_prompt(language)
        return f"{base_prompt}\n\n---\n\n{lang_prompt}\n\n---\n\n## CONTENT FOR EVALUATION\n\n{content}"

    def should_run_issues_aggregation(self) -> bool:
        return True

    def should_run_pattern_analysis(self) -> bool:
        return True

    def _load_prompt(self, filename: str) -> str:
        prompt_path = self.prompts_dir / "evaluation" / filename
        if not prompt_path.exists():
            raise FileNotFoundError(f"Prompt not found: {prompt_path}")
        return prompt_path.read_text(encoding="utf-8")

    def _load_language_prompt(self, language: str) -> str:
        lang_path = self.prompts_dir / "evaluation" / "languages" / f"{language.lower()}.md"
        if lang_path.exists():
            return lang_path.read_text(encoding="utf-8")
        language_name = self._get_language_display_name(language)
        return f"## LANGUAGE FOCUS: {language_name}\n\nFocus on {language_name} linguistic accuracy and localization quality."

    @staticmethod
    def _get_language_display_name(language: str) -> str:
        mapping = {lang.lower(): lang.title() for lang in SUPPORTED_LANGUAGES}
        return mapping.get(language.lower(), language.title())
