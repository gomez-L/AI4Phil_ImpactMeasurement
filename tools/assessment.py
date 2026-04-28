"""
Tool: analyze_knowledge_impact
Computes pre→post knowledge gain using paired t-test and Cohen's d.
"""
from __future__ import annotations

import json
from typing import Annotated

import numpy as np
from scipy import stats
from langchain_core.tools import tool

from observability import observe


# ──────────────────────────────────────────────────────────────────────────────
# Helper
# ──────────────────────────────────────────────────────────────────────────────

def _cohen_d(pre: np.ndarray, post: np.ndarray) -> float:
    diff = post - pre
    if diff.std(ddof=1) == 0:
        return 0.0
    return float(diff.mean() / diff.std(ddof=1))


def _interpret_d(d: float) -> str:
    abs_d = abs(d)
    if abs_d < 0.2:
        return "negligible"
    elif abs_d < 0.5:
        return "small"
    elif abs_d < 0.8:
        return "medium"
    else:
        return "large"


# ──────────────────────────────────────────────────────────────────────────────
# Tool
# ──────────────────────────────────────────────────────────────────────────────

@tool
@observe(name="tool_analyze_knowledge_impact")
def analyze_knowledge_impact(
    workshop_id: Annotated[str, "Identifier for the workshop"],
    pre_scores: Annotated[list[float], "Pre-workshop test scores (0–10) for each participant"],
    post_scores: Annotated[list[float], "Post-workshop test scores (0–10) for each participant"],
) -> str:
    """
    Analyse the knowledge improvement from pre- to post-workshop tests.

    Returns a JSON string with:
      - mean_pre, mean_post, mean_gain
      - cohens_d, effect_size_label
      - t_statistic, p_value, significant (bool)
      - pct_improved, pct_significant_gain (≥ 2 pts)
      - per_participant summary
    """
    if len(pre_scores) != len(post_scores) or len(pre_scores) < 2:
        return json.dumps({"error": "pre_scores and post_scores must be equal-length lists with ≥ 2 items."})

    pre = np.array(pre_scores, dtype=float)
    post = np.array(post_scores, dtype=float)
    gains = post - pre

    t_stat, p_val = stats.ttest_rel(post, pre)
    d = _cohen_d(pre, post)

    pct_improved = float((gains > 0).mean()) * 100
    pct_sig_gain = float((gains >= 2.0).mean()) * 100  # ≥ 2 points = practically significant

    result = {
        "workshop_id": workshop_id,
        "n_participants": len(pre_scores),
        "mean_pre_score": round(float(pre.mean()), 2),
        "mean_post_score": round(float(post.mean()), 2),
        "mean_gain": round(float(gains.mean()), 2),
        "std_gain": round(float(gains.std(ddof=1)), 2),
        "min_gain": round(float(gains.min()), 2),
        "max_gain": round(float(gains.max()), 2),
        "cohens_d": round(d, 3),
        "effect_size_label": _interpret_d(d),
        "t_statistic": round(float(t_stat), 4),
        "p_value": round(float(p_val), 4),
        "statistically_significant": bool(p_val < 0.05),
        "pct_participants_improved": round(pct_improved, 1),
        "pct_participants_significant_gain": round(pct_sig_gain, 1),
        "interpretation": (
            f"On average participants gained {gains.mean():.1f} points (from {pre.mean():.1f} to {post.mean():.1f}/10). "
            f"Effect size is {_interpret_d(d)} (Cohen's d = {d:.2f}). "
            f"{'The improvement is statistically significant (p < 0.05).' if p_val < 0.05 else 'The improvement is NOT statistically significant (p ≥ 0.05).'} "
            f"{pct_sig_gain:.0f}% of participants gained 2 or more points."
        ),
    }
    return json.dumps(result, indent=2)
