"""Issue aggregation utilities for evaluation outputs."""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

from utils.labels import sanitize_label


def aggregate_issues(languages: Iterable[str] | None = None, *, label: str, base_dir: Path | str = ".") -> List[str]:
    """Aggregate linguistic and localization issues per language.

    Args:
        languages: Languages to process. If None, discovers languages automatically.
        label: Version label for tracking (e.g., v1, prod, test).
        base_dir: Base directory (default: current directory).

    Returns:
        List of successfully processed language names.
    """
    base_path = Path(base_dir)
    eval_results_dir = base_path / "eval_results"
    issues_dir = base_path / "issues"
    combined_dir = issues_dir / "combined_issues"

    label_key = sanitize_label(label)

    languages_to_process = list(languages or _discover_languages(eval_results_dir, label, label_key))
    processed: List[str] = []

    if not languages_to_process:
        print(f"⚠️  No languages found with evaluation results for label '{label}'.")
        return processed

    label_dir = combined_dir / label_key
    label_dir.mkdir(parents=True, exist_ok=True)

    for language in languages_to_process:
        result = _collect_language_issues(eval_results_dir, language, label, label_key)
        if result is None:
            continue

        combined, sources = result
        metadata = {
            "label": label,
            "language": language,
            "generated_at": datetime.now().isoformat(),
            "source_files": sources,
            "issue_counts": {name: len(items) for name, items in combined.items()},
        }

        payload = {"metadata": metadata, "issues": combined}
        output_file = label_dir / f"{language}_issues.json"
        with open(output_file, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, ensure_ascii=False, indent=2)
        print(f"Aggregated issues for {language} (label: {label})")
        processed.append(language)

    return processed


def _discover_languages(eval_results_dir: Path, label: str, label_key: str) -> List[str]:
    """Discover languages that have evaluation results for the given label."""
    if not eval_results_dir.exists():
        return []

    languages: List[str] = []
    for path in sorted(eval_results_dir.iterdir()):
        if path.is_dir() and _language_has_label(path, label):
            languages.append(path.name)
    return languages


def _collect_language_issues(
    eval_results_dir: Path, language: str, label: str, label_key: str
) -> Optional[Tuple[Dict[str, List[Dict]], List[str]]]:
    """Collect and combine issues from all evaluation files for a language."""
    language_dir = eval_results_dir / language
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
        label_matches = metadata.get("label") == label
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
        print(f"⏭️  Skipping {language} - no evaluation results with label '{label}'")
        return None

    return combined, matched_files


def _language_has_label(language_dir: Path, label: str) -> bool:
    """Check if a language directory has any evaluation files with the given label."""
    for json_file in language_dir.glob("*.json"):
        try:
            with open(json_file, "r", encoding="utf-8") as handle:
                data = json.load(handle)
        except (OSError, json.JSONDecodeError):
            continue

        metadata = data.get("metadata", {})
        if metadata.get("label") == label:
            return True

    return False
