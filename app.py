#!/usr/bin/env python3
"""Command-line orchestrator for the quiz localization workflow."""

import argparse
import sys
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

from config import LANGUAGES, RAW_JSON_DIR, MARKDOWN_DIR, EVAL_RESULTS_DIR
from core import Evaluator, aggregate_issues, analyze_patterns
from orchestrators.lz_full_eval_orchestrator import LZFullEvalOrchestrator
from orchestrators.lz_lesson_eval_orchestrator import LZLessonEvalOrchestrator
from orchestrators.lz_quiz_eval_orchestrator import LZQuizEvalOrchestrator
from utils.cleaner import clean_eval_results, clean_markdown_files, clean_raw_json_files
from utils.labels import sanitize_label
from utils.servers import serve_dashboard
from utils.static_export import export_static_dashboard

load_dotenv()


ORCHESTRATORS = {
    "lzfull": LZFullEvalOrchestrator,
    "lzlesson": LZLessonEvalOrchestrator,
    "lzquiz": LZQuizEvalOrchestrator,
}

DEFAULT_ORCHESTRATOR = "lzfull"


def load_orchestrator(name: str):
    if name not in ORCHESTRATORS:
        print(f"❌ Unknown orchestrator: {name}")
        print(f"Available orchestrators: {', '.join(sorted(ORCHESTRATORS.keys()))}")
        sys.exit(1)

    orchestrator_class = ORCHESTRATORS[name]
    return orchestrator_class()


