from abc import ABC, abstractmethod
from pathlib import Path
from typing import Type

from converters.base_converter import BaseConverter


class BaseOrchestrator(ABC):
    @abstractmethod
    def get_converter_class(self) -> Type[BaseConverter]:
        raise NotImplementedError

    @abstractmethod
    def get_prompt(self, content: str, language: str) -> str:
        raise NotImplementedError

    @abstractmethod
    def should_run_issues_aggregation(self) -> bool:
        raise NotImplementedError

    @abstractmethod
    def should_run_pattern_analysis(self) -> bool:
        raise NotImplementedError
