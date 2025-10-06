#!/usr/bin/env python3
"""Command-line orchestrator for the quiz localization workflow."""

import argparse
import importlib
import sys
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

from config import SUPPORTED_LANGUAGES
from core import Evaluator, IssueAggregator, ErrorPatternAnalyzer
from orchestrators.base import AbstractOrchestrator
from orchestrators.full_evaluation_orchestrator import FullEvaluationOrchestrator
from orchestrators.content_only_orchestrator import ContentOnlyOrchestrator
from orchestrators.yes_no_evaluation_orchestrator import YesNoEvaluationOrchestrator
from utils.cleaner import DirectoryCleaner
from utils.labels import ensure_label
from utils.servers import serve_dashboard
from utils.static_export import StaticExporter

load_dotenv()


def discover_orchestrators() -> dict[str, type[AbstractOrchestrator]]:
    orchestrators = {}
    orchestrators_dir = Path("orchestrators")

    if orchestrators_dir.exists():
        for file_path in orchestrators_dir.glob("*.py"):
            if file_path.stem.startswith("_") or file_path.stem == "base":
                continue

            module_name = f"orchestrators.{file_path.stem}"
            try:
                module = importlib.import_module(module_name)
                for attr_name in dir(module):
                    attr = getattr(module, attr_name)
                    if isinstance(attr, type) and issubclass(attr, AbstractOrchestrator) and attr is not AbstractOrchestrator:
                        key = attr_name.replace("Orchestrator", "").lower()
                        orchestrators[key] = attr
            except Exception as exc:
                print(f"⚠️  Could not load orchestrator from {file_path.name}: {exc}")

    return orchestrators


