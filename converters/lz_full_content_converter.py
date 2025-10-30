from pathlib import Path
from typing import Dict, List

from .base_converter import BaseConverter


class LZFullContentConverter(BaseConverter):
    """Convert LZ quiz JSON files into markdown with full content (lessons + all quiz types)."""

    def _build_markdown(self, data: Dict, lesson_name: str) -> str:
        md_lines: List[str] = [f"# Lesson name: {lesson_name}", ""]
        sections = data.get("sections", []) if isinstance(data, dict) else []
        slides = data.get("slides", []) if isinstance(data, dict) else []

        if slides:
            self._slides_to_markdown(slides, md_lines, sections)
        elif sections:
            self._sections_to_markdown(sections, md_lines)
        elif isinstance(data, dict) and any(
            key in data for key in ("generatedObjects", "content", "questions")
        ):
            md_lines.append("## Content")
            md_lines.append("")
            md_lines.append("### Quiz Content")
            md_lines.append("")
            if data.get("content"):
                md_lines.append(str(data["content"]))
                md_lines.append("")

        return "\n".join(md_lines)

    def _slides_to_markdown(self, slides: List[Dict], md_lines: List[str], sections: List[Dict] | None) -> None:
        intro_added = False
        slide_index = 0

        for slide_num, slide in enumerate(slides):
            if slide.get("status") != "Success":
                continue

            generated_objects = slide.get("generatedObjects", [])
            first_success_inputs = next(
                (
                    obj.get("inputs", {})
                    for obj in generated_objects
                    if obj.get("status") == "Success"
                ),
                {},
            )

            if not intro_added and slide_num == 0:
                self._add_intro(
                    md_lines,
                    first_success_inputs.get("factoid", "Introduction"),
                    sections,
                )
                intro_added = True

            quiz_objects = [
                obj
                for obj in generated_objects
                if obj.get("status") == "Success"
            ]

            if not quiz_objects:
                continue

            first_quiz_inputs = quiz_objects[0].get("inputs", {})

            self._add_content_slide(
                md_lines,
                first_quiz_inputs.get("factoid", f"Content {slide_num + 1}"),
                slide_index,
                sections,
            )
            slide_index += 1

            for obj in quiz_objects:
                quiz_type = obj.get("type")
                content = obj.get("generatedContent", {})

                if quiz_type == "YesNo":
                    self._add_yes_no(md_lines, content)
                elif quiz_type == "DynamicQuiz":
                    self._add_dynamic_quiz(md_lines, content)
                elif quiz_type == "FillInTheBlanks":
                    self._add_fill_in_blanks(md_lines, content)
                elif quiz_type == "KahootQuiz":
                    self._add_kahoot_quiz(md_lines, content)
                elif quiz_type == "OpenEnded":
                    self._add_open_ended(md_lines, content)
                elif quiz_type == "Match":
                    self._add_match(md_lines, content)
                elif quiz_type == "Sort":
                    self._add_sort(md_lines, content)
                elif quiz_type == "Group":
                    self._add_group(md_lines, content)

            for obj in generated_objects:
                if obj.get("status") != "Success" and obj.get("error"):
                    md_lines.append(
                        f"<!-- Error processing slide {slide_num}: {obj.get('error', 'Unknown error')} -->"
                    )
                    md_lines.append("")

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

    def _add_yes_no(self, md_lines: List[str], content: Dict) -> None:
        statement = content.get("statement", "")
        is_true = content.get("isStatementTrue", True)
        feedback = content.get("feedback", content.get("explanation", ""))

        md_lines.append("## YesNo")
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

    def _add_dynamic_quiz(self, md_lines: List[str], content: Dict) -> None:
        question = content.get("question", "")
        answers = content.get("answers", [])
        feedback = content.get("feedback", content.get("explanation", ""))

        md_lines.append("## DynamicQuiz")
        md_lines.append("")
        md_lines.append(f"**Question:** {question}")
        md_lines.append("")

        if answers:
            md_lines.append("**Answers:**")
            for i, answer in enumerate(answers, 1):
                answer_text = answer.get("answer", "")
                is_correct = answer.get("correct", False)
                marker = "✓" if is_correct else "✗"
                md_lines.append(f"{i}. [{marker}] {answer_text}")
            md_lines.append("")

        if feedback:
            md_lines.append("**Feedback:**")
            md_lines.append(feedback)
            md_lines.append("")
        md_lines.append("")

    def _add_fill_in_blanks(self, md_lines: List[str], content: Dict) -> None:
        title = content.get("title", "Fill in the Blanks")
        sentence = content.get("sentence", content.get("passage", ""))
        distractors = content.get("distractors", [])

        md_lines.append("## FillInTheBlanks")
        md_lines.append("")
        md_lines.append(f"**Title:** {title}")
        md_lines.append("")
        md_lines.append(f"**Sentence:** {sentence}")
        md_lines.append("")

        if distractors:
            md_lines.append("**Distractors:**")
            for distractor in distractors:
                md_lines.append(f"- {distractor}")
            md_lines.append("")
        md_lines.append("")

    def _add_kahoot_quiz(self, md_lines: List[str], content: Dict) -> None:
        question = content.get("question", "")
        answers = content.get("answers", [])
        image_query = content.get("imageSearchQuery", "")

        md_lines.append("## KahootQuiz")
        md_lines.append("")
        md_lines.append(f"**Question:** {question}")
        md_lines.append("")

        if answers:
            md_lines.append("**Answers:**")
            for i, answer in enumerate(answers, 1):
                answer_text = answer.get("answer", "")
                is_correct = answer.get("correct", False)
                marker = "✓" if is_correct else "✗"
                md_lines.append(f"{i}. [{marker}] {answer_text}")
            md_lines.append("")

        if image_query:
            md_lines.append(f"**Image Search:** {image_query}")
            md_lines.append("")
        md_lines.append("")

    def _add_open_ended(self, md_lines: List[str], content: Dict) -> None:
        question = content.get("question", "")
        answer = content.get("answer", "")
        explanation = content.get("explanation", "")

        md_lines.append("## OpenEnded")
        md_lines.append("")
        md_lines.append(f"**Question:** {question}")
        md_lines.append("")

        if answer:
            md_lines.append(f"**Answer:** {answer}")
            md_lines.append("")

        if explanation:
            md_lines.append("**Explanation:**")
            md_lines.append(explanation)
            md_lines.append("")
        md_lines.append("")

    def _add_match(self, md_lines: List[str], content: Dict) -> None:
        question = content.get("question", "")
        pairs = content.get("pairs", {})

        md_lines.append("## Match")
        md_lines.append("")
        md_lines.append(f"**Question:** {question}")
        md_lines.append("")

        if pairs:
            md_lines.append("**Pairs:**")
            for key, value in pairs.items():
                md_lines.append(f"- {key}: {value}")
            md_lines.append("")
        md_lines.append("")

    def _add_sort(self, md_lines: List[str], content: Dict) -> None:
        question = content.get("question", "")
        items = content.get("items", [])

        md_lines.append("## Sort")
        md_lines.append("")
        md_lines.append(f"**Question:** {question}")
        md_lines.append("")

        if items:
            md_lines.append("**Items to Sort:**")
            for i, item in enumerate(items, 1):
                md_lines.append(f"{i}. {item}")
            md_lines.append("")
        md_lines.append("")

    def _add_group(self, md_lines: List[str], content: Dict) -> None:
        question = content.get("question", "")
        groups = content.get("groups", [])

        md_lines.append("## Group")
        md_lines.append("")
        md_lines.append(f"**Question:** {question}")
        md_lines.append("")

        if groups:
            md_lines.append("**Groups:**")
            for group in groups:
                key = group.get("key", "")
                values = group.get("values", [])
                md_lines.append(f"- **{key}:**")
                for value in values:
                    md_lines.append(f"  - {value}")
            md_lines.append("")
        md_lines.append("")
