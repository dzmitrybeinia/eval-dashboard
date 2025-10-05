"""Evaluation helpers built on Azure OpenAI - refactored version."""

from __future__ import annotations

import json
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from openai import AzureOpenAI

from config import API_KEY, API_VERSION, DEPLOYMENT_NAME, ENDPOINT_URL
from orchestrators.base import AbstractOrchestrator

from .error_patterns import ErrorPatternAnalyzer
from .issues import IssueAggregator
from .labels import LabelInfo, ensure_label


class SimpleScorer:
    """Calculate weighted scores based on issue severities."""

    def __init__(self, base_score: float = 10.0) -> None:
        self.base_score = base_score
        self.severity_multipliers = {
            "HIGH": 0.3,
            "MEDIUM": 0.2,
            "MINOR": 0.1,
        }

    def calculate_score(self, issues_list: List[Dict]) -> Dict:
        if not issues_list:
            return {
                "overall_quality_score": self.base_score,
                "classification": "NATIVE",
                "total_issues": 0,
                "total_penalty": 0.0,
                "issue_breakdown": {
                    "linguistic": 0,
                    "localization": 0,
                    "distractor_quality": 0,
                },
                "penalty_breakdown": {
                    "linguistic_penalty": 0.0,
                    "localization_penalty": 0.0,
                    "distractor_quality_penalty": 0.0,
                },
            }

        penalties = {
            "linguistic": 0.0,
            "localization": 0.0,
            "distractor_quality": 0.0,
        }
        counts = {
            "linguistic": 0,
            "localization": 0,
            "distractor_quality": 0,
        }

        for issue in issues_list:
            category = issue.get("category", "linguistic")
            severity = issue.get("severity", "MEDIUM")
            if category not in penalties:
                continue

            counts[category] += 1
            penalties[category] += self.severity_multipliers.get(severity, 0.2)

        total_penalty = sum(penalties.values())
        score = max(0.0, self.base_score - total_penalty)

        return {
            "overall_quality_score": round(score, 1),
            "classification": self._classify(score),
            "total_issues": sum(counts.values()),
            "total_penalty": round(total_penalty, 1),
            "issue_breakdown": counts,
            "penalty_breakdown": {
                "linguistic_penalty": round(penalties["linguistic"], 1),
                "localization_penalty": round(penalties["localization"], 1),
                "distractor_quality_penalty": round(penalties["distractor_quality"], 1),
            },
        }

    @staticmethod
    def _classify(score: float) -> str:
        if score >= 9.0:
            return "NATIVE"
        if score >= 8.0:
            return "PROFESSIONAL"
        if score >= 7.0:
            return "ACCEPTABLE"
        if score >= 6.0:
            return "SUBSTANDARD"
        if score >= 5.0:
            return "POOR"
        return "UNACCEPTABLE"


