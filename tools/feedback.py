"""
Tool: synthesize_feedback_improvements
Empirical feedback analysis across multiple workshops → prioritised improvement plan.
Implements the COLLECT → ANALYSE → HYPOTHESISE → TEST cycle.
"""
from __future__ import annotations

import json
from collections import Counter
from typing import Annotated

import numpy as np
from langchain_core.tools import tool

from observability import observe


# ──────────────────────────────────────────────────────────────────────────────
# Keywords mapped to dimensions
# ──────────────────────────────────────────────────────────────────────────────
ISSUE_PATTERNS = {
    "content_depth": ["advanced", "deeper", "more detail", "too basic", "complex", "intermediate"],
    "time_management": ["time", "rushed", "ran out", "too long", "schedule", "buffer", "Q&A"],
    "materials_quality": ["materials", "slides", "handouts", "outdated", "resources", "exercises"],
    "platform_issues": ["audio", "video", "technical", "lag", "connection", "platform", "online"],
    "group_size": ["small group", "fewer people", "too many", "crowded", "breakout"],
    "follow_up": ["follow-up", "next steps", "homework", "practice", "exercises after"],
    "accessibility": ["free", "affordable", "language", "translation", "location", "schedule"],
    "instructor_clarity": ["confusing", "unclear", "explain", "slow down", "faster", "pace"],
}

IMPROVEMENT_ACTIONS = {
    "content_depth": "Introduce tiered tracks (beginner/intermediate/advanced) with clear prerequisites.",
    "time_management": "Add a 15-minute Q&A buffer at session end; share agenda 48h before.",
    "materials_quality": "Quarterly curriculum review cycle; update exercises with real-world datasets.",
    "platform_issues": "Pre-session tech check 10 min before start; dedicated tech support volunteer.",
    "group_size": "Cap onsite sessions at 20; use breakout rooms for online groups > 15.",
    "follow_up": "Send spaced-repetition exercises and recording link within 72h post-session.",
    "accessibility": "Expand outreach to community centres; offer morning + evening time slots.",
    "instructor_clarity": "Implement structured peer-observation coaching after each workshop cycle.",
}

EFFORT_LABELS = {
    "content_depth": "high",
    "time_management": "low",
    "materials_quality": "medium",
    "platform_issues": "low",
    "group_size": "medium",
    "follow_up": "low",
    "accessibility": "high",
    "instructor_clarity": "medium",
}


def _extract_issues(feedback_texts: list[str]) -> Counter:
    """Count how many feedback items mention each issue pattern."""
    counts: Counter = Counter()
    for text in feedback_texts:
        tl = text.lower()
        for issue, keywords in ISSUE_PATTERNS.items():
            if any(kw in tl for kw in keywords):
                counts[issue] += 1
    return counts


def _impact_effort_priority(mention_rate: float, effort: str) -> str:
    """Assign quadrant label based on mention rate (proxy for impact) and effort."""
    high_impact = mention_rate >= 0.20
    if high_impact and effort == "low":
        return "DO NOW"
    elif high_impact and effort in ("medium", "high"):
        return "PLAN NEXT QUARTER"
    elif not high_impact and effort == "low":
        return "NICE TO HAVE"
    else:
        return "DEPRIORITISE"


