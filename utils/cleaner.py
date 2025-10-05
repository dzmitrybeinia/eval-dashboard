"""Directory maintenance utilities."""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Iterable

from config import SUPPORTED_LANGUAGES


class DirectoryCleaner:
    """Clean generated, markdown, and evaluation directories."""

    def __init__(self, base_dir: Path | str = ".") -> None:
        base_path = Path(base_dir)
        # Updated directory names
        self.generated_quizzes_dir = base_path / "raw_json_files"
        self.markdown_quizzes_dir = base_path / "markdown_files"
        self.eval_results_dir = base_path / "eval_results"
        self.issues_dir = base_path / "issues"

    def clean_generated_quizzes(self, language: str | None = None) -> bool:
        return self._clean(self.generated_quizzes_dir, language, "Raw JSON Files")

    def clean_markdown_quizzes(self, language: str | None = None) -> bool:
        return self._clean(self.markdown_quizzes_dir, language, "Markdown Files")

    def clean_eval_results(self, language: str | None = None) -> bool:
        cleaned = self._clean(self.eval_results_dir, language, "Evaluation Results")
        if cleaned:
            self._clean_related_issues(language)
        return cleaned

    def clean_issues(self, language: str | None = None) -> bool:
        return self._clean(self.issues_dir, language, "Issues")

    def _clean(self, base_path: Path, language: str | None, label: str) -> bool:
        if language:
            return self._clean_language(base_path, language, label)
        return self._clean_all(base_path, label)

    def _clean_language(self, base_path: Path, language: str, label: str) -> bool:
        target_dir = base_path / language
        if not target_dir.exists():
            print(f"⏭️  Directory not found: {target_dir}")
            print(f"Nothing to clean for {language.title()} {label.lower()}")
            return True

        if self._is_empty(target_dir.iterdir()):
            print(f"📭 Directory is already empty: {target_dir}")
            return True

        print(f"🧹 Cleaning {language.title()} {label}...")
        return self._remove_contents(target_dir, language_title=language.title(), label=label)

    def _clean_all(self, base_path: Path, label: str) -> bool:
        if not base_path.exists():
            print(f"⏭️  Directory not found: {base_path}")
            print(f"Nothing to clean for {label.lower()}")
            return True

        if self._is_empty(base_path.iterdir()):
            print(f"📭 Directory is already empty: {base_path}")
            return True

        languages = [d.name.title() for d in base_path.iterdir() if d.is_dir() and d.name in SUPPORTED_LANGUAGES]
        if languages:
            print(f"🌍 Language directories: {', '.join(languages)}")

        print(f"🧹 Cleaning ALL {label}...")
        return self._remove_contents(base_path, language_title=None, label=label)

    def _remove_contents(self, path: Path, *, language_title: str | None, label: str) -> bool:
        files = list(path.rglob("*"))
        file_count = len([entry for entry in files if entry.is_file()])
        dir_count = len([entry for entry in files if entry.is_dir()])
        print(f"Found: {file_count} files, {dir_count} subdirectories")

        try:
            for item in path.iterdir():
                if item.is_file():
                    item.unlink()
                else:
                    shutil.rmtree(item)

            scope = f"{language_title} {label.lower()}" if language_title else f"ALL {label.lower()}"
            print(f"✓ Successfully cleaned {scope}")
            print(f"Removed {file_count} files and {dir_count} subdirectories")
            return True
        except Exception as exc:  # noqa: BLE001 - user needs to see cleanup issues
            scope = f"{language_title} {label.lower()}" if language_title else f"ALL {label.lower()}"
            print(f"❌ Error cleaning {scope}: {exc}")
            return False

    @staticmethod
    def _is_empty(entries: Iterable[Path]) -> bool:
        return not any(True for _ in entries)

    # ------------------------------------------------------------------
    # Issues cleanup helpers

    def _clean_related_issues(self, language: str | None) -> None:
        if not self.issues_dir.exists():
            return

        if language is None:
            print("🪣 Removing all cached issues to mirror evaluation cleanup…")
            try:
                shutil.rmtree(self.issues_dir)
                print("✓ Issues cache removed")
            except FileNotFoundError:
                pass
            return

        language_key = language.lower()
        print(f"🧽 Removing issues cached for {language.title()}…")
        self._remove_combined_issue_files(language_key)
        self._remove_pattern_files(language_key)
        self._prune_aggregated_issues(language_key)

    def _remove_combined_issue_files(self, language: str) -> None:
        combined_dir = self.issues_dir / "combined_issues"
        if not combined_dir.exists():
            return

        # Remove label-aware directories
        for label_dir in combined_dir.glob("*"):
            if not label_dir.is_dir():
                continue
            target = label_dir / f"{language}_issues.json"
            if target.exists():
                target.unlink()
            if self._is_empty(label_dir.iterdir()):
                try:
                    label_dir.rmdir()
                except OSError:
                    pass

        if self._is_empty(combined_dir.iterdir()):
            try:
                combined_dir.rmdir()
            except OSError:
                pass

    def _remove_pattern_files(self, language: str) -> None:
        patterns_dir = self.issues_dir / "common_patterns"
        if not patterns_dir.exists():
            return

        for label_dir in patterns_dir.glob("*"):
            if label_dir.is_dir():
                target = label_dir / f"{language}.json"
                if target.exists():
                    target.unlink()
                if self._is_empty(label_dir.iterdir()):
                    try:
                        label_dir.rmdir()
                    except OSError:
                        pass

        if self._is_empty(patterns_dir.iterdir()):
            try:
                patterns_dir.rmdir()
            except OSError:
                pass

    def _prune_aggregated_issues(self, language: str) -> None:
        all_dir = self.issues_dir / "all"
        all_file = all_dir / "all_common_issues.json"
        if not all_file.exists():
            return

        try:
            with open(all_file, "r", encoding="utf-8") as handle:
                data = json.load(handle)
        except (OSError, json.JSONDecodeError):
            try:
                all_file.unlink()
            except FileNotFoundError:
                pass
            return

        changed = False

        # Only support label-based format
        if isinstance(data, dict) and isinstance(data.get("labels"), dict):
            labels: dict[str, dict] = data["labels"]
            to_delete: list[str] = []

            for key, entry in list(labels.items()):
                if not isinstance(entry, dict):
                    continue
                entry_changed = False
                analyses = entry.get("analyses")
                if isinstance(analyses, dict) and language in analyses:
                    del analyses[language]
                    entry_changed = True

                languages_field = entry.get("languages")
                if isinstance(languages_field, list) and language in languages_field:
                    entry["languages"] = [
                        lang for lang in languages_field if lang != language
                    ]
                    entry_changed = True

                if isinstance(analyses, dict) and not analyses:
                    to_delete.append(key)

                if entry_changed:
                    changed = True

            for key in to_delete:
                labels.pop(key, None)
                changed = True

            if labels:
                if data.get("latest_label") not in labels:
                    data["latest_label"] = next(iter(labels.keys()))
            else:
                data = None

        if not changed:
            return

        if data:
            with open(all_file, "w", encoding="utf-8") as handle:
                json.dump(data, handle, ensure_ascii=False, indent=2)
        else:
            try:
                all_file.unlink()
            except FileNotFoundError:
                pass
            if all_dir.exists() and self._is_empty(all_dir.iterdir()):
                try:
                    all_dir.rmdir()
                except OSError:
                    pass
