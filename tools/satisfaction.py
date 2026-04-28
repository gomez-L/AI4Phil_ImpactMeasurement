"""
Tool: analyze_satisfaction
Multi-dimensional satisfaction analysis + NPS calculation.
"""
from __future__ import annotations

import json
from typing import Annotated

import numpy as np
from langchain_core.tools import tool

from observability import observe


# Satisfaction dimensions and their weights for the composite score
DIMENSION_WEIGHTS = {
    "content": 0.25,
    "organization": 0.15,
    "instructor": 0.30,
    "materials": 0.15,
    "overall": 0.15,
}
ALERT_THRESHOLDS = {
    "content": 3.5,
    "organization": 3.5,
    "instructor": 4.0,
    "materials": 3.5,
    "platform": 3.5,
    "overall": 3.5,
}


def _compute_nps(nps_scores: list[int]) -> float:
    if not nps_scores:
        return 0.0
    arr = np.array(nps_scores)
    pct_promoters = float((arr >= 9).mean()) * 100
    pct_detractors = float((arr <= 6).mean()) * 100
    return round(pct_promoters - pct_detractors, 1)


def _nps_label(nps: float) -> str:
    if nps >= 70:
        return "World-class"
    elif nps >= 50:
        return "Excellent"
    elif nps >= 30:
        return "Good"
    elif nps >= 0:
        return "Acceptable"
    else:
        return "Poor — urgent attention needed"


@tool
@observe(name="tool_analyze_satisfaction")
def analyze_satisfaction(
    workshop_id: Annotated[str, "Workshop identifier"],
    surveys: Annotated[
        list[dict],
        (
            "List of survey dicts. Each dict must contain: content (float 0-5), "
            "organization (float 0-5), instructor (float 0-5), materials (float 0-5), "
            "overall (float 0-5), nps (int 0-10). Optional: platform (float 0-5, online only), "
            "open_feedback (str)."
        ),
    ],
    modality: Annotated[str, "Workshop modality: 'onsite' or 'online'"] = "onsite",
    previous_scores: Annotated[
        dict | None,
        "Optional dict of previous workshop's mean scores per dimension, for trend comparison."
    ] = None,
) -> str:
    """
    Compute multi-dimensional satisfaction metrics and NPS for a workshop.
    Returns alerts for dimensions below threshold, trend vs. previous session,
    and a weighted composite satisfaction score.
    """
    if not surveys:
        return json.dumps({"error": "No survey data provided."})

    dims = ["content", "organization", "instructor", "materials", "overall"]
    if modality == "online":
        dims.append("platform")

    dimension_scores: dict[str, dict] = {}
    for dim in dims:
        values = [s[dim] for s in surveys if s.get(dim) is not None]
        if values:
            arr = np.array(values, dtype=float)
            dimension_scores[dim] = {
                "mean": round(float(arr.mean()), 2),
                "std": round(float(arr.std(ddof=1)), 2) if len(arr) > 1 else 0.0,
                "min": round(float(arr.min()), 2),
                "max": round(float(arr.max()), 2),
                "below_threshold": bool(arr.mean() < ALERT_THRESHOLDS.get(dim, 3.5)),
            }

    # Weighted composite (exclude platform from weights)
    composite = sum(
        dimension_scores[d]["mean"] * w
        for d, w in DIMENSION_WEIGHTS.items()
        if d in dimension_scores
    )

    # NPS
    nps_vals = [s["nps"] for s in surveys if "nps" in s]
    nps = _compute_nps(nps_vals)

    # Trend vs. previous
    trend: dict[str, float] = {}
    if previous_scores:
        for dim in dims:
            if dim in dimension_scores and dim in previous_scores:
                trend[dim] = round(dimension_scores[dim]["mean"] - previous_scores[dim], 2)

    # Alerts
    alerts = [
        f"⚠  '{dim}' score {dimension_scores[dim]['mean']:.1f}/5 is below threshold "
        f"({ALERT_THRESHOLDS.get(dim, 3.5)}/5) — review recommended."
        for dim in dims
        if dim in dimension_scores and dimension_scores[dim]["below_threshold"]
    ]

    # Open feedback sample
    open_feedback_sample = [
        s["open_feedback"] for s in surveys
        if s.get("open_feedback") and isinstance(s["open_feedback"], str)
    ][:5]

    result = {
        "workshop_id": workshop_id,
        "n_responses": len(surveys),
        "modality": modality,
        "dimension_scores": dimension_scores,
        "composite_satisfaction": round(composite, 2),
        "composite_label": (
            "High" if composite >= 4.0
            else "Moderate" if composite >= 3.5
            else "Low"
        ),
        "nps": nps,
        "nps_label": _nps_label(nps),
        "trend_vs_previous": trend,
        "alerts": alerts,
        "open_feedback_sample": open_feedback_sample,
        "interpretation": (
            f"Composite satisfaction: {composite:.2f}/5 ({('High' if composite >= 4.0 else 'Moderate' if composite >= 3.5 else 'Low')}). "
            f"NPS: {nps} ({_nps_label(nps)}). "
            f"{'No dimensions below threshold.' if not alerts else f'{len(alerts)} dimension(s) need attention.'}"
        ),
    }
    return json.dumps(result, indent=2)
