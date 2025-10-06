"""JSON parsing utilities for LLM responses."""

import json
import re
from typing import Callable, Dict, Optional

def parse_llm_json_response(text: str) -> Optional[Dict]:
    """Parse JSON from LLM response with multiple fallback strategies."""
    cleaned = clean_json_wrapper(text)
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass
    strategies: tuple[Callable[[str], Optional[Dict]], ...] = (
        _extract_json_by_braces,
        _aggressive_clean_and_parse,
        _extract_json_by_issues_pattern,
    )

    for strategy in strategies:
        try:
            result = strategy(text)
            if result is not None:
                return result
        except (json.JSONDecodeError, ValueError, AttributeError):
            continue

    return None


def clean_json_wrapper(text: str) -> str:
    """Remove common markdown wrappers from LLM JSON responses."""
    if not text:
        return ""

    cleaned = text.strip()
    patterns = (
        ("```json\n", "```"),
        ("```json", "```"),
        ("```\n", "```"),
        ("```", "```"),
    )

    for start, end in patterns:
        if cleaned.startswith(start) and cleaned.endswith(end):
            start_len = len(start)
            end_len = len(end)
            cleaned = cleaned[start_len:-end_len].strip()
            break

    return cleaned


def _extract_json_by_braces(response: str) -> Optional[Dict]:
    """Extract JSON by finding first { and last }."""
    start_idx = response.find("{")
    end_idx = response.rfind("}") + 1
    if start_idx != -1 and end_idx > start_idx:
        return json.loads(response[start_idx:end_idx])
    return None


def _aggressive_clean_and_parse(response: str) -> Optional[Dict]:
    """Clean whitespace aggressively and parse."""
    match = re.search(r"\{.*\}", response, re.DOTALL)
    if not match:
        return None
    json_str = match.group()
    json_str = re.sub(r"[\r\n\t]+", " ", json_str)
    json_str = re.sub(r"\s+", " ", json_str)
    return json.loads(json_str)


def _extract_json_by_issues_pattern(response: str) -> Optional[Dict]:
    """Extract JSON by finding 'issues' array pattern."""
    match = re.search(r"\"issues\"\s*:\s*\[.*?\]", response, re.DOTALL)
    if not match:
        return None
    return json.loads("{" + match.group() + "}")
