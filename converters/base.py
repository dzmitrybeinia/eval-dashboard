"""Base converter interface."""

from abc import ABC, abstractmethod
from pathlib import Path

class AbstractConverter(ABC):
    """Base interface for converting source data to markdown."""

    @abstractmethod
    def convert_file(self, input_path: Path, output_path: Path) -> bool:
        """Convert single file from JSON to markdown."""
        pass

    @abstractmethod
    def convert_language(self, input_dir: Path, output_dir: Path, language: str) -> bool:
        """Convert all files for a specific language."""
        pass

    def get_file_extension(self) -> str:
        """Return input file extension to search for."""
        return ".jsonl"
