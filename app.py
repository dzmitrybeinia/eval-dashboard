#!/usr/bin/env python3
"""Command-line orchestrator for the quiz localization workflow."""

import argparse
import sys
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

from config import LANGUAGES
from core import Evaluator, aggregate_issues, analyze_patterns
from orchestrators.full_evaluation_orchestrator import FullEvaluationOrchestrator
from orchestrators.content_only_orchestrator import ContentOnlyOrchestrator
from orchestrators.yes_no_evaluation_orchestrator import YesNoEvaluationOrchestrator
from utils.cleaner import clean_eval_results, clean_markdown_files, clean_raw_json_files
from utils.labels import sanitize_label
from utils.servers import serve_dashboard
from utils.static_export import export_static_dashboard

load_dotenv()


ORCHESTRATORS = {
    "fullevaluation": FullEvaluationOrchestrator,
    "contentonly": ContentOnlyOrchestrator,
    "yesnoevaluation": YesNoEvaluationOrchestrator,
}


def load_orchestrator(name: str):
    if name not in ORCHESTRATORS:
        print(f"❌ Unknown orchestrator: {name}")
        print(f"Available orchestrators: {', '.join(sorted(ORCHESTRATORS.keys()))}")
        sys.exit(1)

    orchestrator_class = ORCHESTRATORS[name]
    return orchestrator_class()


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Localization Quality Evaluation Tool - AI-powered evaluation of localized content",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    subparsers = parser.add_subparsers(
        dest="command",
        help="Command to run",
        metavar="{eval,convert,evaluate,aggregate-issues,analyze-patterns,dashboard,export-static,clean}",
    )

    # eval command - full pipeline
    eval_parser = subparsers.add_parser(
        "eval",
        help="Run full evaluation pipeline (convert + evaluate + aggregate + analyze)",
        description="Convert JSON to markdown, run AI evaluation, aggregate issues, and analyze patterns",
    )
    eval_parser.add_argument(
        "--orchestrator", required=True, help="Orchestrator name (fullevaluation, contentonly, yesnoevaluation)"
    )
    eval_parser.add_argument("--from", dest="from_path", required=True, help="Input directory with JSON files")
    eval_parser.add_argument("--to", dest="to_path", required=True, help="Output directory for markdown files")
    eval_parser.add_argument(
        "--language", required=True, choices=LANGUAGES, help="Target language to evaluate"
    )
    eval_parser.add_argument("--label", required=True, help="Version label for tracking (e.g., v1, prod, test)")

    # convert command
    convert_parser = subparsers.add_parser(
        "convert",
        help="Convert JSON files to markdown",
        description="Transform JSON lesson files into markdown format using specified converter",
    )
    convert_parser.add_argument(
        "--orchestrator", required=True, help="Orchestrator name (determines which converter to use)"
    )
    convert_parser.add_argument("--from", dest="from_path", required=True, help="Input directory with JSON files")
    convert_parser.add_argument("--to", dest="to_path", required=True, help="Output directory for markdown files")
    convert_parser.add_argument(
        "--language", required=True, choices=LANGUAGES, help="Target language"
    )

    # evaluate command
    evaluate_parser = subparsers.add_parser(
        "evaluate",
        help="Evaluate markdown files for quality",
        description="Run AI-powered quality evaluation on existing markdown files",
    )
    evaluate_parser.add_argument(
        "--orchestrator", required=True, help="Orchestrator name"
    )
    evaluate_parser.add_argument("--from", dest="from_path", required=True, help="Directory with markdown files")
    evaluate_parser.add_argument(
        "--language", required=True, choices=LANGUAGES, help="Target language"
    )
    evaluate_parser.add_argument("--label", required=True, help="Version label for tracking")

    # aggregate-issues command
    aggregate_parser = subparsers.add_parser(
        "aggregate-issues",
        help="Aggregate issues from evaluation results",
        description="Combine individual evaluation results into common issues by category and severity",
    )
    aggregate_parser.add_argument(
        "--language", required=True, choices=LANGUAGES, help="Target language"
    )
    aggregate_parser.add_argument("--label", required=True, help="Version label")

    # analyze-patterns command
    analyze_parser = subparsers.add_parser(
        "analyze-patterns",
        help="Analyze error patterns from aggregated issues",
        description="Use AI to identify recurring error patterns and generate recommendations",
    )
    analyze_parser.add_argument(
        "--orchestrator", required=True, help="Orchestrator name (used for prompt building)"
    )
    analyze_parser.add_argument(
        "--language", required=True, choices=LANGUAGES, help="Target language"
    )
    analyze_parser.add_argument("--label", required=True, help="Version label")

    # dashboard command
    subparsers.add_parser(
        "dashboard",
        help="Serve evaluation dashboard",
        description="Start local web server to view evaluation results in browser (opens at http://localhost:8083)",
    )

    # export-static command
    export_parser = subparsers.add_parser(
        "export-static",
        help="Export dashboard as static site for GitHub Pages",
        description="Create a self-contained static site with all evaluation data for GitHub Pages hosting",
    )
    export_parser.add_argument(
        "--output", default="docs", help="Output directory (default: docs)"
    )

    # clean command
    clean_parser = subparsers.add_parser(
        "clean",
        help="Clean directories",
        description="Remove generated files and directories",
    )
    clean_parser.add_argument(
        "path",
        choices=["eval_results", "markdown_files", "raw_json_files"],
        help="Directory to clean",
    )
    clean_parser.add_argument(
        "--all", action="store_true", help="Delete all language subdirectories"
    )
    clean_parser.add_argument(
        "--language", choices=LANGUAGES, help="Specific language to clean"
    )
    clean_parser.add_argument(
        "--label", help="Clean by label (eval_results only): removes eval files, issues, and patterns"
    )

    # Parse arguments
    provided_args = argv if argv is not None else sys.argv[1:]
    if not provided_args or provided_args[0] in ("-h", "--help"):
        parser.print_help()
        return 0

    args = parser.parse_args(provided_args)

    if not args.command:
        parser.print_help()
        return 1

    if args.command == "eval":
        return run_eval(
            args.orchestrator, args.from_path, args.to_path, args.language, args.label
        )
    elif args.command == "convert":
        return run_convert(args.orchestrator, args.from_path, args.to_path, args.language)
    elif args.command == "evaluate":
        return run_evaluate(args.orchestrator, args.from_path, args.language, args.label)
    elif args.command == "aggregate-issues":
        return run_aggregate_issues(args.language, args.label)
    elif args.command == "analyze-patterns":
        return run_analyze_patterns(args.orchestrator, args.language, args.label)
    elif args.command == "dashboard":
        return run_dashboard()
    elif args.command == "export-static":
        return run_export_static(args.output)
    elif args.command == "clean":
        return run_clean(args.path, args.all, args.language, args.label)

    return 1


