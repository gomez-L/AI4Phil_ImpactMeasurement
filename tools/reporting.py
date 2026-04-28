"""
Tool: generate_impact_report
Formats a structured impact report from pre-computed analysis results.
"""
from __future__ import annotations

import json
from datetime import datetime
from typing import Annotated

from langchain_core.tools import tool

from observability import observe


def _rating_bar(score: float, max_score: float = 5.0, width: int = 10) -> str:
    """Returns a simple ASCII progress bar."""
    filled = int(round(score / max_score * width))
    return "█" * filled + "░" * (width - filled)


@tool
@observe(name="tool_generate_impact_report")
def generate_impact_report(
    workshop_name: Annotated[str, "Name of the workshop"],
    workshop_date: Annotated[str, "Date of the workshop (ISO format)"],
    knowledge_analysis: Annotated[dict | str, "JSON from analyze_knowledge_impact"],
    satisfaction_analysis: Annotated[dict | str, "JSON from analyze_satisfaction"],
    financial_analysis: Annotated[dict | str | None, "JSON from calculate_free_workshop_capacity (optional)"] = None,
    reputation_analysis: Annotated[dict | str | None, "JSON from measure_reputation (optional)"] = None,
    feedback_analysis: Annotated[dict | str | None, "JSON from synthesize_feedback_improvements (optional)"] = None,
    organisation_name: Annotated[str, "Name of the non-profit organisation"] = "DigitalSkills Geneva",
) -> str:
    """
    Compile all impact analysis results into a formatted Markdown impact report.
    Accepts either dict or JSON string for each analysis input.
    """
    def _parse(data):
        if isinstance(data, str):
            try:
                return json.loads(data)
            except Exception:
                return {}
        return data or {}

    ka = _parse(knowledge_analysis)
    sa = _parse(satisfaction_analysis)
    fa = _parse(financial_analysis)
    ra = _parse(reputation_analysis)
    fb = _parse(feedback_analysis)

    generated_at = datetime.now().strftime("%d %B %Y, %H:%M")

    lines = [
        f"# Impact Report — {workshop_name}",
        f"**Organisation:** {organisation_name}  ",
        f"**Workshop date:** {workshop_date}  ",
        f"**Report generated:** {generated_at}  ",
        "",
        "---",
        "",
        "## 1. Knowledge Impact",
    ]

    if ka:
        mean_pre = ka.get("mean_pre_score", "N/A")
        mean_post = ka.get("mean_post_score", "N/A")
        mean_gain = ka.get("mean_gain", "N/A")
        d = ka.get("cohens_d", "N/A")
        sig = ka.get("statistically_significant", False)
        pct_imp = ka.get("pct_participants_improved", "N/A")
        pct_sig = ka.get("pct_participants_significant_gain", "N/A")
        n = ka.get("n_participants", "N/A")

        lines += [
            f"| Metric | Value |",
            f"|--------|-------|",
            f"| Participants | {n} |",
            f"| Mean pre-score | {mean_pre}/10 |",
            f"| Mean post-score | {mean_post}/10 |",
            f"| Mean knowledge gain | **+{mean_gain} pts** |",
            f"| Effect size (Cohen's d) | {d} — {ka.get('effect_size_label', '')} |",
            f"| Statistically significant | {'✅ Yes (p < 0.05)' if sig else '❌ No (p ≥ 0.05)'} |",
            f"| Participants improved | {pct_imp}% |",
            f"| Significant gain (≥ 2 pts) | {pct_sig}% |",
            "",
            f"> {ka.get('interpretation', '')}",
            "",
        ]
    else:
        lines += ["_No knowledge assessment data provided._", ""]

    lines += ["## 2. Participant Satisfaction"]

    if sa:
        ds = sa.get("dimension_scores", {})
        composite = sa.get("composite_satisfaction", "N/A")
        nps = sa.get("nps", "N/A")
        nps_label = sa.get("nps_label", "")
        n_resp = sa.get("n_responses", "N/A")
        alerts = sa.get("alerts", [])

        lines += [
            f"**Responses:** {n_resp}  **NPS:** {nps} ({nps_label})  **Composite:** {composite}/5",
            "",
            "| Dimension | Mean | Rating |",
            "|-----------|------|--------|",
        ]
        for dim, scores in ds.items():
            mean = scores.get("mean", 0)
            bar = _rating_bar(mean)
            lines.append(f"| {dim.capitalize()} | {mean}/5 | {bar} |")

        if alerts:
            lines += ["", "**⚠ Alerts:**"]
            for a in alerts:
                lines.append(f"- {a}")

        if sa.get("open_feedback_sample"):
            lines += ["", "**Participant voices:**"]
            for fb_text in sa.get("open_feedback_sample", [])[:3]:
                lines.append(f"> *\"{fb_text}\"*")

        lines += ["", f"> {sa.get('interpretation', '')}", ""]
    else:
        lines += ["_No satisfaction data provided._", ""]

    if ra:
        lines += [
            "## 3. Reputation in the Community",
            "",
            f"| Metric | Value |",
            f"|--------|-------|",
            f"| Reputation Index | **{ra.get('reputation_index', 'N/A')}/100** |",
            f"| Label | {ra.get('reputation_label', 'N/A')} |",
            f"| Period | {ra.get('period', 'N/A')} |",
            f"| City | {ra.get('city', 'N/A')} |",
            "",
        ]
        pb = ra.get("pillar_breakdown", {})
        if pb:
            lines += ["**Pillar breakdown:**", ""]
            for pillar, data in pb.items():
                score = data.get("normalised_score", "")
                weight = data.get("weight", "")
                lines.append(f"- **{pillar.replace('_', ' ').title()}** ({weight}): {score}/100")
        if ra.get("positive_themes"):
            lines += ["", "**Positive themes:**"]
            for t in ra.get("positive_themes", []):
                lines.append(f"> *\"{t}\"*")
        lines += ["", f"> {ra.get('interpretation', '')}", ""]

    if fb:
        lines += ["## 4. Improvement Recommendations", ""]
        log = fb.get("programme_improvement_log", [])
        if log:
            lines += [
                "| Priority | Issue | Action | Hypothesis |",
                "|----------|-------|--------|------------|",
            ]
            for entry in log:
                prio = entry.get("priority", "")
                issue = entry.get("issue", "").replace("_", " ")
                action = entry.get("action", "")[:80]
                hyp = entry.get("hypothesis", "")[:80]
                lines.append(f"| {prio} | {issue} | {action}… | {hyp}… |")
        trends = fb.get("cross_workshop_trends", {})
        if trends:
            lines += [
                "",
                f"**NPS trend:** {trends.get('nps_trend', 'N/A')}  |  "
                f"**Knowledge gain trend:** {trends.get('knowledge_gain_trend', 'N/A')}",
            ]
        lines += ["", f"> {fb.get('interpretation', '')}", ""]

    if fa:
        mc = fa.get("upcoming_forecast", {}).get("monte_carlo_results", {})
        hs = fa.get("historical_summary", {})
        pricing = fa.get("pricing", {})
        lines += [
            "## 5. Free Workshop Capacity Forecast",
            "",
            f"*Pricing: {pricing.get('onsite_paid_chf', 5)} CHF onsite · {pricing.get('online_paid_chf', 15)} CHF online*",
            "",
            "| Scenario | Revenue (CHF) | Free Spots |",
            "|----------|--------------|------------|",
            f"| Expected | {mc.get('expected_revenue_chf', 'N/A')} | **{mc.get('expected_free_spots', 'N/A')}** |",
            f"| Pessimistic (p10) | {mc.get('revenue_p10_chf', 'N/A')} | {mc.get('pessimistic_free_spots_p10', 'N/A')} |",
            f"| Optimistic (p90) | {mc.get('revenue_p90_chf', 'N/A')} | {mc.get('optimistic_free_spots_p90', 'N/A')} |",
            "",
            f"Historical avg surplus per workshop: **{hs.get('avg_surplus_chf', 'N/A')} CHF**  |  "
            f"Probability of positive surplus: **{mc.get('probability_surplus_positive', 'N/A')}%**",
            "",
            f"> {fa.get('interpretation', '')}",
            "",
        ]

    lines += [
        "---",
        f"*Report generated by the Impact Measurement Agent — {organisation_name}*",
    ]

    report_md = "\n".join(lines)

    return json.dumps({
        "report_markdown": report_md,
        "sections_included": [
            s for s, d in [
                ("knowledge_impact", bool(ka)),
                ("satisfaction", bool(sa)),
                ("reputation", bool(ra)),
                ("improvements", bool(fb)),
                ("financial_forecast", bool(fa)),
            ] if d
        ],
    }, indent=2)
