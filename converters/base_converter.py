import json
from pathlib import Path
from typing import Dict


class BaseConverter:
    def get_file_extension(self) -> str:
        return ".jsonl"

    def convert_file(self, input_path: Path, output_path: Path) -> bool:
        try:
            data = self._load_json(input_path)
            lesson_name = self._extract_lesson_name(input_path, data)
            markdown = self._build_markdown(data, lesson_name)
            return self._save_markdown(output_path, markdown)
        except Exception as exc:
            print(f"Error processing {input_path}: {exc}")
            return False

    def convert_language(self, input_dir: Path, output_dir: Path, language: str) -> bool:
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

    def _load_json(self, input_path: Path) -> Dict:
        with open(input_path, "r", encoding="utf-8") as handle:
            return json.load(handle)

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
