"""Lesson converter for SLM part - converts only questions/statements and feedback."""

from pathlib import Path
from typing import Dict, List

from .base_converter import BaseConverter


class YesNoConverter(BaseConverter):
    """Convert lesson questions/statements and feedback to markdown, excluding content."""

    def _build_markdown(self, data: Dict, lesson_name: str) -> str:
        md_lines: List[str] = [f"# Lesson name: {lesson_name}", ""]
        slides = data.get("slides", []) if isinstance(data, dict) else []

        if slides:
            self._slides_to_markdown(slides, md_lines)
        elif isinstance(data, dict) and data.get("questions"):
            md_lines.append("## Questions")
            md_lines.append("")
            for q in data.get("questions", []):
                if isinstance(q, dict):
                    md_lines.append(f"**Question:** {q.get('question', '')}")
                    md_lines.append("")

        return "\n".join(md_lines)

    def _slides_to_markdown(self, slides: List[Dict], md_lines: List[str]) -> None:
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
