"""
Tool: measure_reputation
Computes a composite Reputation Index (0–100) for the non-profit in its city.
"""
from __future__ import annotations

import json
from typing import Annotated

import numpy as np
from langchain_core.tools import tool

from observability import observe


def _sentiment_score(mentions: list[dict]) -> float:
    """
    Compute a sentiment score 0–5 from social mentions.
    Each mention must have 'sentiment': 'pos' | 'neu' | 'neg'.
    """
    if not mentions:
        return 3.0  # neutral default
    weights = {"pos": 5.0, "neu": 3.0, "neg": 1.0}
    scores = [weights.get(m.get("sentiment", "neu"), 3.0) for m in mentions]
    return float(np.mean(scores))


def _normalise_nps(nps: float) -> float:
    """Normalise NPS from [-100, 100] → [0, 100]."""
    return (nps + 100) / 2


def _reputation_label(index: float) -> str:
    if index >= 75:
        return "Strong — eligible for municipal grants and co-branding"
    elif index >= 60:
        return "Solid — continue building partnerships"
    elif index >= 45:
        return "Moderate — proactive communication campaigns needed"
    else:
        return "Weak — reputation recovery plan required"


@tool
@observe(name="tool_measure_reputation")
def measure_reputation(
    period: Annotated[str, "Reporting period (e.g. 'Q1 2026')"],
    city: Annotated[str, "City name"],
    nps_stakeholders: Annotated[float, "NPS from institutional stakeholders (-100 to 100)"],
    partner_ratings: Annotated[list[float], "Partner satisfaction ratings (0–5 each)"],
    social_mentions: Annotated[
        list[dict],
        "List of {text, sentiment ('pos'/'neu'/'neg'), platform} dicts"
    ],
    municipal_engagement_score: Annotated[float, "Municipal engagement quality score (0–5)"],
    testimonials: Annotated[list[str], "Free-text testimonials from stakeholders"] = [],
    press_coverage_count: Annotated[int, "Number of press / media mentions in period"] = 0,
) -> str:
    """
    Compute the composite Reputation Index for the non-profit in its city.

    Pillars and weights:
      35% — Stakeholder NPS (normalised)
      25% — Partner satisfaction (mean rating)
      20% — Social / media sentiment
      20% — Municipal engagement

    Returns the index (0–100), label, pillar breakdown, and qualitative insights.
    """
    # Pillar computations
    stakeholder_pillar = _normalise_nps(nps_stakeholders)  # 0–100

    partner_pillar = (float(np.mean(partner_ratings)) / 5 * 100) if partner_ratings else 50.0

    sentiment_raw = _sentiment_score(social_mentions)  # 0–5
    social_pillar = sentiment_raw / 5 * 100

    municipal_pillar = municipal_engagement_score / 5 * 100

    # Composite
    index = (
        stakeholder_pillar * 0.35
        + partner_pillar * 0.25
        + social_pillar * 0.20
        + municipal_pillar * 0.20
    )

    # Sentiment breakdown
    sentiment_counts = {"pos": 0, "neu": 0, "neg": 0}
    for m in social_mentions:
        s = m.get("sentiment", "neu")
        sentiment_counts[s] = sentiment_counts.get(s, 0) + 1

    total_mentions = len(social_mentions)

    # Themes from testimonials (keyword extraction)
    positive_themes: list[str] = []
    improvement_themes: list[str] = []
    positive_kw = ["excellent", "great", "helpful", "accessible", "clear", "recommend", "love", "free", "admirable"]
    improve_kw = ["confusing", "advanced", "small group", "more sessions", "issue", "bit", "would like"]
    for t in testimonials:
        tl = t.lower()
        if any(k in tl for k in positive_kw):
            positive_themes.append(t[:100])
        if any(k in tl for k in improve_kw):
            improvement_themes.append(t[:100])

    result = {
        "period": period,
        "city": city,
        "reputation_index": round(index, 1),
        "reputation_label": _reputation_label(index),
        "pillar_breakdown": {
            "stakeholder_nps": {
                "raw_nps": nps_stakeholders,
                "normalised_score": round(stakeholder_pillar, 1),
                "weight": "35%",
            },
            "partner_satisfaction": {
                "mean_rating": round(float(np.mean(partner_ratings)), 2) if partner_ratings else None,
                "n_ratings": len(partner_ratings),
                "normalised_score": round(partner_pillar, 1),
                "weight": "25%",
            },
            "social_sentiment": {
                "total_mentions": total_mentions,
                "positive": sentiment_counts["pos"],
                "neutral": sentiment_counts["neu"],
                "negative": sentiment_counts["neg"],
                "sentiment_score_0_5": round(sentiment_raw, 2),
                "normalised_score": round(social_pillar, 1),
                "weight": "20%",
            },
            "municipal_engagement": {
                "score": municipal_engagement_score,
                "normalised_score": round(municipal_pillar, 1),
                "weight": "20%",
            },
        },
        "press_coverage_count": press_coverage_count,
        "positive_themes": positive_themes[:3],
        "improvement_themes": improvement_themes[:3],
        "interpretation": (
            f"Reputation Index for period {period} in {city}: {index:.1f}/100 — {_reputation_label(index)}. "
            f"Stakeholder NPS of {nps_stakeholders} is the strongest driver. "
            f"{sentiment_counts['pos']} positive social mentions out of {total_mentions} total. "
            f"Press coverage: {press_coverage_count} mentions."
        ),
    }
    return json.dumps(result, indent=2)
