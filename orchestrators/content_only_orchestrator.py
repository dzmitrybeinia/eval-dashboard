from pathlib import Path
from typing import Type

from config import SUPPORTED_LANGUAGES
from converters.base_converter import BaseConverter
from converters.content_only_converter import ContentOnlyConverter


class ContentOnlyOrchestrator:
    def __init__(self, prompts_dir: Path | str = Path("prompts")):
        self.prompts_dir = Path(prompts_dir)

    def get_converter_class(self) -> Type[BaseConverter]:
        return ContentOnlyConverter

    def get_prompt(self, content: str, language: str) -> str:
        linguistic_prompt = self._load_prompt("linguistic_only.md")
        language_name = self._get_language_display_name(language)
        lang_path = self.prompts_dir / "evaluation" / "languages" / f"{language.lower()}.md"
        if lang_path.exists():
            lang_prompt = lang_path.read_text(encoding="utf-8")
            lang_section = f"\n\n## LANGUAGE-SPECIFIC RULES: {language_name}\n\n{lang_prompt}\n\n"
        else:
            lang_section = f"\n\n## TARGET LANGUAGE: {language_name}\n\nEvaluate linguistic accuracy for {language_name}.\n\n"
        return f"{linguistic_prompt}\n\n{lang_section}---\n\n## CONTENT FOR EVALUATION\n\n{content}"

    def should_run_issues_aggregation(self) -> bool:
        return True

    def should_run_pattern_analysis(self) -> bool:
        return True

    def _load_prompt(self, filename: str) -> str:
        prompt_path = self.prompts_dir / "evaluation" / filename
        if not prompt_path.exists():
            raise FileNotFoundError(f"Prompt not found: {prompt_path}")
        return prompt_path.read_text(encoding="utf-8")

    @staticmethod
    def _get_language_display_name(language: str) -> str:
        mapping = {lang.lower(): lang.title() for lang in SUPPORTED_LANGUAGES}
        return mapping.get(language.lower(), language.title())
