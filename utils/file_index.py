"""File index utilities for dashboard."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional


def build_file_index(eval_results_dir: Path) -> Optional[Dict]:
    """
    Build an index of evaluation result files organized by language.

    Args:
        eval_results_dir: Directory containing language subdirectories with JSON files

    Returns:
        Dictionary with file index metadata or None if directory doesn't exist
    """
    if not eval_results_dir.exists():
        return None

    language_files: Dict[str, List[str]] = {}
    total_files = 0

    for language_dir in sorted(eval_results_dir.iterdir()):
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
            # Sort by modification time, newest first
            files_with_mtime.sort(key=lambda item: item[1], reverse=True)
            language_files[language_dir.name] = [name for name, _ in files_with_mtime]
            total_files += len(files_with_mtime)

    return {
        "generated_at": datetime.now().isoformat(),
        "total_files": total_files,
        "languages": sorted(language_files.keys()),
        "files": language_files,
    }


def save_file_index(data: Dict, output_path: Path) -> None:
    """
    Save file index data to JSON file.

    Args:
        data: File index dictionary
        output_path: Path where JSON should be written
    """
    with open(output_path, "w", encoding="utf-8") as handle:
        json.dump(data, handle, indent=2, ensure_ascii=False)