@tool
@observe(name="tool_synthesize_feedback_improvements")
def synthesize_feedback_improvements(
    workshops: Annotated[
        list[dict],
        (
            "List of workshop dicts, each with: "
            "id (str), name (str), date (str), "
            "feedback_texts (list[str] — open-ended responses), "
            "dimension_scores (dict[str, float] — mean per dimension), "
            "mean_gain (float — knowledge gain), "
            "nps (float)."
        ),
    ],
) -> str:
    """
    Analyse feedback across multiple workshops to produce a prioritised,
    evidence-based improvement plan following the COLLECT→ANALYSE→HYPOTHESISE→TEST cycle.

    Returns:
      - frequency analysis of recurring issues
      - impact/effort priority matrix
      - testable improvement hypotheses for top issues
      - trend analysis across workshops
      - programme improvement log template
    """
    if not workshops:
        return json.dumps({"error": "No workshop data provided."})

    # ── Aggregate feedback texts ─────────────────────────────────────────────
    all_feedback: list[str] = []
    for ws in workshops:
        all_feedback.extend(ws.get("feedback_texts", []))

    n_responses = len(all_feedback)
    issue_counts = _extract_issues(all_feedback)

    # ── Issue frequency table ────────────────────────────────────────────────
    issue_analysis: list[dict] = []
    for issue, count in issue_counts.most_common():
        rate = count / n_responses if n_responses else 0
        effort = EFFORT_LABELS.get(issue, "medium")
        priority = _impact_effort_priority(rate, effort)
        issue_analysis.append({
            "issue": issue,
            "mention_count": count,
            "mention_rate_pct": round(rate * 100, 1),
            "effort": effort,
            "priority_quadrant": priority,
            "recommended_action": IMPROVEMENT_ACTIONS.get(issue, "Review and address manually."),
            "hypothesis": (
                f"If we implement '{IMPROVEMENT_ACTIONS.get(issue, 'the recommended action')}', "
                f"then the '{issue.replace('_', ' ')}' dimension score will improve by ≥ 0.3 pts "
                f"within 2 workshop cycles."
            ),
        })

    # ── Cross-workshop trend analysis ────────────────────────────────────────
    sorted_ws = sorted(workshops, key=lambda w: w.get("date", ""))
    trends: dict[str, list] = {"nps": [], "mean_gain": [], "dates": []}
    for ws in sorted_ws:
        trends["nps"].append(ws.get("nps"))
        trends["mean_gain"].append(ws.get("mean_gain"))
        trends["dates"].append(ws.get("date"))

    # Trend direction
    def _trend_dir(values: list) -> str:
        vals = [v for v in values if v is not None]
        if len(vals) < 2:
            return "insufficient data"
        delta = vals[-1] - vals[0]
        if delta > 0.5:
            return "improving"
        elif delta < -0.5:
            return "declining"
        else:
            return "stable"

    # ── Dimension averages across workshops ──────────────────────────────────
    dim_all: dict[str, list[float]] = {}
    for ws in workshops:
        for dim, score in ws.get("dimension_scores", {}).items():
            dim_all.setdefault(dim, []).append(score)

    dim_averages = {
        dim: round(float(np.mean(scores)), 2)
        for dim, scores in dim_all.items()
    }
    lowest_dim = min(dim_averages, key=dim_averages.get) if dim_averages else None

    # ── Improvement log template ─────────────────────────────────────────────
    top_actions = [
        i for i in issue_analysis
        if i["priority_quadrant"] in ("DO NOW", "PLAN NEXT QUARTER")
    ][:4]

    improvement_log = [
        {
            "issue": a["issue"],
            "action": a["recommended_action"],
            "hypothesis": a["hypothesis"],
            "priority": a["priority_quadrant"],
            "status": "OPEN",
            "target_workshop": "Next cycle",
            "success_metric": f"Improvement ≥ 0.3 pts in related dimension score",
        }
        for a in top_actions
    ]

    result = {
        "n_workshops_analysed": len(workshops),
        "n_feedback_responses": n_responses,
        "issue_frequency_table": issue_analysis,
        "cross_workshop_trends": {
            "dates": trends["dates"],
            "nps_values": trends["nps"],
            "nps_trend": _trend_dir(trends["nps"]),
            "knowledge_gain_values": trends["mean_gain"],
            "knowledge_gain_trend": _trend_dir(trends["mean_gain"]),
        },
        "dimension_averages_all_workshops": dim_averages,
        "lowest_performing_dimension": lowest_dim,
        "programme_improvement_log": improvement_log,
        "interpretation": (
            f"Analysed {n_responses} feedback responses across {len(workshops)} workshops. "
            f"Top recurring issue: '{issue_counts.most_common(1)[0][0].replace('_', ' ')}' "
            f"(mentioned by {issue_counts.most_common(1)[0][1]} participants). "
            f"NPS trend: {_trend_dir(trends['nps'])}. "
            f"Knowledge gain trend: {_trend_dir(trends['mean_gain'])}. "
            f"Lowest satisfaction dimension overall: {lowest_dim}."
        ) if issue_counts else "No recurring issues detected in the provided feedback.",
    }
    return json.dumps(result, indent=2)
