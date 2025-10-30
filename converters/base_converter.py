import json
from pathlib import Path
from typing import Dict, List


class BaseConverter:
    def get_file_extension(self) -> str:
        return ".jsonl"

    def convert_language(self, input_dir: Path, output_dir: Path, language: str) -> bool:
        if not input_dir.exists():
            print(f"Source directory not found: {input_dir}")
            return False

        output_dir.mkdir(parents=True, exist_ok=True)
        json_files = sorted(input_dir.glob(f"*{self.get_file_extension()}"))

        if not json_files:
            print(f"No {self.get_file_extension()} files found in {input_dir}")
            return False

        total_converted = 0
        total_skipped = 0

        for json_file in json_files:
            try:
                print(f"Processing {json_file.name}...")
                lessons = self._load_lessons(json_file)

                for lesson_index, lesson_data in enumerate(lessons, 1):
                    lesson_name = self._extract_lesson_name(json_file, lesson_data)
                    safe_name = self._sanitize_filename(lesson_name)
                    output_file = output_dir / f"{safe_name}.md"

                    if output_file.exists():
                        print(f"  Skipping lesson {lesson_index}/{len(lessons)}: {lesson_name} (already exists)")
                        total_skipped += 1
                        continue

                    markdown = self._build_markdown(lesson_data, lesson_name)
                    self._save_markdown(output_file, markdown)
                    total_converted += 1
                    print(f"  Converted lesson {lesson_index}/{len(lessons)}: {lesson_name}")

            except Exception as exc:
                print(f"Error processing {json_file.name}: {exc}")

        print(f"\nConversion Summary:")
        print(f"  Converted: {total_converted}")
        print(f"  Skipped: {total_skipped}")
        print(f"  Total lessons: {total_converted + total_skipped}")

        return (total_converted + total_skipped) > 0

    def _load_lessons(self, input_path: Path) -> List[Dict]:
        lessons = []
        with open(input_path, "r", encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if line:
                    lessons.append(json.loads(line))
        return lessons

    def _sanitize_filename(self, name: str) -> str:
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            name = name.replace(char, '_')
        name = name.replace('  ', ' ').strip()
        return name[:200]

    def _extract_lesson_name(self, json_file: Path, data: Dict) -> str:
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

    def _save_markdown(self, output_path: Path, markdown: str) -> bool:
        with open(output_path, "w", encoding="utf-8") as handle:
            handle.write(markdown)
        return True

    def _build_markdown(self, data: Dict, lesson_name: str) -> str:
        """Override this method in subclasses to generate markdown content."""
        raise NotImplementedError("Subclasses must implement _build_markdown")
