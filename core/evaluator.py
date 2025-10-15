"""Evaluation helpers built on Azure OpenAI."""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from openai import AzureOpenAI

from config import API_KEY, API_VERSION, DEPLOYMENT_NAME, ENDPOINT_URL
from utils.json_parser import parse_json_response
from utils.labels import sanitize_label
from utils.false_positive_filter import filter_evaluation_result

from .aggregator import aggregate_issues
from .analyzer import analyze_patterns
from .models import EvaluationMetadata, EvaluationResult, Issue
from .scoring import calculate_quality_score


class Evaluator:
    def __init__(self, orchestrator, markdown_dir: Path, eval_results_dir: Path, base_dir: Path | str = ".") -> None:
        if not ENDPOINT_URL or not API_KEY:
            raise ValueError("ENDPOINT_URL and AZURE_OPENAI_API_KEY environment variables are required. Please check your .env file.")

        self.client = AzureOpenAI(azure_endpoint=ENDPOINT_URL, api_key=API_KEY, api_version=API_VERSION)
        self.deployment = DEPLOYMENT_NAME
        self.markdown_dir = Path(markdown_dir)
        self.eval_results_dir = Path(eval_results_dir)
        self.base_path = Path(base_dir)
        self.orchestrator = orchestrator

    def evaluate_language(self, language: str, label: str) -> bool:
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
        print(f"Using label: {label}")
        evaluated = 0

        for md_file in md_files:
            print(f"Evaluating {md_file.name}...")
            if self.evaluate_file(md_file, language, label):
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
        return success

    def evaluate_file(self, md_file: Path, language: str, label: str) -> bool:
        try:
            with open(md_file, "r", encoding="utf-8") as handle:
                content = handle.read()
        except OSError as exc:
            print(f"Error reading {md_file}: {exc}")
            return False

        prompt = self.orchestrator.get_prompt(content, language)

        if language.lower() == "english":
            system_content = "You are an expert educational content evaluator specializing in quiz quality assessment and localization review. You must return only valid JSON without any additional text."
        else:
            system_content = "You are a specialized dual-expertise evaluator combining both linguistic accuracy and localization quality assessment. Apply deduplication rules strictly. Return only valid JSON without any additional text."
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

    def run_aggregation(self, languages: List[str], label: str) -> bool:
        if not languages:
            return False

        try:
            aggregated = aggregate_issues(languages, label=label, base_dir=self.base_path)
        except Exception as exc:
            print(f"⚠️  Issue aggregation failed for label '{label}': {exc}")
            return False

        return bool(aggregated)

    def run_pattern_analysis(self, languages: List[str], label: str) -> bool:
        if not languages:
            return False

        try:
            processed = analyze_patterns(languages, label=label, base_dir=self.base_path)
        except Exception as exc:
            print(f"⚠️  Issue pattern analysis failed for label '{label}': {exc}")
            return False

        return bool(processed)

    def refresh_file_index(self) -> None:
        self._refresh_file_index()

    def _refresh_file_index(self) -> None:
        index_data = self._build_file_index(self.eval_results_dir)
        if not index_data:
            return

        index_path = self.eval_results_dir.parent / "file_index.json"
        self._save_file_index(index_data, index_path)
        print(f"📄 Updated file index: {index_path.name}")

    def _parse_response(self, response_text: str, md_file: Path, language: str, label: str) -> Optional[Dict]:
        evaluation_json = parse_json_response(response_text)

        if evaluation_json is None:
            print("❌ Failed to parse JSON from LLM response")
            print(f"Raw response (first 500 chars): {response_text[:500]}...")
            print(f"Raw response (last 200 chars): ...{response_text[-200:]}")
            return None

        if "issues" not in evaluation_json or not isinstance(evaluation_json["issues"], list):
            print("⚠️  Invalid format: 'issues' must be an array")
            return None

        metadata = EvaluationMetadata(
            file=md_file.name,
            language=language.title(),
            timestamp=datetime.now().isoformat(),
            model="gpt-4.1",
            label=label,
        )

        issues = [Issue.from_dict(issue) if isinstance(issue, dict) else issue
                  for issue in evaluation_json.get("issues", [])]
        scores = calculate_quality_score(issues)

        result = EvaluationResult(issues=issues, metadata=metadata, scores=scores)
        result_dict = result.to_dict()

        # Filter out false positives before returning
        print(f"Initial scores - Overall: {scores.overall_quality_score}/10 ({scores.classification}), Issues: {len(issues)}")
        result_dict = filter_evaluation_result(result_dict, verbose=True)

        # Print final scores after filtering
        final_scores = result_dict.get("scores", {})
        final_issue_count = len(result_dict.get("issues", []))
        filtered_count = result_dict.get("metadata", {}).get("false_positives_filtered", 0)

        if filtered_count > 0:
            print(f"Final scores - Overall: {final_scores.get('overall_quality_score', 0)}/10 ({final_scores.get('classification', 'N/A')}), Issues: {final_issue_count}")

        return result_dict

    def _persist_evaluation(self, evaluation_json: Dict, language: str) -> None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        result_filename = f"evaluation_{timestamp}.json"
        result_path = self.eval_results_dir / language / result_filename
        with open(result_path, "w", encoding="utf-8") as handle:
            json.dump(evaluation_json, handle, indent=2, ensure_ascii=False)
        print(f"💾 Evaluation saved: {result_filename}")

    def _build_file_index(self, eval_results_dir: Path) -> Dict:
        """Build an index of all evaluation files organized by language."""
        if not eval_results_dir.exists():
            return {}

        files_by_language = {}
        languages = []

        for lang_dir in sorted(eval_results_dir.iterdir()):
            if not lang_dir.is_dir():
                continue

            language = lang_dir.name
            languages.append(language)

            eval_files = sorted(
                [f.name for f in lang_dir.glob("evaluation_*.json")],
                reverse=True  # Most recent first
            )
            files_by_language[language] = eval_files

        total_files = sum(len(files) for files in files_by_language.values())

        return {
            "generated_at": datetime.now().isoformat(),
            "total_files": total_files,
            "languages": languages,
            "files": files_by_language,
        }

    def _save_file_index(self, index_data: Dict, index_path: Path) -> None:
        """Save the file index to a JSON file."""
        with open(index_path, "w", encoding="utf-8") as handle:
            json.dump(index_data, handle, indent=2, ensure_ascii=False)
