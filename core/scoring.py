from typing import List
from .models import Issue, Scores, IssueBreakdown, PenaltyBreakdown

SEVERITY_MULTIPLIERS = {
    "HIGH": 0.3,
    "MEDIUM": 0.2,
    "MINOR": 0.1,
}

def calculate_quality_score(issues: List[Issue | dict], base_score: float = 10.0) -> Scores:
    if not issues:
        return Scores(
            overall_quality_score=base_score,
            classification="NATIVE",
            total_issues=0,
            total_penalty=0.0,
            issue_breakdown=IssueBreakdown(),
            penalty_breakdown=PenaltyBreakdown(),
        )

    penalties = {"linguistic": 0.0, "localization": 0.0, "distractor_quality": 0.0}
    counts = {"linguistic": 0, "localization": 0, "distractor_quality": 0}

    for issue in issues:
        if isinstance(issue, Issue):
            category = issue.category
            severity = issue.severity
        else:
            category = issue.get("category", "linguistic")
            severity = issue.get("severity", "MEDIUM")

        if category not in penalties:
            continue

        counts[category] += 1
        penalties[category] += SEVERITY_MULTIPLIERS.get(severity, 0.2)

    total_penalty = sum(penalties.values())
    score = max(0.0, base_score - total_penalty)

    return Scores(
        overall_quality_score=round(score, 1),
        classification=_classify_score(score),
        total_issues=sum(counts.values()),
        total_penalty=round(total_penalty, 1),
        issue_breakdown=IssueBreakdown(
            linguistic=counts["linguistic"],
            localization=counts["localization"],
            distractor_quality=counts["distractor_quality"],
        ),
        penalty_breakdown=PenaltyBreakdown(
            linguistic_penalty=round(penalties["linguistic"], 1),
            localization_penalty=round(penalties["localization"], 1),
            distractor_quality_penalty=round(penalties["distractor_quality"], 1),
        ),
    )

def _classify_score(score: float) -> str:
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