def run_eval(orchestrator_name: str, from_path: str, to_path: str, language: str, label: str) -> int:
    print(f"Starting full evaluation pipeline for {language.title()}")
    print(f"   Orchestrator: {orchestrator_name}")
    print(f"   Source: {from_path}")
    print(f"   Target: {to_path}")
    print(f"   Label: {label}")
    print("=" * 60)

    orchestrator = load_orchestrator(orchestrator_name)

    print("\nStep 1: Converting JSON to markdown...")
    converter_class = orchestrator.get_converter_class()
    converter = converter_class()

    input_dir = Path(from_path)
    output_dir = Path(to_path)

    if not converter.convert_language(input_dir, output_dir, language):
        print("❌ Conversion failed")
        return 1

    print("\n🤖 Step 2: Running AI evaluation...")
    evaluator = Evaluator(
        orchestrator=orchestrator,
        markdown_dir=output_dir.parent,
        eval_results_dir=Path("eval_results"),
    )

    if not evaluator.evaluate_language(language, label):
        print("❌ Evaluation failed")
        return 1

    if orchestrator.should_run_issues_aggregation():
        print("\nStep 3: Aggregating issues...")
        if not evaluator.run_aggregation([language], label):
            print("⚠️  Issue aggregation failed")

    if orchestrator.should_run_pattern_analysis():
        print("\nStep 4: Analyzing error patterns...")
        if not evaluator.run_pattern_analysis([language], label):
            print("⚠️  Pattern analysis failed")

    print("\n✓ Full pipeline completed successfully!")
    return 0


def run_convert(orchestrator_name: str, from_path: str, to_path: str, language: str) -> int:
    print(f"Converting {language.title()} quizzes...")
    orchestrator = load_orchestrator(orchestrator_name)

    converter_class = orchestrator.get_converter_class()
    converter = converter_class()

    input_dir = Path(from_path)
    output_dir = Path(to_path)

    success = converter.convert_language(input_dir, output_dir, language)
    return 0 if success else 1


def run_evaluate(orchestrator_name: str, from_path: str, language: str, label: str) -> int:
    print(f"🤖 Evaluating {language.title()} content...")
    orchestrator = load_orchestrator(orchestrator_name)

    markdown_path = Path(from_path)

    evaluator = Evaluator(
        orchestrator=orchestrator,
        markdown_dir=markdown_path.parent,
        eval_results_dir=Path("eval_results"),
    )

    success = evaluator.evaluate_language(language, label)

    return 0 if success else 1

