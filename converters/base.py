"""Base converter interface."""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path


class AbstractConverter(ABC):
    """Base interface for converting source data to markdown."""

    @abstractmethod
    def convert_file(self, input_path: Path, output_path: Path) -> bool:
        """
        Convert single file from JSON to markdown.

        Args:
            input_path: Path to source JSON file
            output_path: Path where markdown should be written

        Returns:
            True if conversion succeeded, False otherwise
        """
        pass

    @abstractmethod
    def convert_language(
        self,
        input_dir: Path,
        output_dir: Path,
        language: str,
    ) -> bool:
        """
        Convert all files for a specific language.

        Args:
            input_dir: Directory containing source JSON files
            output_dir: Directory where markdown files should be written
            language: Target language name (e.g., "french", "polish")

        Returns:
            True if at least one file was successfully converted
        """
        pass

    def get_file_extension(self) -> str:
        """
        Return input file extension to search for.
        Default is .jsonl, override if your format differs.
        """
        return ".jsonl"
