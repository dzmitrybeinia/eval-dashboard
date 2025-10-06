"""Issue aggregation utilities for evaluation outputs."""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

from utils.labels import LabelInfo, ensure_label


class IssueAggregator:
    """Aggregate linguistic and localization issues per language."""

    def __init__(self, base_dir: Path | str = ".") -> None:
        base_path = Path(base_dir)
        self.eval_results_dir = base_path / "eval_results"
        self.issues_dir = base_path / "issues"
        self.combined_dir = self.issues_dir / "combined_issues"

    def aggregate(self, languages: Iterable[str] | None = None, *, label: LabelInfo | str) -> List[str]:
        label_info = ensure_label(label)

        languages_to_process = list(languages or self._discover_languages(label_info))
        processed: List[str] = []

        if not languages_to_process:
            print(f"⚠️  No languages found with evaluation results for label '{label_info.original}'.")
            return processed

        label_dir = self.combined_dir / label_info.key
        label_dir.mkdir(parents=True, exist_ok=True)

        for language in languages_to_process:
            result = self._collect_language_issues(language, label_info)
            if result is None:
                continue

            combined, sources = result
            metadata = {
                "label": label_info.original,
                "language": language,
                "generated_at": datetime.now().isoformat(),
                "source_files": sources,
                "issue_counts": {name: len(items) for name, items in combined.items()},
            }

            payload = {"metadata": metadata, "issues": combined}
            output_file = label_dir / f"{language}_issues.json"
            with open(output_file, "w", encoding="utf-8") as handle:
                json.dump(payload, handle, ensure_ascii=False, indent=2)
            print(f"Aggregated issues for {language} (label: {label_info.original})")
            processed.append(language)

        return processed

    def _discover_languages(self, label: LabelInfo) -> List[str]:
        if not self.eval_results_dir.exists():
            return []

        languages: List[str] = []
        for path in sorted(self.eval_results_dir.iterdir()):
            if path.is_dir() and self._language_has_label(path, label):
                languages.append(path.name)
        return languages

    def _collect_language_issues(self, language: str, label: LabelInfo) -> Optional[Tuple[Dict[str, List[Dict]], List[str]]]:
        language_dir = self.eval_results_dir / language
        if not language_dir.exists():
            print(f"⏭️  Skipping {language} - no evaluation results")
            return None

        combined: Dict[str, List[Dict]] = {"linguistic": [], "localization": []}
        matched_files: List[str] = []

        for json_file in sorted(language_dir.glob("*.json")):
            try:
                with open(json_file, "r", encoding="utf-8") as handle:
                    data = json.load(handle)
            except (OSError, json.JSONDecodeError) as exc:
                print(f"⚠️  Skipping {json_file.name} ({exc})")
                continue

            metadata = data.get("metadata", {})
            label_matches = metadata.get("label") == label.original
            if not label_matches:
                continue

            matched_files.append(json_file.name)
            issues_payload = data.get("issues", [])

            if isinstance(issues_payload, dict):
                for category, entries in issues_payload.items():
                    if category in combined and isinstance(entries, list):
                        combined[category].extend(entries)
                continue

            if not isinstance(issues_payload, list):
                continue

            for issue in issues_payload:
                if not isinstance(issue, dict):
                    continue
                category = issue.get("category")
                if category in combined:
                    combined[category].append(issue)

        if not matched_files:
            print(f"⏭️  Skipping {language} - no evaluation results with label '{label.original}'")
            return None

        return combined, matched_files

    def _language_has_label(self, language_dir: Path, label: LabelInfo) -> bool:
        for json_file in language_dir.glob("*.json"):
            try:
                with open(json_file, "r", encoding="utf-8") as handle:
                    data = json.load(handle)
            except (OSError, json.JSONDecodeError):
                continue

            metadata = data.get("metadata", {})
            if metadata.get("label") == label.original:
                return True

        return False