class QuizEvaluator:
    """Run localization quality evaluation over markdown quizzes."""

    def __init__(
        self,
        orchestrator: AbstractOrchestrator,
        markdown_dir: Path,
        eval_results_dir: Path,
        base_dir: Path | str = ".",
    ) -> None:
        """
        Initialize evaluator with orchestrator and paths.

        Args:
            orchestrator: Orchestrator instance for prompt building and pipeline control
            markdown_dir: Directory containing markdown files to evaluate
            eval_results_dir: Directory where evaluation results should be saved
            base_dir: Base directory for issues/patterns (default: current directory)
        """
        # Azure OpenAI client
        if not ENDPOINT_URL or not API_KEY:
            raise ValueError(
                "ENDPOINT_URL and AZURE_OPENAI_API_KEY environment variables are required. "
                "Please check your .env file."
            )

        self.client = AzureOpenAI(
            azure_endpoint=ENDPOINT_URL,
            api_key=API_KEY,
            api_version=API_VERSION,
        )
        self.deployment = DEPLOYMENT_NAME  # gpt-4.1

        # Paths
        self.markdown_dir = Path(markdown_dir)
        self.eval_results_dir = Path(eval_results_dir)
        self.base_path = Path(base_dir)

        # Orchestrator controls the pipeline
        self.orchestrator = orchestrator

        # Helper services
        self.scorer = SimpleScorer()
        self.issue_aggregator = IssueAggregator(self.base_path)
        self.pattern_analyzer = ErrorPatternAnalyzer(base_dir=self.base_path)

    def evaluate_language(self, language: str, label: LabelInfo | str) -> bool:
        """Evaluate all markdown files for a specific language."""
        label_info = ensure_label(label)
        source_dir = self.markdown_dir / language
        if not source_dir.exists():
            print(f"❌ Markdown directory not found: {source_dir}")
            return False

        language_dir = self.eval_results_dir / language
        language_dir.mkdir(parents=True, exist_ok=True)

        md_files = sorted(source_dir.glob("*.md"))
        if not md_files:
            print(f"❌ No markdown files found in {source_dir}")
            return False

        print(f"📁 Found {len(md_files)} markdown file(s) in {source_dir}")
        print(f"Using label: {label_info.original}")
        evaluated = 0

        for md_file in md_files:
            print(f"Evaluating {md_file.name}...")
            if self.evaluate_file(md_file, language, label_info):
                evaluated += 1
                print(f"✓ Evaluated {md_file.name}")
            else:
                print(f"❌ Failed to evaluate {md_file.name}")

        print("\nEvaluation Summary:")
        print(f"   ✓ Evaluated: {evaluated}")
        print(f"   Total files: {len(md_files)}")

        success = evaluated > 0
        if success:
            self._refresh_file_index()
            # Don't auto-run aggregation/patterns - caller should call explicitly
        return success

    def evaluate_file(self, md_file: Path, language: str, label: LabelInfo) -> bool:
        """Evaluate a single markdown file."""
        try:
            with open(md_file, "r", encoding="utf-8") as handle:
                content = handle.read()
        except OSError as exc:
            print(f"Error reading {md_file}: {exc}")
            return False

        # Use orchestrator to build evaluation prompt
        prompt = self.orchestrator.build_evaluation_prompt(content, language)

        # Determine system message based on language
        if language.lower() == "english":
            system_content = (
                "You are an expert educational content evaluator specializing in quiz quality "
                "assessment and localization review. You must return only valid JSON without any additional text."
            )
        else:
            system_content = (
                "You are a specialized dual-expertise evaluator combining both linguistic accuracy and "
                "localization quality assessment. Apply deduplication rules strictly. Return only valid JSON "
                "without any additional text."
            )

        # Call LLM
        response = self.client.chat.completions.create(
            model=self.deployment,
            messages=[
                {"role": "system", "content": system_content},
                {"role": "user", "content": prompt},
            ],
            max_completion_tokens=32_768,
            temperature=0.0,
        )
        result = response.choices[0].message.content.strip()

        if not result:
            return False

        evaluation_json = self._parse_response(result, md_file, language, label)
        if not evaluation_json:
            return False

        self._persist_evaluation(evaluation_json, language)
        return True

    def run_aggregation(self, languages: List[str], label: LabelInfo | str) -> bool:
        """
        Run issue aggregation for specified languages.
        This should be called explicitly after evaluation.
        """
        label_info = ensure_label(label)
        if not languages:
            return False

        try:
            aggregated = self.issue_aggregator.aggregate(languages, label=label_info)
        except Exception as exc:
            print(f"⚠️  Issue aggregation failed for label '{label_info.original}': {exc}")
            return False

        return bool(aggregated)

    def run_pattern_analysis(self, languages: List[str], label: LabelInfo | str) -> bool:
        """
        Run error pattern analysis for specified languages.
        This should be called explicitly after aggregation.
        """
        label_info = ensure_label(label)
        if not languages:
            return False

        try:
            processed = self.pattern_analyzer.analyze(languages, label=label_info)
        except Exception as exc:
            print(f"⚠️  Issue pattern analysis failed for label '{label_info.original}': {exc}")
            return False

        return bool(processed)

    def refresh_file_index(self) -> None:
        """Rebuild the dashboard file index without running evaluations."""
        self._refresh_file_index()

    def _refresh_file_index(self) -> None:
        index_data = self._build_file_index()
        if not index_data:
            return

        index_path = self.eval_results_dir.parent / "file_index.json"
        with open(index_path, "w", encoding="utf-8") as handle:
            json.dump(index_data, handle, indent=2, ensure_ascii=False)
        print(f"📄 Updated file index: {index_path.name}")

    def _build_file_index(self) -> Optional[Dict[str, object]]:
        if not self.eval_results_dir.exists():
            return None

        language_files: Dict[str, List[str]] = {}
        total_files = 0

        for language_dir in sorted(self.eval_results_dir.iterdir()):
            if not language_dir.is_dir():
                continue

            files_with_mtime: List[tuple[str, float]] = []
            for json_file in language_dir.glob("*.json"):
                if not json_file.is_file():
                    continue
                try:
                    mtime = json_file.stat().st_mtime
                except OSError:
                    mtime = 0
                files_with_mtime.append((json_file.name, mtime))

            if files_with_mtime:
                files_with_mtime.sort(key=lambda item: item[1], reverse=True)
                language_files[language_dir.name] = [name for name, _ in files_with_mtime]
                total_files += len(files_with_mtime)

        return {
            "generated_at": datetime.now().isoformat(),
            "total_files": total_files,
            "languages": sorted(language_files.keys()),
            "files": language_files,
        }

    def _parse_response(
        self,
        response_text: str,
        md_file: Path,
        language: str,
        label: LabelInfo,
    ) -> Optional[Dict]:
        cleaned = self._clean_json_response(response_text)
        try:
            evaluation_json = json.loads(cleaned)
        except json.JSONDecodeError as err:
            print(f"⚠️  JSON parsing failed: {err}")
            print(f"Raw response (first 500 chars): {response_text[:500]}...")
            print(f"Raw response (last 200 chars): ...{response_text[-200:]}")
            print(f"🧹 Cleaned response length: {len(cleaned)} chars")
            evaluation_json = self._fallback_parse(response_text)
            if evaluation_json is None:
                print("❌ All JSON extraction attempts failed")
                return None
            print("✓ Successfully extracted JSON using fallback strategy")

        if "issues" not in evaluation_json or not isinstance(
            evaluation_json["issues"], list
        ):
            print("⚠️  Invalid format: 'issues' must be an array")
            return None

        evaluation_json.setdefault("metadata", {})
        metadata = evaluation_json["metadata"]
        metadata.update(
            {
                "file": md_file.name,
                "language": language.title(),
                "timestamp": datetime.now().isoformat(),
                "model": "gpt-4.1",
            }
        )
        metadata["label"] = label.original

        scores = self.scorer.calculate_score(evaluation_json.get("issues", []))
        evaluation_json["scores"] = scores
        print(
            "Calculated scores - Overall: "
            f"{scores['overall_quality_score']}/10 ({scores['classification']})"
        )
        return evaluation_json

    def _persist_evaluation(self, evaluation_json: Dict, language: str) -> None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        result_filename = f"evaluation_{timestamp}.json"
        result_path = self.eval_results_dir / language / result_filename
        with open(result_path, "w", encoding="utf-8") as handle:
            json.dump(evaluation_json, handle, indent=2, ensure_ascii=False)
        print(f"💾 Evaluation saved: {result_filename}")

    def _fallback_parse(self, response_text: str) -> Optional[Dict]:
        strategies = (
            self._extract_json_by_braces,
            self._aggressive_clean_and_parse,
            self._extract_json_by_issues_pattern,
        )
        for index, strategy in enumerate(strategies, start=1):
            try:
                result = strategy(response_text)
                if result is not None:
                    print(f"   • Fallback strategy {index} succeeded")
                    return result
            except Exception as exc:
                print(f"   • Fallback strategy {index} failed: {exc}")
        return None

    @staticmethod
    def _clean_json_response(response: str) -> str:
        if not response:
            return ""

        cleaned = response.strip()
        patterns = (
            ("```json\n", "```"),
            ("```json", "```"),
            ("```\n", "```"),
            ("```", "```"),
        )
        for start, end in patterns:
            if cleaned.startswith(start):
                cleaned = cleaned[len(start) :]
                if cleaned.endswith(end):
                    cleaned = cleaned[: -len(end)]
                break

        cleaned = cleaned.strip()
        prefixes = ("Here is the JSON:", "Here's the evaluation:", "JSON response:")
        for prefix in prefixes:
            if cleaned.lower().startswith(prefix.lower()):
                cleaned = cleaned[len(prefix) :].strip()
        return cleaned

    @staticmethod
    def _extract_json_by_braces(response: str) -> Optional[Dict]:
        start_idx = response.find("{")
        end_idx = response.rfind("}") + 1
        if start_idx != -1 and end_idx > start_idx:
            return json.loads(response[start_idx:end_idx])
        return None

    @staticmethod
    def _aggressive_clean_and_parse(response: str) -> Optional[Dict]:
        match = re.search(r"\{.*\}", response, re.DOTALL)
        if not match:
            return None
        json_str = match.group()
        json_str = re.sub(r"[\r\n\t]+", " ", json_str)
        json_str = re.sub(r"\s+", " ", json_str)
        return json.loads(json_str)

    @staticmethod
    def _extract_json_by_issues_pattern(response: str) -> Optional[Dict]:
        match = re.search(r"\"issues\"\s*:\s*\[.*?\]", response, re.DOTALL)
        if not match:
            return None
        return json.loads("{" + match.group() + "}")
