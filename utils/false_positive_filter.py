"""Filter out obvious false positives from evaluation results."""

import re
from typing import List, Dict, Any


def is_false_positive(issue: Dict[str, Any]) -> tuple[bool, str]:
    """
    Check if an issue is a false positive.

    Returns:
        tuple: (is_false_positive: bool, reason: str)
    """
    original = issue.get("original", "").strip()
    correction = issue.get("correction", "").strip()
    description = issue.get("description", "").strip().lower()

    # Case 1: Original and correction are identical
    if original and correction and original == correction:
        return True, "Original equals correction"

    # Case 2: Original and correction are effectively identical (ignoring whitespace)
    if original and correction:
        # Normalize whitespace for comparison
        orig_normalized = re.sub(r'\s+', ' ', original).strip()
        corr_normalized = re.sub(r'\s+', ' ', correction).strip()
        if orig_normalized == corr_normalized:
            return True, "Original equals correction (normalized)"

    # Case 3: Description explicitly states no issues found
    no_issue_patterns = [
        r'\bno\s+(linguistic|localization|issues?|corrections?|problems?)\s+(detected|found|needed|required)',
        r'\bno\s+correction\s+is\s+needed',
        r'\bno\s+issues?\s+found',
        r'\bno\s+changes?\s+(needed|required)',
        r'\bthis\s+(sentence|text|phrase)\s+is\s+correct',
        r'\bthe\s+text\s+is\s+correct',
        r'\bcorrectly\s+(used|written|formatted)',
        r'\balready\s+correct',
        r'\bno\s+correction\s+necessary',
    ]

    for pattern in no_issue_patterns:
        if re.search(pattern, description):
            return True, f"Description indicates no issue: '{pattern}'"

    # Case 4: Description contradicts the issue (says it's correct but flagged anyway)
    contradiction_patterns = [
        r'\bthis\s+is\s+(already\s+)?correct',
        r'\bthe\s+(original|text)\s+is\s+(already\s+)?correct',
        r'\bthe\s+text\s+uses\s+the\s+correct',
        r'\bno\s+error',
    ]

    for pattern in contradiction_patterns:
        if re.search(pattern, description):
            return True, f"Description contradicts issue: '{pattern}'"

    # Case 5: Emoji removal issues (description mentions removing emoji for formality)
    emoji_removal_patterns = [
        r'use\s+of\s+(the\s+)?\w+\s+emoji',
        r'emoji.*\b(is\s+not\s+standard|informal|distracting|inappropriate)',
        r'removing\s+(the\s+)?emoji',
        r'emojis?.*\b(in\s+educational|formal|academic|professional)',
        r'emojis?.*\b(may\s+be\s+perceived|generally\s+considered)\s+as\s+informal',
        r'emoji.*\b(should\s+be\s+removed|ensures?\s+a\s+more\s+neutral)',
    ]

    for pattern in emoji_removal_patterns:
        if re.search(pattern, description, re.IGNORECASE):
            return True, "Issue about emoji formality/removal"

    return False, ""


def filter_false_positives(issues: List[Dict[str, Any]], verbose: bool = False) -> tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Filter out false positives from a list of issues.

    Args:
        issues: List of issue dictionaries
        verbose: If True, print information about filtered issues

    Returns:
        tuple: (valid_issues, filtered_issues)
    """
    valid_issues = []
    filtered_issues = []

    for issue in issues:
        is_fp, reason = is_false_positive(issue)

        if is_fp:
            filtered_issues.append({
                **issue,
                "_filter_reason": reason
            })
            if verbose:
                print(f"   Filtered false positive: {reason}")
                print(f"      Original: {issue.get('original', '')[:80]}...")
        else:
            valid_issues.append(issue)

    return valid_issues, filtered_issues


def filter_evaluation_result(evaluation_data: Dict[str, Any], verbose: bool = False) -> Dict[str, Any]:
    """
    Filter false positives from a complete evaluation result.

    Args:
        evaluation_data: Complete evaluation result dictionary
        verbose: If True, print information about filtering

    Returns:
        Dict: Updated evaluation data with false positives removed
    """
    if "issues" not in evaluation_data:
        return evaluation_data

    original_issues = evaluation_data["issues"]
    original_count = len(original_issues)

    valid_issues, filtered_issues = filter_false_positives(original_issues, verbose=verbose)

    if verbose and filtered_issues:
        print(f"   Filtered {len(filtered_issues)} false positive(s) out of {original_count} issue(s)")

    # Update the evaluation data
    evaluation_data["issues"] = valid_issues

    # Add metadata about filtering
    if filtered_issues:
        if "metadata" not in evaluation_data:
            evaluation_data["metadata"] = {}

        evaluation_data["metadata"]["false_positives_filtered"] = len(filtered_issues)
        evaluation_data["metadata"]["original_issue_count"] = original_count

        # Store filtered issues for reference if needed
        evaluation_data["_filtered_false_positives"] = filtered_issues

    # Recalculate scores if scoring module is available
    if "scores" in evaluation_data and valid_issues != original_issues:
        try:
            from core.scoring import calculate_quality_score
            from core.models import Issue

            issue_objects = [Issue.from_dict(issue) if isinstance(issue, dict) else issue
                           for issue in valid_issues]
            new_scores = calculate_quality_score(issue_objects)
            evaluation_data["scores"] = new_scores.to_dict()

            if verbose:
                print(f"   Recalculated score: {new_scores.overall_quality_score:.1f}/10 ({new_scores.classification})")
        except ImportError:
            if verbose:
                print("   Warning: Could not recalculate scores (scoring module not available)")

    return evaluation_data
