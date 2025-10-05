"""Lesson converter for LLM part - converts content without questions/feedback."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List

from .base import AbstractConverter


class LessonContentConverter(AbstractConverter):
    """Convert lesson content to markdown, excluding questions and feedback."""

    def convert_file(self, input_path: Path, output_path: Path) -> bool:
        """Convert single JSONL file to markdown (content only, no questions)."""
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

        # Return True if we have files to work with (either newly converted or already existing)
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
        """Build markdown from data - content only, skip questions/feedback."""
        md_lines: List[str] = [f"# Lesson name: {lesson_name}", ""]
        sections = data.get("sections", []) if isinstance(data, dict) else []
        slides = data.get("slides", []) if isinstance(data, dict) else []

        if slides:
            self._slides_to_markdown(slides, md_lines, sections)
        elif sections:
            self._sections_to_markdown(sections, md_lines)
        elif isinstance(data, dict) and data.get("content"):
            md_lines.append("## Content")
            md_lines.append("")
            md_lines.append(str(data["content"]))
            md_lines.append("")

        return "\n".join(md_lines)

    def _slides_to_markdown(
        self, slides: List[Dict], md_lines: List[str], sections: List[Dict] | None
    ) -> None:
        """Convert slides to markdown - content only, no questions."""
        intro_added = False
        slide_index = 0

        for slide_num, slide in enumerate(slides):
            if slide.get("status") != "Success":
                continue

            generated_objects = [
                obj
                for obj in slide.get("generatedObjects", [])
                if obj.get("status") == "Success"
            ]

            if not generated_objects:
                continue

            if not intro_added and slide_num == 0:
                first_inputs = generated_objects[0].get("inputs", {})
                self._add_intro(
                    md_lines, first_inputs.get("factoid", "Introduction"), sections
                )
                intro_added = True

            yes_no_objects = [
                obj for obj in generated_objects if obj.get("type") == "YesNo"
            ]

            if not yes_no_objects:
                continue

            first_yes_no_inputs = yes_no_objects[0].get("inputs", {})
            self._add_content_slide(
                md_lines,
                first_yes_no_inputs.get("factoid", f"Content {slide_num + 1}"),
                slide_index,
                sections,
            )
            slide_index += 1

            # Skip the question content itself - we only want lesson content

    def _sections_to_markdown(self, sections: List[Dict], md_lines: List[str]) -> None:
        """Convert sections to markdown - content only."""
        for index, section in enumerate(sections):
            title = section.get("title", f"Section {index + 1}")
            content = section.get("content", "")
            themes = section.get("themes", [])

            if index == 0:
                md_lines.append("## Intro")
            else:
                md_lines.append("## Content slide")
            md_lines.append("")
            md_lines.append(f"### {title}")
            md_lines.append("")
            if content:
                md_lines.append(content)
                md_lines.append("")
            if themes:
                md_lines.append("#### **Themes:**")
                for theme in themes:
                    md_lines.append(f"- {theme}")
                md_lines.append("")

    def _add_intro(
        self, md_lines: List[str], factoid: str, sections: List[Dict] | None
    ) -> None:
        """Add intro section content."""
        if not sections:
            return
        section = sections[0]

        md_lines.append("## Intro")
        md_lines.append("")
        md_lines.append(f"### {section.get('title', factoid.title())}")
        md_lines.append("")

        content = section.get("content", "")
        if content:
            md_lines.append(content)
            md_lines.append("")

        themes = section.get("themes", [])
        if themes:
            md_lines.append("#### **Themes:**")
            for theme in themes:
                md_lines.append(f"- {theme}")
            md_lines.append("")

    def _add_content_slide(
        self,
        md_lines: List[str],
        factoid: str,
        slide_index: int,
        sections: List[Dict] | None,
    ) -> None:
        """Add content slide (without questions/feedback)."""
        if not sections or len(sections) <= slide_index + 1:
            return
        section = sections[slide_index + 1]

        md_lines.append("## Content slide")
        md_lines.append("")
        md_lines.append(f"### {section.get('title', factoid.title())}")
        md_lines.append("")

        content = section.get("content", "")
        if content:
            md_lines.append(content)
            md_lines.append("")

        themes = section.get("themes", [])
        if themes:
            md_lines.append("#### **Themes:**")
            for theme in themes:
                md_lines.append(f"- {theme}")
            md_lines.append("")
