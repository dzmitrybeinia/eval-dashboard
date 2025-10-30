from pathlib import Path
from typing import Dict, List

from .base_converter import BaseConverter


class LZQuizConverter(BaseConverter):
    """Convert LZ quiz/exercise content to markdown, excluding lesson content slides."""

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

            quiz_objects = [
                obj
                for obj in slide.get("generatedObjects", [])
                if obj.get("status") == "Success"
            ]

            for obj in quiz_objects:
                quiz_type = obj.get("type")
                content = obj.get("generatedContent", {})
                question_count += 1

                if quiz_type == "YesNo":
                    self._add_yes_no(md_lines, content, question_count)
                elif quiz_type == "DynamicQuiz":
                    self._add_dynamic_quiz(md_lines, content, question_count)
                elif quiz_type == "FillInTheBlanks":
                    self._add_fill_in_blanks(md_lines, content, question_count)
                elif quiz_type == "KahootQuiz":
                    self._add_kahoot_quiz(md_lines, content, question_count)
                elif quiz_type == "OpenEnded":
                    self._add_open_ended(md_lines, content, question_count)
                elif quiz_type == "Match":
                    self._add_match(md_lines, content, question_count)
                elif quiz_type == "Sort":
                    self._add_sort(md_lines, content, question_count)
                elif quiz_type == "Group":
                    self._add_group(md_lines, content, question_count)

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

    def _add_dynamic_quiz(self, md_lines: List[str], content: Dict, q_num: int) -> None:
        question = content.get("question", "")
        answers = content.get("answers", [])
        feedback = content.get("feedback", content.get("explanation", ""))

        md_lines.append(f"## Question {q_num}: DynamicQuiz")
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

    def _add_fill_in_blanks(self, md_lines: List[str], content: Dict, q_num: int) -> None:
        title = content.get("title", "Fill in the Blanks")
        sentence = content.get("sentence", content.get("passage", ""))
        distractors = content.get("distractors", [])

        md_lines.append(f"## Question {q_num}: FillInTheBlanks")
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

    def _add_kahoot_quiz(self, md_lines: List[str], content: Dict, q_num: int) -> None:
        question = content.get("question", "")
        answers = content.get("answers", [])
        image_query = content.get("imageSearchQuery", "")

        md_lines.append(f"## Question {q_num}: KahootQuiz")
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

    def _add_open_ended(self, md_lines: List[str], content: Dict, q_num: int) -> None:
        question = content.get("question", "")
        answer = content.get("answer", "")
        explanation = content.get("explanation", "")

        md_lines.append(f"## Question {q_num}: OpenEnded")
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

    def _add_match(self, md_lines: List[str], content: Dict, q_num: int) -> None:
        question = content.get("question", "")
        pairs = content.get("pairs", {})

        md_lines.append(f"## Question {q_num}: Match")
        md_lines.append("")
        md_lines.append(f"**Question:** {question}")
        md_lines.append("")

        if pairs:
            md_lines.append("**Pairs:**")
            for key, value in pairs.items():
                md_lines.append(f"- {key}: {value}")
            md_lines.append("")
        md_lines.append("")

    def _add_sort(self, md_lines: List[str], content: Dict, q_num: int) -> None:
        question = content.get("question", "")
        items = content.get("items", [])

        md_lines.append(f"## Question {q_num}: Sort")
        md_lines.append("")
        md_lines.append(f"**Question:** {question}")
        md_lines.append("")

        if items:
            md_lines.append("**Items to Sort:**")
            for i, item in enumerate(items, 1):
                md_lines.append(f"{i}. {item}")
            md_lines.append("")
        md_lines.append("")

    def _add_group(self, md_lines: List[str], content: Dict, q_num: int) -> None:
        question = content.get("question", "")
        groups = content.get("groups", [])

        md_lines.append(f"## Question {q_num}: Group")
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
