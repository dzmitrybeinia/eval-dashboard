"""Error pattern analysis helpers using Azure OpenAI."""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Iterable, List, Optional

from dotenv import load_dotenv
from openai import AzureOpenAI

from utils.labels import sanitize_label

load_dotenv()

SEVERITIES = ("HIGH", "MEDIUM", "MINOR")
CATEGORIES = ("linguistic", "localization")


def analyze_patterns(
    languages: Iterable[str] | None = None,
    *,
    label: str,
    base_dir: Path | str = ".",
    prompt_path: Path | str = "prompts/pattern_analysis/error_pattern_analysis.md",
) -> List[str]:
    """Generate cross-language error pattern reports.

    Args:
        languages: Languages to process. If None, discovers languages automatically.
        label: Version label for tracking (e.g., v1, prod, test).
        base_dir: Base directory (default: current directory).
        prompt_path: Path to the pattern analysis prompt template.

    Returns:
        List of successfully processed language names.
    """
    base_path = Path(base_dir)
    issues_dir = base_path / "issues"
    patterns_dir = issues_dir / "common_patterns"
    output_dir = issues_dir / "all"

    label_key = sanitize_label(label)
    prompt_template = _load_prompt(Path(prompt_path))
    client = _create_client()
    deployment = os.getenv("DEPLOYMENT_NAME", "o3-mini")

    languages_to_process = list(languages or _discover_languages(issues_dir, label_key))
    if not languages_to_process:
        print(f"⚠️  No aggregated issues found for label '{label}'.")
        return []

    processed: List[str] = []
    analyses: Dict[str, Dict] = {}

    for language in languages_to_process:
        combined_issues = _load_combined_issues(issues_dir, language, label, label_key)
        if combined_issues is None:
            continue

        reports = _analyze_language(language, combined_issues, prompt_template, client, deployment)
        merged = _merge_reports(reports)
        analyses[language] = merged
        _write_language_report(patterns_dir, language, merged, label, label_key)
        processed.append(language)

    if analyses:
        _write_global_report(output_dir, analyses, label, label_key)

    return processed


def _create_client() -> AzureOpenAI:
    """Create and return an Azure OpenAI client."""
    return AzureOpenAI(
        azure_endpoint=_require_env("ENDPOINT_URL"),
        api_key=_require_env("AZURE_OPENAI_API_KEY"),
        api_version=os.getenv("API_VERSION", "2025-01-01-preview"),
    )


def _analyze_language(
    language: str,
    combined_issues: Dict[str, List[Dict]],
    prompt_template: str,
    client: AzureOpenAI,
    deployment: str,
) -> List[Dict]:
    """Analyze issues for a single language across all categories and severities."""
    reports: List[Dict] = []
    for category in CATEGORIES:
        for severity in SEVERITIES:
            issues = [
                issue
                for issue in combined_issues.get(category, [])
                if issue.get("severity", "MEDIUM") == severity
            ]
            if not issues:
                continue
            report = _call_model(language, category, severity, issues, prompt_template, client, deployment)
            if report:
                reports.append(report)
    return reports


def _call_model(
    language: str,
    category: str,
    severity: str,
    issues: List[Dict],
    prompt_template: str,
    client: AzureOpenAI,
    deployment: str,
) -> Optional[Dict]:
    """Call the AI model to analyze a set of issues."""
    prompt = f"{prompt_template}\n\n**Target language:** {language.title()}\n**Pattern focus:** {category} issues with {severity} severity\n**Issue count:** {len(issues)}\n\n**Issues to analyse:**\n{json.dumps(issues, ensure_ascii=False, indent=2)}"

    response = client.chat.completions.create(
        model=deployment,
        messages=[
            {
                "role": "system",
                "content": "You are a localization quality expert. Return only valid JSON without markdown.",
            },
            {"role": "user", "content": prompt},
        ],
        max_completion_tokens=16_384,
        temperature=0.0,
    )
    content = response.choices[0].message.content.strip()

    try:
        return json.loads(content)
    except json.JSONDecodeError:
        try:
            cleaned = content.strip().strip("`")
            return json.loads(cleaned)
        except json.JSONDecodeError:
            print(f"⚠️  Failed to parse model output for {language} ({category}/{severity})")
            return None


def _merge_reports(reports: List[Dict]) -> Dict:
    """Merge multiple pattern reports into a single report."""
    if not reports:
        return {}

    merged_patterns = _merge_patterns(reports)
    return {"top_error_patterns": merged_patterns}