def load_orchestrator(name: str) -> AbstractOrchestrator:
    available = discover_orchestrators()

    if name not in available:
        print(f"❌ Unknown orchestrator: {name}")
        print(f"Available orchestrators: {', '.join(sorted(available.keys()))}")
        sys.exit(1)

    orchestrator_class = available[name]
    return orchestrator_class()


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Localization Quality Evaluation Tool - AI-powered evaluation of localized content",
        epilog="""
Examples:
  # Full pipeline: convert, evaluate, aggregate, analyze
  %(prog)s eval --orchestrator fullevaluation --from raw_json_files/polish --to markdown_files/polish_v1 --language polish --label v1

  # Content-only evaluation (linguistic focus)
  %(prog)s eval --orchestrator contentonly --from raw_json_files/russian --to markdown_files/russian_content --language russian --label content_v1

  # Questions-only evaluation with pattern analysis
  %(prog)s eval --orchestrator yesnoevaluation --from raw_json_files/spanish --to markdown_files/spanish_questions --language spanish --label questions_v2

  # Convert only (no evaluation)
  %(prog)s convert --orchestrator contentonly --from raw_json_files/french --to markdown_files/french_content --language french

  # Evaluate existing markdown files
  %(prog)s evaluate --orchestrator yesnoevaluation --from markdown_files/polish_questions --language polish --label test_v3

  # Aggregate and analyze separately
  %(prog)s aggregate-issues --language polish --label v1
  %(prog)s analyze-patterns --orchestrator yesnoevaluation --language polish --label v1

  # View results in browser
  %(prog)s dashboard

  # Export dashboard for GitHub Pages
  %(prog)s export-static --output docs

  # Clean by language or label
  %(prog)s clean eval_results --language polish
  %(prog)s clean eval_results --label old_v1
  %(prog)s clean markdown_files --all

Available orchestrators:
  fullevaluation   - Full evaluation (content + questions)
  contentonly      - Content-only evaluation (linguistic focus)
  yesnoevaluation  - Questions-only evaluation (with pattern analysis)
        """,
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
        epilog="Example: %(prog)s --orchestrator fullevaluation --from raw_json_files/polish --to markdown_files/polish_v1 --language polish --label v1",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    eval_parser.add_argument(
        "--orchestrator", required=True, help="Orchestrator name (fullevaluation, contentonly, yesnoevaluation)"
    )
    eval_parser.add_argument("--from", dest="from_path", required=True, help="Input directory with JSON files")
    eval_parser.add_argument("--to", dest="to_path", required=True, help="Output directory for markdown files")
    eval_parser.add_argument(
        "--language", required=True, choices=SUPPORTED_LANGUAGES, help="Target language to evaluate"
    )
    eval_parser.add_argument("--label", required=True, help="Version label for tracking (e.g., v1, prod, test)")

    # convert command
    convert_parser = subparsers.add_parser(
        "convert",
        help="Convert JSON files to markdown",
        description="Transform JSON lesson files into markdown format using specified converter",
        epilog="""Examples:
  # Full content + questions
  %(prog)s --orchestrator fullevaluation --from raw_json_files/polish --to markdown_files/polish_full --language polish

  # Content only (no questions)
  %(prog)s --orchestrator contentonly --from raw_json_files/russian --to markdown_files/russian_content --language russian

  # Questions only (no content)
  %(prog)s --orchestrator yesnoevaluation --from raw_json_files/spanish --to markdown_files/spanish_questions --language spanish""",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    convert_parser.add_argument(
        "--orchestrator", required=True, help="Orchestrator name (determines which converter to use)"
    )
    convert_parser.add_argument("--from", dest="from_path", required=True, help="Input directory with JSON files")
    convert_parser.add_argument("--to", dest="to_path", required=True, help="Output directory for markdown files")
    convert_parser.add_argument(
        "--language", required=True, choices=SUPPORTED_LANGUAGES, help="Target language"
    )

    # evaluate command
    evaluate_parser = subparsers.add_parser(
        "evaluate",
        help="Evaluate markdown files for quality",
        description="Run AI-powered quality evaluation on existing markdown files",
        epilog="""Examples:
  # Evaluate full content
  %(prog)s --orchestrator fullevaluation --from markdown_files/polish_v1 --language polish --label v1

  # Re-evaluate with different label
  %(prog)s --orchestrator contentonly --from markdown_files/russian_content --language russian --label retest_v2

  # Evaluate questions only
  %(prog)s --orchestrator yesnoevaluation --from markdown_files/spanish_questions --language spanish --label qa_v3""",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    evaluate_parser.add_argument(
        "--orchestrator", required=True, help="Orchestrator name"
    )
    evaluate_parser.add_argument("--from", dest="from_path", required=True, help="Directory with markdown files")
    evaluate_parser.add_argument(
        "--language", required=True, choices=SUPPORTED_LANGUAGES, help="Target language"
    )
    evaluate_parser.add_argument("--label", required=True, help="Version label for tracking")

    # aggregate-issues command
    aggregate_parser = subparsers.add_parser(
        "aggregate-issues",
        help="Aggregate issues from evaluation results",
        description="Combine individual evaluation results into common issues by category and severity",
        epilog="Example: %(prog)s --language polish --label v1",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    aggregate_parser.add_argument(
        "--language", required=True, choices=SUPPORTED_LANGUAGES, help="Target language"
    )
    aggregate_parser.add_argument("--label", required=True, help="Version label")

    # analyze-patterns command
    analyze_parser = subparsers.add_parser(
        "analyze-patterns",
        help="Analyze error patterns from aggregated issues",
        description="Use AI to identify recurring error patterns and generate recommendations",
        epilog="Example: %(prog)s --orchestrator yesnoevaluation --language polish --label v1",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    analyze_parser.add_argument(
        "--orchestrator", required=True, help="Orchestrator name (used for prompt building)"
    )
    analyze_parser.add_argument(
        "--language", required=True, choices=SUPPORTED_LANGUAGES, help="Target language"
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
        epilog="""Examples:
  # Export to default 'docs' directory
  %(prog)s

  # Export to custom directory
  %(prog)s --output my-dashboard

  # Export and deploy to GitHub Pages
  %(prog)s --output docs
  git add docs/ && git commit -m "Update dashboard" && git push""",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    export_parser.add_argument(
        "--output", default="docs", help="Output directory (default: docs)"
    )

    # clean command
    clean_parser = subparsers.add_parser(
        "clean",
        help="Clean directories",
        description="Remove generated files and directories",
        epilog="""Examples:
  %(prog)s eval_results --language polish    # Clean specific language
  %(prog)s markdown_files --all              # Clean all languages
  %(prog)s eval_results --label v1           # Clean all data for label v1""",
        formatter_class=argparse.RawDescriptionHelpFormatter,
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
        "--language", choices=SUPPORTED_LANGUAGES, help="Specific language to clean"
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
    label_info = ensure_label(label)

    aggregator = IssueAggregator()
    processed = aggregator.aggregate([language], label=label_info)

    return 0 if processed else 1


def run_analyze_patterns(orchestrator_name: str, language: str, label: str) -> int:
    print(f"Analyzing error patterns for {language.title()}...")

    label_info = ensure_label(label)
    analyzer = ErrorPatternAnalyzer()
    processed = analyzer.analyze([language], label=label_info)

    return 0 if processed else 1


def run_dashboard() -> int:
    try:
        serve_dashboard()
    except FileNotFoundError as exc:
        print(f"❌ {exc}")
        return 1
    return 0


def run_export_static(output_dir: str) -> int:
    exporter = StaticExporter()
    success = exporter.export(output_dir)
    return 0 if success else 1


def run_clean_by_label(label: str) -> int:
    import json
    import shutil
    from utils.labels import ensure_label

    label_info = ensure_label(label)
    label_key = label_info.key  # Get the normalized key
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
    cleaner = DirectoryCleaner()

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
        "eval_results": cleaner.clean_eval_results,
        "markdown_files": cleaner.clean_markdown_quizzes,
        "raw_json_files": cleaner.clean_generated_quizzes,
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
