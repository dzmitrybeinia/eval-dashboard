"""Lesson converter for SLM part - converts only questions/statements and feedback."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List

from .base import AbstractConverter


class YesNoConverter(AbstractConverter):
    """Convert lesson questions/statements and feedback to markdown, excluding content."""

    def convert_file(self, input_path: Path, output_path: Path) -> bool:
        """Convert single JSONL file to markdown (questions/feedback only)."""
        try:
            with open(input_path, "r", encoding="utf-8") as handle:
                data = json.load(handle)

            lesson_name = self._lesson_name(input_path, data)
            markdown = self._build_markdown(data, lesson_name)

            with open(output_path, "w", encoding="utf-8") as handle:
                handle.write(markdown)
            return True
        except Exception as exc:
            print(f"Error processing {input_path}: {exc}")
            return False

    def convert_language(
        self,
        input_dir: Path,
        output_dir: Path,
        language: str,
    ) -> bool:
        """Convert all JSON files for a specific language."""
        if not input_dir.exists():
            print(f"❌ Source directory not found: {input_dir}")
            return False

        output_dir.mkdir(parents=True, exist_ok=True)
        json_files = sorted(input_dir.glob(f"*{self.get_file_extension()}"))

        if not json_files:
            print(f"❌ No {self.get_file_extension()} files found in {input_dir}")
            return False

        converted = 0
        skipped = 0

        for json_file in json_files:
            output_file = output_dir / f"{json_file.stem}.md"
            if output_file.exists():
                print(f"⏭️  Skipping {json_file.name} (output already exists)")
                skipped += 1
                continue

            try:
                print(f"Converting {json_file.name}...")
                if self.convert_file(json_file, output_file):
                    converted += 1
                    print(f"✓ Created {output_file.name}")
                else:
                    print(f"❌ Failed to convert {json_file.name}")
            except Exception as exc:
                print(f"❌ Error converting {json_file.name}: {exc}")

        print("\nConversion Summary:")
        print(f"   ✓ Converted: {converted}")
        print(f"   ⏭️  Skipped: {skipped}")
        print(f"   Total files: {len(json_files)}")

        return (converted + skipped) > 0

    def _lesson_name(self, json_file: Path, data: Dict) -> str:
        """Extract lesson name from metadata or filename."""
        if isinstance(data, dict):
            metadata = data.get("fileMetadata", {})
            if isinstance(metadata, dict) and metadata.get("sourceFilePath"):
                return metadata["sourceFilePath"]

            sections = data.get("sections")
            if isinstance(sections, list) and sections:
                title = sections[0].get("title")
                if title:
                    return title

        filename = json_file.stem
        if "__" in filename:
            return filename.split("__", maxsplit=1)[0].replace("_", " ").title()
        return filename.replace("_", " ").title()

    def _build_markdown(self, data: Dict, lesson_name: str) -> str:
        """Build markdown from data - questions/feedback only, skip lesson content."""
        md_lines: List[str] = [f"# Lesson name: {lesson_name}", ""]
        slides = data.get("slides", []) if isinstance(data, dict) else []

        if slides:
            self._slides_to_markdown(slides, md_lines)
        elif isinstance(data, dict) and data.get("questions"):
            # Fallback for simple question format
            md_lines.append("## Questions")
            md_lines.append("")
            for q in data.get("questions", []):
                if isinstance(q, dict):
                    md_lines.append(f"**Question:** {q.get('question', '')}")
                    md_lines.append("")

        return "\n".join(md_lines)

    def _slides_to_markdown(self, slides: List[Dict], md_lines: List[str]) -> None:
        """Convert slides to markdown - questions/feedback only."""
        question_count = 0

        for slide_num, slide in enumerate(slides):
            if slide.get("status") != "Success":
                continue

            yes_no_objects = [
                obj
                for obj in slide.get("generatedObjects", [])
                if obj.get("status") == "Success" and obj.get("type") == "YesNo"
            ]

            for obj in yes_no_objects:
                question_count += 1
                content = obj.get("generatedContent", {})
                self._add_yes_no(md_lines, content, question_count)

    def _add_yes_no(self, md_lines: List[str], content: Dict, q_num: int) -> None:
        """Extract YesNo question statement and feedback."""
        statement = content.get("statement", "")
        is_true = content.get("isStatementTrue", True)
        feedback = content.get("feedback", content.get("explanation", ""))

        md_lines.append(f"## Question {q_num}: YesNo")
        md_lines.append("")
        md_lines.append(f"**Statement:** {statement}")
        md_lines.append("")
        md_lines.append(f"**Answer:** {'True' if is_true else 'False'}")
        md_lines.append("")
        if feedback:
            md_lines.append("**Feedback:**")
            md_lines.append(feedback)
            md_lines.append("")
        md_lines.append("")