def _merge_patterns(reports: List[Dict]) -> List[Dict]:
    """Merge and deduplicate patterns from multiple reports."""
    deduped: Dict[tuple[str, str], Dict] = {}
    severity_priority = {"HIGH": 3, "MEDIUM": 2, "LOW": 1}
    frequency_priority = {"very_common": 4, "common": 3, "occasional": 2, "rare": 1}

    for report in reports:
        for pattern in report.get("top_error_patterns", []):
            name = pattern.get("pattern_name", "").strip()
            category = pattern.get("category", "")
            if not name:
                continue

            key = (name, category)
            frequency_count = pattern.get("frequency_count")
            try:
                frequency_count = int(frequency_count)
            except (TypeError, ValueError):
                frequency_count = 0

            entry = deduped.get(key)
            if entry is None:
                new_entry = {
                    "pattern_name": name,
                    "category": category,
                    "subcategory": pattern.get("subcategory", ""),
                    "impact_level": pattern.get("impact_level", "MEDIUM"),
                    "frequency": pattern.get("frequency", "common"),
                    "frequency_count": frequency_count,
                    "description": pattern.get("description", ""),
                    "examples": pattern.get("examples", []) or [],
                }
                deduped[key] = new_entry
                continue

            entry["frequency_count"] += frequency_count

            current_severity = entry.get("impact_level", "MEDIUM")
            new_severity = pattern.get("impact_level", "MEDIUM")
            if severity_priority.get(new_severity, 2) > severity_priority.get(current_severity, 2):
                entry["impact_level"] = new_severity

            current_freq = entry.get("frequency", "common")
            new_freq = pattern.get("frequency", current_freq)
            if frequency_priority.get(new_freq, 0) > frequency_priority.get(current_freq, 0):
                entry["frequency"] = new_freq

            if not entry.get("description") and pattern.get("description"):
                entry["description"] = pattern.get("description", "")

            examples = pattern.get("examples", []) or []
            if examples:
                existing_examples = {json.dumps(ex, sort_keys=True) for ex in entry.get("examples", [])}
                for example in examples:
                    serialized = json.dumps(example, sort_keys=True)
                    if serialized not in existing_examples:
                        entry.setdefault("examples", []).append(example)
                        existing_examples.add(serialized)

    patterns = list(deduped.values())
    patterns.sort(
        key=lambda p: (
            severity_priority.get(p.get("impact_level", "MEDIUM"), 0),
            p.get("frequency_count", 0),
        ),
        reverse=True,
    )
    return patterns


def _write_language_report(patterns_dir: Path, language: str, report: Dict, label: str, label_key: str) -> None:
    """Write pattern analysis report for a single language."""
    label_dir = patterns_dir / label_key
    label_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        "metadata": {
            "label": label,
            "language": language,
            "generated_at": datetime.now().isoformat(),
        },
        "top_error_patterns": report.get("top_error_patterns", []),
    }
    out_path = label_dir / f"{language}.json"
    with open(out_path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)
    print(f"📄 Saved analysis for {language} (label: {label})")


def _write_global_report(output_dir: Path, analyses: Dict[str, Dict], label: str, label_key: str) -> None:
    """Write the global aggregated report with all languages and labels."""
    output_dir.mkdir(parents=True, exist_ok=True)
    out_path = output_dir / "all_common_issues.json"

    payload: Dict[str, object] = {"labels": {}, "latest_label": label_key}

    # Load existing data (label-based format only)
    if out_path.exists():
        try:
            with open(out_path, "r", encoding="utf-8") as handle:
                existing = json.load(handle)
            if isinstance(existing, dict) and isinstance(existing.get("labels"), dict):
                payload = existing
        except (OSError, json.JSONDecodeError):
            pass

    labels_dict = payload.setdefault("labels", {})
    if not isinstance(labels_dict, dict):
        labels_dict = {}
        payload["labels"] = labels_dict

    existing_entry = labels_dict.get(label_key)
    merged_analyses: Dict[str, Dict]
    if isinstance(existing_entry, dict) and isinstance(existing_entry.get("analyses"), dict):
        merged_analyses = dict(existing_entry["analyses"])
        merged_analyses.update(analyses)
        existing_languages = existing_entry.get("languages", [])
        if isinstance(existing_languages, list):
            languages = {str(lang).lower() for lang in existing_languages}
        else:
            languages = set()
    else:
        merged_analyses = dict(analyses)
        languages = set()

    languages.update(lang.lower() for lang in analyses.keys())

    labels_dict[label_key] = {
        "label": label,
        "generated_at": datetime.now().isoformat(),
        "languages": sorted(languages),
        "analyses": merged_analyses,
    }
    payload["latest_label"] = label_key

    with open(out_path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)
    print(f"🌍 Saved aggregated common issues report (label: {label})")


def _load_prompt(prompt_path: Path) -> str:
    """Load the prompt template from file."""
    try:
        return prompt_path.read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise FileNotFoundError(f"Error pattern prompt not found: {prompt_path}") from exc


def _load_combined_issues(issues_dir: Path, language: str, label: str, label_key: str) -> Optional[Dict[str, List[Dict]]]:
    """Load combined issues for a language and label."""
    combined_base = issues_dir / "combined_issues"
    candidates = [combined_base / label_key / f"{language}_issues.json"]
    candidates.append(combined_base / f"{language}_issues.json")

    for combined_path in candidates:
        if not combined_path.exists():
            continue
        try:
            with open(combined_path, "r", encoding="utf-8") as handle:
                data = json.load(handle)
        except (OSError, json.JSONDecodeError) as exc:
            print(f"⚠️  Could not read {combined_path.name}: {exc}")
            continue

        metadata = data.get("metadata", {}) if isinstance(data, dict) else {}
        stored_label = metadata.get("label")
        if stored_label and stored_label != label:
            continue

        issues_payload = data.get("issues") if isinstance(data, dict) else None
        if isinstance(issues_payload, dict):
            return issues_payload
        if isinstance(data, dict):
            return {
                key: value
                for key, value in data.items()
                if isinstance(value, list) and key in CATEGORIES
            }
        return data

    print(f"⏭️  Skipping {language} - run issue aggregation for label '{label}' first")
    return None


def _discover_languages(issues_dir: Path, label_key: str) -> List[str]:
    """Discover languages that have combined issues for the given label."""
    label_dir = issues_dir / "combined_issues" / label_key
    if not label_dir.exists():
        return []
    languages = [
        path.stem.replace("_issues", "")
        for path in sorted(label_dir.glob("*_issues.json"))
    ]
    return languages


def _require_env(name: str) -> str:
    """Get a required environment variable or raise an error."""
    value = os.getenv(name)
    if not value:
        raise ValueError(f"{name} environment variable is required. Please check your .env file.")
    return value
