"""Converter for LLM-generated lesson content JSON files."""

import json
from pathlib import Path
from typing import Any, Dict, List

from .base_converter import BaseConverter


class LessonContentLLMConverter(BaseConverter):
    """Convert LLM-generated lesson content JSON into markdown."""

    def get_file_extension(self) -> str:
        """LLM payloads use plain JSON files."""
        return ".json"

    def convert_file(self, input_path: Path, output_path: Path) -> bool:
        """Convert a single LLM JSON file to markdown."""
        try:
            with open(input_path, "r", encoding="utf-8") as handle:
                raw_data: Dict[str, Any] = json.load(handle)
        except (OSError, json.JSONDecodeError) as exc:
            print(f"Error reading {input_path}: {exc}")
            return False

        normalized = self._normalize_payload(raw_data)
        sections = normalized.get("sections", [])
        if not sections:
            print(f"[warn] No slides found in {input_path}")
            return False

        lesson_name = self._extract_lesson_name(input_path, normalized)
        markdown = self._build_markdown(normalized, lesson_name)

        try:
            return self._save_markdown(output_path, markdown)
        except OSError as exc:
            print(f"Error writing {output_path}: {exc}")
            return False

    def _normalize_payload(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract slide content and metadata in LessonContentConverter format."""
        response = raw_data.get("response") or {}
        slides = response.get("slides")
        sections: List[Dict[str, Any]] = []

        if isinstance(slides, list):
            for index, slide in enumerate(slides):
                if not isinstance(slide, dict):
                    continue

                content = slide.get("content")
                title = slide.get("title") or f"Slide {index + 1}"
                if not isinstance(content, str) or not content.strip():
                    continue

                section: Dict[str, Any] = {
                    "title": title.strip(),
                    "content": content.strip(),
                }

                themes = slide.get("themes")
                if isinstance(themes, list):
                    cleaned_themes = [
                        theme.strip()
                        for theme in themes
                        if isinstance(theme, str) and theme.strip()
                    ]
                    if cleaned_themes:
                        section["themes"] = cleaned_themes

                question_types = slide.get("question_types")
                if isinstance(question_types, list):
                    cleaned_types = [
                        q_type.strip()
                        for q_type in question_types
                        if isinstance(q_type, str) and q_type.strip()
                    ]
                    if cleaned_types:
                        section["question_types"] = cleaned_types

                sections.append(section)

        metadata: Dict[str, Any] = {}
        title = response.get("title")
        if isinstance(title, str) and title.strip():
            metadata["sourceFilePath"] = title.strip()
        else:
            request = raw_data.get("request")
            if isinstance(request, dict):
                fallback = request.get("lesson_description") or request.get("topicInEnglish")
                if isinstance(fallback, str) and fallback.strip():
                    metadata["sourceFilePath"] = fallback.strip()

        normalized: Dict[str, Any] = {"sections": sections}
        if metadata:
            normalized["fileMetadata"] = metadata
        return normalized

    def _build_markdown(self, data: Dict[str, Any], lesson_name: str) -> str:
        """Render normalized sections into markdown."""
        md_lines: List[str] = [f"# Lesson name: {lesson_name}", ""]
        sections = data.get("sections", [])

        if isinstance(sections, list) and sections:
            self._sections_to_markdown(sections, md_lines)
        else:
            md_lines.append("_No slide content available._")

        return "\n".join(md_lines)

    def _sections_to_markdown(self, sections: List[Dict[str, Any]], md_lines: List[str]) -> None:
        """Render sections with headings adapted to LLM slide structure."""
        for index, section in enumerate(sections):
            title = section.get("title", f"Slide {index + 1}")
            heading = self._section_heading(index, section, title)

            md_lines.append(f"## {heading}")
            md_lines.append("")
            md_lines.append(f"### {title}")
            md_lines.append("")

            content = section.get("content")
            if isinstance(content, str):
                cleaned_content = content.strip()
            else:
                cleaned_content = ""

            if cleaned_content:
                md_lines.append(cleaned_content)
                md_lines.append("")

            themes = section.get("themes", [])
            if isinstance(themes, list):
                cleaned_themes = [
                    theme.strip()
                    for theme in themes
                    if isinstance(theme, str) and theme.strip()
                ]
                if cleaned_themes:
                    md_lines.append("#### **Themes:**")
                    for theme in cleaned_themes:
                        md_lines.append(f"- {theme}")
                    md_lines.append("")

    def _section_heading(self, index: int, section: Dict[str, Any], title: str) -> str:
        """Determine the section heading label for the markdown output."""
        normalized_title = title.lower()
        question_types = [
            q_type.lower()
            for q_type in section.get("question_types", [])
            if isinstance(q_type, str)
        ]

        if index == 0 or "intro" in normalized_title or "intro" in question_types:
            return "Intro"

        summary_keywords = ("summary", "resumen", "conclus", "cierre", "repaso")
        if any(keyword in normalized_title for keyword in summary_keywords):
            return "Summary"
        if any(keyword in question_types for keyword in ("summary", "closing")):
            return "Summary"

        return "Content slide"
