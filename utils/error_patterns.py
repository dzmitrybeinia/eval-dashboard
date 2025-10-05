"""Error pattern analysis helpers using Azure OpenAI."""

from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Iterable, List, Optional

from dotenv import load_dotenv
from openai import AzureOpenAI

from .labels import LabelInfo, ensure_label, sanitize_label


class ErrorPatternAnalyzer:
    """Generate cross-language error pattern reports."""

    SEVERITIES = ("HIGH", "MEDIUM", "MINOR")
    CATEGORIES = ("linguistic", "localization")

    def __init__(
        self,
        base_dir: Path | str = ".",
        prompt_path: Path | str = "prompts/pattern_analysis/error_pattern_analysis.md",
    ) -> None:
        load_dotenv()
        self.base_path = Path(base_dir)
        self.issues_dir = self.base_path / "issues"
        self.output_dir = self.issues_dir / "all"
        self.patterns_dir = self.issues_dir / "common_patterns"
        self.prompt_path = Path(prompt_path)
        self.prompt_template = self._load_prompt()
        self.client = AzureOpenAI(
            azure_endpoint=self._require_env("ENDPOINT_URL"),
            api_key=self._require_env("AZURE_OPENAI_API_KEY"),
            api_version=os.getenv("API_VERSION", "2025-01-01-preview"),
        )
        self.deployment = os.getenv("DEPLOYMENT_NAME", "o3-mini")

    def analyze(
        self, languages: Iterable[str] | None = None, *, label: LabelInfo | str
    ) -> List[str]:
        label_info = ensure_label(label)

        languages_to_process = list(languages or self._discover_languages(label_info))
        if not languages_to_process:
            print(
                f"⚠️  No aggregated issues found for label '{label_info.original}'."
            )
            return []

        processed: List[str] = []
        analyses: Dict[str, Dict] = {}

        for language in languages_to_process:
            combined_issues = self._load_combined_issues(language, label_info)
            if combined_issues is None:
                continue

            reports = self._analyze_language(language, combined_issues)
            merged = self._merge(reports)
            analyses[language] = merged
            self._write_language_report(language, merged, label_info)
            processed.append(language)

        if analyses:
            self._write_global_report(analyses, label_info)

        return processed

    def _analyze_language(self, language: str, combined_issues: Dict[str, List[Dict]]) -> List[Dict]:
        reports: List[Dict] = []
        for category in self.CATEGORIES:
            for severity in self.SEVERITIES:
                issues = [
                    issue
                    for issue in combined_issues.get(category, [])
                    if issue.get("severity", "MEDIUM") == severity
                ]
                if not issues:
                    continue
                report = self._call_model(language, category, severity, issues)
                if report:
                    reports.append(report)
        return reports

    def _call_model(
        self,
        language: str,
        category: str,
        severity: str,
        issues: List[Dict],
    ) -> Optional[Dict]:
        prompt = (
            f"{self.prompt_template}\n\n"
            f"**Target language:** {language.title()}\n"
            f"**Pattern focus:** {category} issues with {severity} severity\n"
            f"**Issue count:** {len(issues)}\n\n"
            f"**Issues to analyse:**\n{json.dumps(issues, ensure_ascii=False, indent=2)}"
        )

        response = self.client.chat.completions.create(
            model=self.deployment,
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

    def _merge(self, reports: List[Dict]) -> Dict:
        if not reports:
            return {}

        merged_patterns = self._merge_patterns(reports)
        return {"top_error_patterns": merged_patterns}

    @staticmethod
    def _merge_patterns(reports: List[Dict]) -> List[Dict]:
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

    def _write_language_report(
        self, language: str, report: Dict, label: LabelInfo
    ) -> None:
        label_dir = self.patterns_dir / label.key
        label_dir.mkdir(parents=True, exist_ok=True)
        payload = {
            "metadata": {
                "label": label.original,
                "language": language,
                "generated_at": datetime.now().isoformat(),
            },
            "top_error_patterns": report.get("top_error_patterns", []),
        }
        out_path = label_dir / f"{language}.json"
        with open(out_path, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, ensure_ascii=False, indent=2)
        print(f"📄 Saved analysis for {language} (label: {label.original})")

    def _write_global_report(self, analyses: Dict[str, Dict], label: LabelInfo) -> None:
        self.output_dir.mkdir(parents=True, exist_ok=True)
        out_path = self.output_dir / "all_common_issues.json"

        payload: Dict[str, object] = {"labels": {}, "latest_label": label.key}

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

        existing_entry = labels_dict.get(label.key)
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

        labels_dict[label.key] = {
            "label": label.original,
            "generated_at": datetime.now().isoformat(),
            "languages": sorted(languages),
            "analyses": merged_analyses,
        }
        payload["latest_label"] = label.key

        with open(out_path, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, ensure_ascii=False, indent=2)
        print(f"🌍 Saved aggregated common issues report (label: {label.original})")

    def _load_prompt(self) -> str:
        try:
            return self.prompt_path.read_text(encoding="utf-8")
        except FileNotFoundError as exc:
            raise FileNotFoundError(f"Error pattern prompt not found: {self.prompt_path}") from exc

    def _load_combined_issues(
        self, language: str, label: LabelInfo
    ) -> Optional[Dict[str, List[Dict]]]:
        combined_base = self.issues_dir / "combined_issues"
        candidates = [combined_base / label.key / f"{language}_issues.json"]

        # Fallback for legacy structure without label directories
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
            if stored_label and stored_label != label.original:
                continue

            issues_payload = data.get("issues") if isinstance(data, dict) else None
            if isinstance(issues_payload, dict):
                return issues_payload
            if isinstance(data, dict):
                return {
                    key: value
                    for key, value in data.items()
                    if isinstance(value, list) and key in self.CATEGORIES
                }
            return data

        print(
            f"⏭️  Skipping {language} - run issue aggregation for label '{label.original}' first"
        )
        return None

    def _discover_languages(self, label: LabelInfo) -> List[str]:
        label_dir = self.issues_dir / "combined_issues" / label.key
        if not label_dir.exists():
            return []
        languages = [
            path.stem.replace("_issues", "")
            for path in sorted(label_dir.glob("*_issues.json"))
        ]
        return languages

    @staticmethod
    def _require_env(name: str) -> str:
        value = os.getenv(name)
        if not value:
            raise ValueError(f"{name} environment variable is required. Please check your .env file.")
        return value


__all__ = ["ErrorPatternAnalyzer"]