def run_aggregate_issues(language: str, label: str) -> int:
    print(f"Aggregating issues for {language.title()}...")

    processed = aggregate_issues([language], label=label)

    return 0 if processed else 1


def run_analyze_patterns(orchestrator_name: str, language: str, label: str) -> int:
    print(f"Analyzing error patterns for {language.title()}...")

    processed = analyze_patterns([language], label=label)

    return 0 if processed else 1


def run_dashboard() -> int:
    try:
        serve_dashboard()
    except FileNotFoundError as exc:
        print(f"❌ {exc}")
        return 1
    return 0


def run_export_static(output_dir: str) -> int:
    success = export_static_dashboard(output_dir)
    return 0 if success else 1


def run_clean_by_label(label: str) -> int:
    import json
    import shutil

    label_key = sanitize_label(label)
    print(f"🧹 Cleaning all data for label: {label_key}")
    print("=" * 60)

    eval_results_dir = Path("eval_results")
    issues_dir = Path("issues")

    print("\n📁 Step 1: Cleaning evaluation results...")
    deleted_count = 0
    languages_affected = set()

    if eval_results_dir.exists():
        for lang_dir in eval_results_dir.iterdir():
            if not lang_dir.is_dir():
                continue

            for eval_file in lang_dir.glob("evaluation_*.json"):
                try:
                    with open(eval_file, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        file_label = data.get("metadata", {}).get("label", "")

                        if file_label == label_key:
                            eval_file.unlink()
                            deleted_count += 1
                            languages_affected.add(lang_dir.name)
                except (json.JSONDecodeError, KeyError, OSError):
                    continue

    print(f"✓ Deleted {deleted_count} evaluation files")
    if languages_affected:
        print(f"   Languages affected: {', '.join(sorted(languages_affected))}")

    print("\n📁 Step 2: Cleaning combined issues...")
    combined_issues_dir = issues_dir / "combined_issues" / label_key
    if combined_issues_dir.exists():
        shutil.rmtree(combined_issues_dir)
        print(f"✓ Removed: {combined_issues_dir}")
    else:
        print(f"⏭️  No combined issues found for {label_key}")

    print("\n📁 Step 3: Cleaning common patterns...")
    patterns_dir = issues_dir / "common_patterns" / label_key
    if patterns_dir.exists():
        shutil.rmtree(patterns_dir)
        print(f"✓ Removed: {patterns_dir}")
    else:
        print(f"⏭️  No common patterns found for {label_key}")

    print("\n📁 Step 4: Cleaning all common issues...")
    all_issues_file = issues_dir / "all" / "all_common_issues.json"
    if all_issues_file.exists():
        try:
            with open(all_issues_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            if isinstance(data, dict) and "labels" in data:
                labels = data["labels"]
                if label_key in labels:
                    del labels[label_key]
                    print(f"✓ Removed label '{label_key}' from all_common_issues.json")

                    if data.get("latest_label") == label_key:
                        if labels:
                            data["latest_label"] = next(iter(labels.keys()))
                            print(f"   Updated latest_label to: {data['latest_label']}")
                        else:
                            all_issues_file.unlink()
                            print("   No labels remaining, removed all_common_issues.json")
                            return 0

                    with open(all_issues_file, "w", encoding="utf-8") as f:
                        json.dump(data, f, ensure_ascii=False, indent=2)
                else:
                    print(f"⏭️  Label '{label_key}' not found in all_common_issues.json")
        except (json.JSONDecodeError, OSError) as exc:
            print(f"⚠️  Could not update all_common_issues.json: {exc}")
    else:
        print("⏭️  No all_common_issues.json file found")

    print("\n" + "=" * 60)
    print(f"✓ Successfully cleaned all data for label: {label_key}")
    return 0


def run_clean(path: str, clean_all: bool, language: str | None, label: str | None) -> int:
    if clean_all and language:
        print("❌ Cannot use --all and --language together")
        return 1

    if label and clean_all:
        print("❌ Cannot use --all and --label together")
        return 1

    if label and language:
        print("❌ Cannot use --language and --label together")
        return 1

    if label:
        if path != "eval_results":
            print("❌ --label option is only supported for eval_results")
            return 1
        return run_clean_by_label(label)

    path_cleaners = {
        "eval_results": clean_eval_results,
        "markdown_files": clean_markdown_files,
        "raw_json_files": clean_raw_json_files,
    }

    clean_func = path_cleaners[path]

    if clean_all:
        success = clean_func(language=None)
    elif language:
        success = clean_func(language=language)
    else:
        print("❌ Must specify either --all, --language, or --label")
        return 1

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
