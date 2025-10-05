"""Example custom format converter."""

from __future__ import annotations

import json
from pathlib import Path

from converters.base import AbstractConverter


class CustomFormatConverter(AbstractConverter):
    """
    Example converter for a different JSON structure.

    Demonstrates how to implement AbstractConverter for custom formats.
    """

    def convert_file(self, input_path: Path, output_path: Path) -> bool:
        try:
            # Load custom JSON format
            data = json.loads(input_path.read_text(encoding="utf-8"))

            # Custom parsing logic
            markdown = self._parse_custom_format(data)

            # Write output
            output_path.write_text(markdown, encoding="utf-8")
            return True
        except Exception as exc:
            print(f"Error converting {input_path.name}: {exc}")
            return False

    def convert_language(
        self,
        input_dir: Path,
        output_dir: Path,
        language: str,
    ) -> bool:
        output_dir.mkdir(parents=True, exist_ok=True)
        files = list(input_dir.glob(f"*{self.get_file_extension()}"))

        if not files:
            print(f"❌ No {self.get_file_extension()} files found in {input_dir}")
            return False

        converted = 0
        for file in files:
            output_file = output_dir / f"{file.stem}.md"
            if self.convert_file(file, output_file):
                converted += 1

        return converted > 0

    def get_file_extension(self) -> str:
        """Custom format uses .json instead of .jsonl"""
        return ".json"

    def _parse_custom_format(self, data: dict) -> str:
        """Custom parsing logic here."""
        return f"# Custom Format\n\n{data.get('content', '')}"
