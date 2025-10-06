"""Scoring utilities for evaluation quality assessment."""

from typing import Dict, List

SEVERITY_MULTIPLIERS = {
    "HIGH": 0.3,
    "MEDIUM": 0.2,
    "MINOR": 0.1,
}


def calculate_quality_score(issues_list: List[Dict], base_score: float = 10.0) -> Dict:
    """Calculate weighted quality score based on issue severities."""
    if not issues_list:
        return {
            "overall_quality_score": base_score,
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
        penalties[category] += SEVERITY_MULTIPLIERS.get(severity, 0.2)

    total_penalty = sum(penalties.values())
    score = max(0.0, base_score - total_penalty)

    return {
        "overall_quality_score": round(score, 1),
        "classification": classify_score(score),
        "total_issues": sum(counts.values()),
        "total_penalty": round(total_penalty, 1),
        "issue_breakdown": counts,
        "penalty_breakdown": {
            "linguistic_penalty": round(penalties["linguistic"], 1),
            "localization_penalty": round(penalties["localization"], 1),
            "distractor_quality_penalty": round(penalties["distractor_quality"], 1),
        },
    }


def classify_score(score: float) -> str:
    """Return quality classification for a given score."""
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
