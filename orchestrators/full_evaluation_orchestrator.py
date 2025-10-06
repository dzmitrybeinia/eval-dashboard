"""Standard evaluation orchestrator that reproduces current behavior."""

from typing import Type

from converters.base import AbstractConverter
from converters.full_content_converter import FullContentConverter

from .base_orchestrator import BaseOrchestrator


class FullEvaluationOrchestrator(BaseOrchestrator):
    """Standard evaluation flow."""

    def __init__(self):
        super().__init__(prompt_file="combined_expert.md", use_language_prompts=True)

    def get_converter_class(self) -> Type[AbstractConverter]:
        return FullContentConverter

    def should_run_issues_aggregation(self) -> bool:
        return True

    def should_run_pattern_analysis(self) -> bool:
        return True
