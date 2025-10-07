import json
import shutil
from pathlib import Path

from config import LANGUAGES, EVAL_RESULTS_DIR, MARKDOWN_DIR, RAW_JSON_DIR, ISSUES_DIR

def clean_eval_results(language: str | None = None) -> bool:
    cleaned = _clean_directory(EVAL_RESULTS_DIR, language, "Evaluation Results")
    if cleaned and language:
        _clean_language_issues(language)
    elif cleaned and not language:
        _clean_all_issues()
    return cleaned

def clean_markdown_files(language: str | None = None) -> bool:
    return _clean_directory(MARKDOWN_DIR, language, "Markdown Files")

def clean_raw_json_files(language: str | None = None) -> bool:
    return _clean_directory(RAW_JSON_DIR, language, "Raw JSON Files")

def _clean_directory(base_path: Path, language: str | None, label: str) -> bool:
    if not base_path.exists():
        print(f"⏭️  Directory not found: {base_path}")
        return True

    if language:
        target = base_path / language
        if not target.exists():
            print(f"⏭️  Directory not found: {target}")
            return True
        print(f"🧹 Cleaning {language.title()} {label}...")
        return _remove_contents(target)

    print(f"🧹 Cleaning ALL {label}...")
    return _remove_contents(base_path)

def _remove_contents(path: Path) -> bool:
    try:
        for item in path.iterdir():
            if item.is_file():
                item.unlink()
            else:
                shutil.rmtree(item)
        print(f"✓ Successfully cleaned {path}")
        return True
    except Exception as exc:
        print(f"❌ Error cleaning {path}: {exc}")
        return False

def _clean_language_issues(language: str) -> None:
    if not ISSUES_DIR.exists():
        return

    combined_dir = ISSUES_DIR / "combined_issues"
    if combined_dir.exists():
        for label_dir in combined_dir.glob("*"):
            if label_dir.is_dir():
                target = label_dir / f"{language}_issues.json"
                if target.exists():
                    target.unlink()

    patterns_dir = ISSUES_DIR / "common_patterns"
    if patterns_dir.exists():
        for label_dir in patterns_dir.glob("*"):
            if label_dir.is_dir():
                target = label_dir / f"{language}.json"
                if target.exists():
                    target.unlink()

    all_file = ISSUES_DIR / "all" / "all_common_issues.json"
    if all_file.exists():
        try:
            with open(all_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, dict) and "labels" in data:
                for label_data in data["labels"].values():
                    if isinstance(label_data, dict) and "analyses" in label_data:
                        label_data["analyses"].pop(language, None)
            with open(all_file, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except (json.JSONDecodeError, OSError):
            pass

def _clean_all_issues() -> None:
    if ISSUES_DIR.exists():
        try:
            shutil.rmtree(ISSUES_DIR)
            print("✓ Issues cache removed")
        except FileNotFoundError:
            pass