def get_standard_paths(language: str):
    """Get standard paths for a given language."""
    return {
        "raw_json": RAW_JSON_DIR / language,
        "markdown": MARKDOWN_DIR / language,
        "eval_results": EVAL_RESULTS_DIR / language,
    }


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="""Eval Dashboard - AI-powered evaluation of educational quiz content

HOW IT WORKS:
  1. Convert: JSONL files -> Markdown files 
  2. Evaluate: Each markdown file -> LLM -> Issue report (JSON)
  3. Analyze: Combine all issues -> Find common patterns

ORCHESTRATORS (choose what to evaluate, default: lzfull):
  lzfull    - Full content: Lesson text + ALL 8 quiz types (DynamicQuiz, FillInTheBlanks,
              YesNo, KahootQuiz, OpenEnded, Match, Sort, Group)
  lzlesson  - Lesson content only (no quizzes)
  lzquiz    - Quiz questions only (all 8 types, no lesson content)

BASIC WORKFLOW:
  # 1. Convert JSONL -> Markdown
  python app.py convert spanish

  # 2. Evaluate all lessons 
  python app.py eval spanish --label v1

  # 3. View results
  python app.py dashboard

For detailed help: python app.py <command> -h""",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    subparsers = parser.add_subparsers(
        dest="command",
        help="Command to run",
        metavar="{eval,convert,aggregate,analyze,file-index,dashboard,export,clean}",
    )

    # eval command - full pipeline
    eval_parser = subparsers.add_parser(
        "eval",
        help="Run full evaluation pipeline (convert + evaluate + aggregate + analyze)",
        description="""Convert JSONL to markdown, run GPT-4 evaluation, aggregate issues, and analyze patterns.

ORCHESTRATORS:
  lzfull    - Evaluates lesson content + all 8 quiz types (default)
  lzlesson  - Evaluates only lesson content (skips quizzes)
  lzquiz    - Evaluates only quiz questions (skips lesson content)

Examples:
  # Evaluate everything (uses lzfull by default)
  python app.py eval spanish --label v1

  # Evaluate only lesson content
  python app.py eval spanish --label content_v1 --orchestrator lzlesson

  # Evaluate only quiz questions
  python app.py eval spanish --label quiz_v1 --orchestrator lzquiz""",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    eval_parser.add_argument(
        "language",
        choices=LANGUAGES,
        help="Target language to evaluate"
    )
    eval_parser.add_argument(
        "--label",
        required=True,
        help="Version label for tracking (e.g., v1, prod, test)"
    )
    eval_parser.add_argument(
        "--orchestrator",
        default=DEFAULT_ORCHESTRATOR,
        choices=list(ORCHESTRATORS.keys()),
        help=f"Orchestrator type (default: {DEFAULT_ORCHESTRATOR})"
    )

    # convert command
    convert_parser = subparsers.add_parser(
        "convert",
        help="Convert JSONL files to markdown",
        description="""Transform JSONL lesson files into markdown format.

WHAT HAPPENS:
  - Reads JSONL files from raw_json_files/{language}/
  - Creates separate markdown file for each lesson
  - Saves to markdown_files/{language}/

ORCHESTRATORS:
  lzfull    - Converts lesson content + all 8 quiz types (default)
  lzlesson  - Converts only lesson content (no quizzes)
  lzquiz    - Converts only quiz questions (no lesson content)

Examples:
  # Convert everything (uses lzfull by default)
  python app.py convert spanish

  # Convert only lesson content
  python app.py convert spanish --orchestrator lzlesson

  # Convert only quiz questions
  python app.py convert spanish --orchestrator lzquiz""",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    convert_parser.add_argument(
        "language",
        choices=LANGUAGES,
        help="Target language"
    )
    convert_parser.add_argument(
        "--orchestrator",
        default=DEFAULT_ORCHESTRATOR,
        choices=list(ORCHESTRATORS.keys()),
        help=f"Orchestrator type (default: {DEFAULT_ORCHESTRATOR})"
    )

    # aggregate command
    aggregate_parser = subparsers.add_parser(
        "aggregate",
        help="Aggregate issues from evaluation results",
        description="""Combine individual evaluation results into common issues by category and severity.
Groups issues from eval_results/{language}/ into issues/combined_issues/{label}/

Examples:
  python app.py aggregate spanish --label v1
  python app.py aggregate hebrew --label prod
  python app.py aggregate french --label 2024-01-15""",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    aggregate_parser.add_argument(
        "language",
        choices=LANGUAGES,
        help="Target language"
    )
    aggregate_parser.add_argument(
        "--label",
        required=True,
        help="Version label"
    )

    # analyze command
    analyze_parser = subparsers.add_parser(
        "analyze",
        help="Analyze error patterns from aggregated issues",
        description="""Use AI to identify recurring error patterns and generate recommendations.
Analyzes issues/combined_issues/{label}/ and outputs to issues/common_patterns/{label}/

Examples:
  python app.py analyze spanish --label v1
  python app.py analyze hebrew --label prod
  python app.py analyze french --label 2024-01-15""",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    analyze_parser.add_argument(
        "language",
        choices=LANGUAGES,
        help="Target language"
    )
    analyze_parser.add_argument(
        "--label",
        required=True,
        help="Version label"
    )

    # file-index command
    subparsers.add_parser(
        "file-index",
        help="Update file index",
        description="""Scan eval_results directory and update file_index.json.
This index is used by the dashboard to quickly list all evaluation files.

Example:
  python app.py file-index

The file index contains:
  - List of all languages with evaluations
  - Total number of evaluation files
  - All evaluation files per language (sorted by newest first)
  - Timestamp of when the index was generated""",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    # dashboard command
    subparsers.add_parser(
        "dashboard",
        help="Serve evaluation dashboard",
        description="Start local web server to view evaluation results in browser (opens at http://localhost:8083)",
    )

    # export command
    export_parser = subparsers.add_parser(
        "export",
        help="Export dashboard as static files",
        description="Create a self-contained static files",
    )
    export_parser.add_argument(
        "--output",
        default="docs",
        help="Output directory (default: docs)"
    )

    # clean command
    clean_parser = subparsers.add_parser(
        "clean",
        help="Clean directories",
        description="""Remove generated files and directories.

Examples:
  # Clean specific language
  python app.py clean eval_results --language spanish
  python app.py clean markdown_files --language hebrew

  # Clean all languages
  python app.py clean eval_results --all
  python app.py clean markdown_files --all

  # Clean by label (eval_results only)
  python app.py clean eval_results --label v1
  python app.py clean eval_results --label old-test

Note: Use --label to remove all data (evaluations, issues, patterns) for a specific version.""",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    clean_parser.add_argument(
        "path",
        choices=["eval_results", "markdown_files", "raw_json_files"],
        help="Directory to clean",
    )
    clean_parser.add_argument(
        "--all",
        action="store_true",
        help="Delete all language subdirectories"
    )
    clean_parser.add_argument(
        "--language",
        choices=LANGUAGES,
        help="Specific language to clean"
    )
    clean_parser.add_argument(
        "--label",
        help="Clean by label (eval_results only): removes eval files, issues, and patterns"
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
        return run_eval(args.language, args.label, args.orchestrator)
    elif args.command == "convert":
        return run_convert(args.language, args.orchestrator)
    elif args.command == "aggregate":
        return run_aggregate(args.language, args.label)
    elif args.command == "analyze":
        return run_analyze(args.language, args.label)
    elif args.command == "file-index":
        return run_file_index()
    elif args.command == "dashboard":
        return run_dashboard()
    elif args.command == "export":
        return run_export(args.output)
    elif args.command == "clean":
        return run_clean(args.path, args.all, args.language, args.label)

    return 1


def run_eval(language: str, label: str, orchestrator_name: str) -> int:
    """Run full evaluation pipeline with auto-conversion if needed."""
    print(f"Starting full evaluation pipeline for {language.title()}")
    print(f"   Orchestrator: {orchestrator_name}")
    print(f"   Label: {label}")
    print("=" * 60)

    orchestrator = load_orchestrator(orchestrator_name)
    paths = get_standard_paths(language)

    # Auto-convert if markdown files don't exist
    markdown_dir = paths["markdown"]
    if not markdown_dir.exists() or not list(markdown_dir.glob("*.md")):
        print("\n📝 Markdown files not found. Running conversion first...")
        print(f"   Source: {paths['raw_json']}")
        print(f"   Target: {markdown_dir}")

        converter_class = orchestrator.get_converter_class()
        converter = converter_class()

        if not converter.convert_language(paths["raw_json"], markdown_dir, language):
            print("❌ Conversion failed")
            return 1
        print("✓ Conversion completed\n")

    print("\n🤖 Step 1: Running AI evaluation...")
    evaluator = Evaluator(
        orchestrator=orchestrator,
        markdown_dir=MARKDOWN_DIR,
        eval_results_dir=EVAL_RESULTS_DIR,
    )

    if not evaluator.evaluate_language(language, label):
        print("❌ Evaluation failed")
        return 1

    if orchestrator.should_run_issues_aggregation():
        print("\n📊 Step 2: Aggregating issues...")
        if not evaluator.run_aggregation([language], label):
            print("⚠️  Issue aggregation failed")

    if orchestrator.should_run_pattern_analysis():
        print("\n🔍 Step 3: Analyzing error patterns...")
        if not evaluator.run_pattern_analysis([language], label):
            print("⚠️  Pattern analysis failed")

    print("\n✓ Full pipeline completed successfully!")
    return 0


def run_convert(language: str, orchestrator_name: str) -> int:
    """Convert JSON files to markdown using standard paths."""
    print(f"Converting {language.title()} quizzes...")
    print(f"   Orchestrator: {orchestrator_name}")

    orchestrator = load_orchestrator(orchestrator_name)
    paths = get_standard_paths(language)

    print(f"   Source: {paths['raw_json']}")
    print(f"   Target: {paths['markdown']}")

    converter_class = orchestrator.get_converter_class()
    converter = converter_class()

    success = converter.convert_language(paths["raw_json"], paths["markdown"], language)
    return 0 if success else 1


def run_aggregate(language: str, label: str) -> int:
    """Aggregate issues for a language and label."""
    print(f"Aggregating issues for {language.title()}...")
    print(f"   Label: {label}")

    processed = aggregate_issues([language], label=label)
    return 0 if processed else 1


def run_analyze(language: str, label: str) -> int:
    """Analyze error patterns for a language and label."""
    print(f"Analyzing error patterns for {language.title()}...")
    print(f"   Label: {label}")

    processed = analyze_patterns([language], label=label)
    return 0 if processed else 1


def run_file_index() -> int:
    """Update the file index by scanning eval_results directory."""
    import json
    from datetime import datetime

    print("📁 Scanning eval_results directory...")

    if not EVAL_RESULTS_DIR.exists():
        print(f"❌ Directory not found: {EVAL_RESULTS_DIR}")
        return 1

    # Build file index
    files_by_language = {}
    languages = []

    for lang_dir in sorted(EVAL_RESULTS_DIR.iterdir()):
        if not lang_dir.is_dir():
            continue

        language = lang_dir.name
        languages.append(language)

        eval_files = sorted(
            [f.name for f in lang_dir.glob("evaluation_*.json")],
            reverse=True  # Most recent first
        )
        files_by_language[language] = eval_files
        print(f"   {language}: {len(eval_files)} file(s)")

    total_files = sum(len(files) for files in files_by_language.values())

    index_data = {
        "generated_at": datetime.now().isoformat(),
        "total_files": total_files,
        "languages": languages,
        "files": files_by_language,
    }

    # Save file index
    index_path = Path("file_index.json")
    with open(index_path, "w", encoding="utf-8") as f:
        json.dump(index_data, f, indent=2, ensure_ascii=False)

    print(f"\n✓ File index updated: {index_path}")
    print(f"   Total files: {total_files}")
    print(f"   Languages: {len(languages)}")
    return 0


def run_dashboard() -> int:
    """Start the evaluation dashboard server."""
    try:
        serve_dashboard()
    except FileNotFoundError as exc:
        print(f"❌ {exc}")
        return 1
    return 0


def run_export(output_dir: str) -> int:
    """Export dashboard as static site."""
    success = export_static_dashboard(output_dir)
    return 0 if success else 1


def run_clean_by_label(label: str) -> int:
    """Clean all data associated with a specific label."""
    import json
    import shutil

    label_key = sanitize_label(label)
    print(f"🧹 Cleaning all data for label: {label_key}")
    print("=" * 60)

    issues_dir = Path("issues")

    print("\n📁 Step 1: Cleaning evaluation results...")
    deleted_count = 0
    languages_affected = set()

    if EVAL_RESULTS_DIR.exists():
        for lang_dir in EVAL_RESULTS_DIR.iterdir():
            if not lang_dir.is_dir():
                continue

            for eval_file in lang_dir.glob("evaluation_*.json"):
                try:
                    with open(eval_file, "r", encoding="utf-8") as f:
                        data = json.load(f)
                except (json.JSONDecodeError, OSError):
                    continue

                metadata = data.get("metadata", {})
                file_label_raw = metadata.get("label") or metadata.get("label_key")

                if not file_label_raw:
                    continue

                try:
                    file_label_key = sanitize_label(str(file_label_raw))
                except ValueError:
                    continue

                if file_label_key != label_key:
                    continue

                try:
                    eval_file.unlink()
                except OSError as exc:
                    print(f"  Could not remove {eval_file}: {exc}")
                    continue

                deleted_count += 1
                languages_affected.add(lang_dir.name)

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
    """Clean directories based on the specified path and options."""
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
