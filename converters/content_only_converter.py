"""Lesson converter for LLM part - converts content without questions/feedback."""

from pathlib import Path
from typing import Dict, List

from .base_converter import BaseConverter


class ContentOnlyConverter(BaseConverter):
    """Convert lesson content to markdown, excluding questions and feedback."""

    def _build_markdown(self, data: Dict, lesson_name: str) -> str:
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

    def _slides_to_markdown(self, slides: List[Dict], md_lines: List[str], sections: List[Dict] | None) -> None:
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

    def _sections_to_markdown(self, sections: List[Dict], md_lines: List[str]) -> None:
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

    def _add_intro(self, md_lines: List[str], factoid: str, sections: List[Dict] | None) -> None:
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

    def _add_content_slide(self, md_lines: List[str], factoid: str, slide_index: int, sections: List[Dict] | None) -> None:
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
