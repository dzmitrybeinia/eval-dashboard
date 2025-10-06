"""Base orchestrator interface."""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Type

from config import SUPPORTED_LANGUAGES
from converters.base import AbstractConverter

class AbstractOrchestrator(ABC):
    """Defines the evaluation pipeline."""

    def __init__(self, prompts_dir: Path | str = Path("prompts")):
        self.prompts_dir = Path(prompts_dir)

    @abstractmethod
    def get_converter_class(self) -> Type[AbstractConverter]:
        pass

    @abstractmethod
    def build_evaluation_prompt(self, content: str, language: str) -> str:
        pass

    @abstractmethod
    def build_pattern_analysis_prompt(self, issues: list, language: str, category: str, severity: str) -> str:
        pass

    @abstractmethod
    def should_run_issues_aggregation(self) -> bool:
        pass

    @abstractmethod
    def should_run_pattern_analysis(self) -> bool:
        pass

    @staticmethod
    def get_language_display_name(language: str) -> str:
        mapping = {lang.lower(): lang.title() for lang in SUPPORTED_LANGUAGES}
        return mapping.get(language.lower(), language.title())
