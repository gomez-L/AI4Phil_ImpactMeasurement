"""
main.py — CLI entry point and demo runner for the Impact Measurement Agent.

Usage:
    python main.py                  # run all demo scenarios
    python main.py --query "..."    # single custom query
    python main.py --demo 2         # run a specific demo (1–5)
    python main.py --diagram        # print the agent graph diagram

Prerequisites:
    1. pip install -r requirements.txt
    2. cp .env.example .env  →  set GEMINI_API_KEY (and optionally LangFuse keys)
    3. python main.py
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.rule import Rule

import config

console = Console()


# ──────────────────────────────────────────────────────────────────────────────
# Data helpers
# ──────────────────────────────────────────────────────────────────────────────

OUTPUT_DIR = Path(config.DATA_DIR) / "generated"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def _slugify(value: str) -> str:
    return "".join(ch.lower() if ch.isalnum() else "_" for ch in value).strip("_")


def _save_result(title: str, query: str, response: str, thread_id: str) -> Path:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = OUTPUT_DIR / f"{timestamp}_{_slugify(title)[:80]}.json"
    payload = {
        "title": title,
        "thread_id": thread_id,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "query": query,
        "response": response,
    }
    output_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return output_path

def _workshop_to_agent_payload(ws) -> dict:
    """Convert a Workshop schema object to plain dicts for the agent."""
    return {
        "id": ws.id,
        "name": ws.name,
        "date": ws.date,
        "pre_scores": [p.pre_score for p in ws.participants],
        "post_scores": [p.post_score for p in ws.participants],
        "surveys": [
            {
                "content": p.survey.content,
                "organization": p.survey.organization,
                "instructor": p.survey.instructor,
                "materials": p.survey.materials,
                "platform": p.survey.platform,
                "overall": p.survey.overall,
                "nps": p.survey.nps,
                "open_feedback": p.survey.open_feedback,
            }
            for p in ws.participants
        ],
        "modality": "online" if all(p.modality == "online" for p in ws.participants) else "onsite",
        "n_paid_onsite": ws.n_paid_onsite,
        "n_paid_online": ws.n_paid_online,
        "n_free": ws.n_free,
        "fixed_cost_chf": ws.costs.venue + ws.costs.instructor,
        "variable_cost_per_head_chf": (ws.costs.materials + ws.costs.admin) / max(len(ws.participants), 1),
    }


# ──────────────────────────────────────────────────────────────────────────────
# Demo scenarios
# ──────────────────────────────────────────────────────────────────────────────

def demo_1_knowledge_impact():
    """Demo 1: Knowledge impact analysis for Python Basics workshop."""
    from sample_data import WORKSHOP_1

    ws = _workshop_to_agent_payload(WORKSHOP_1)
    query = (
        f"Analyse the knowledge impact for the workshop '{ws['name']}' held on {ws['date']}. "
        f"Here are the pre-scores: {ws['pre_scores']} "
        f"and post-scores: {ws['post_scores']}. "
        f"Workshop ID: {ws['id']}. "
        "Also look up in the knowledge base how to interpret Cohen's d for training programmes."
    )
    return "1 — Knowledge Impact Analysis", query


def demo_2_satisfaction():
    """Demo 2: Multi-dimensional satisfaction + NPS for Cybersecurity workshop."""
    from sample_data import WORKSHOP_2

    ws = _workshop_to_agent_payload(WORKSHOP_2)
    query = (
        f"Analyse participant satisfaction for '{ws['name']}' (workshop ID: {ws['id']}, "
        f"date: {ws['date']}, modality: online). "
        f"Here are the survey results: {json.dumps(ws['surveys'][:8])}. "
        "Identify any dimensions that need urgent attention and check NPS benchmarks in the knowledge base."
    )
    return "2 — Satisfaction Analysis", query


def demo_3_reputation():
    """Demo 3: Reputation index for Geneva, Q1 2026."""
    from sample_data import REPUTATION_Q1_2026

    r = REPUTATION_Q1_2026
    query = (
        f"Measure the reputation of our non-profit in {r.city} for {r.period}. "
        f"Stakeholder NPS: {r.nps_stakeholders}. "
        f"Partner ratings: {r.partner_ratings}. "
        f"Social mentions: {json.dumps(r.social_mentions)}. "
        f"Municipal engagement score: {r.municipal_engagement_score}. "
        f"Testimonials: {json.dumps(r.testimonials[:4])}. "
        f"Press coverage: {r.press_coverage_count} mentions. "
        "Also query the knowledge base for reputation benchmarks for Swiss NGOs."
    )
    return "3 — Reputation Measurement", query


def demo_4_feedback_improvements():
    """Demo 4: Empirical improvement plan from 3 workshops of feedback."""
    from sample_data import ALL_WORKSHOPS

    workshops_payload = []
    for ws in ALL_WORKSHOPS:
        p = _workshop_to_agent_payload(ws)
        feedback_texts = [
            s["open_feedback"] for s in p["surveys"] if s.get("open_feedback")
        ]
        dim_scores = {}
        for dim in ["content", "organization", "instructor", "materials", "overall"]:
            vals = [s[dim] for s in p["surveys"] if s.get(dim) is not None]
            if vals:
                dim_scores[dim] = round(sum(vals) / len(vals), 2)

        pre = p["pre_scores"]
        post = p["post_scores"]
        mean_gain = round(sum(po - pr for pr, po in zip(pre, post)) / len(pre), 2)
        nps_vals = [s["nps"] for s in p["surveys"] if "nps" in s]
        nps = round(
            (sum(1 for v in nps_vals if v >= 9) - sum(1 for v in nps_vals if v <= 6))
            / len(nps_vals) * 100,
            1,
        ) if nps_vals else 0.0

        workshops_payload.append({
            "id": p["id"],
            "name": ws.name,
            "date": ws.date,
            "feedback_texts": feedback_texts,
            "dimension_scores": dim_scores,
            "mean_gain": mean_gain,
            "nps": nps,
        })

    query = (
        "Based on feedback from our last three workshops, generate an empirical improvement plan. "
        f"Workshop data: {json.dumps(workshops_payload)}. "
        "Prioritise improvements using the impact/effort matrix and generate testable hypotheses. "
        "Also check the knowledge base for best practices on continuous improvement in training programmes."
    )
    return "4 — Empirical Feedback & Improvement Plan", query


def demo_5_financial_forecast():
    """Demo 5: Free-spot financial forecast for next 5 workshops."""
    from sample_data import ALL_WORKSHOPS, UPCOMING_WORKSHOPS_PLAN

    historical = [
        {
            "id": ws.id,
            "date": ws.date,
            "n_paid_onsite": ws.n_paid_onsite,
            "n_paid_online": ws.n_paid_online,
            "n_free": ws.n_free,
            "fixed_cost_chf": ws.costs.venue + ws.costs.instructor,
            "variable_cost_per_head_chf": round(
                (ws.costs.materials + ws.costs.admin) / max(len(ws.participants), 1), 2
            ),
        }
        for ws in ALL_WORKSHOPS
    ]

    query = (
        "Predict how many free workshop spots we can offer over the next 5 workshops. "
        f"Historical data: {json.dumps(historical)}. "
        f"Upcoming workshops: {json.dumps(UPCOMING_WORKSHOPS_PLAN)}. "
        "Assume fixed cost per workshop = 550 CHF, variable cost per participant = 8 CHF. "
        "Remember: onsite participants pay 15 CHF, online pay 5 CHF. "
        "Also query the knowledge base for the recommended financial model for free-spot capacity."
    )
    return "5 — Free Workshop Capacity Forecast", query


DEMOS = {
    1: demo_1_knowledge_impact,
    2: demo_2_satisfaction,
    3: demo_3_reputation,
    4: demo_4_feedback_improvements,
    5: demo_5_financial_forecast,
}


# ──────────────────────────────────────────────────────────────────────────────
# Runner
# ──────────────────────────────────────────────────────────────────────────────

def run_demo(demo_fn, thread_id: str):
    """Execute a single demo scenario, print results, and save them under data/generated."""
    from agent.graph import run

    title, query = demo_fn()
    console.print(Rule(f"[bold cyan]{title}[/bold cyan]"))
    console.print(Panel(query[:400] + ("…" if len(query) > 400 else ""), title="[dim]Query[/dim]", border_style="dim"))

    console.print("\n[dim]Running agent…[/dim]\n")
    try:
        response = run(query, thread_id=thread_id, session_name=title)
        console.print(Markdown(response))
        output_path = _save_result(title, query, response, thread_id)
        console.print(f"\n[dim]Saved output to {output_path}[/dim]")
    except Exception as exc:
        console.print(f"[red]Error:[/red] {exc}")
        raise
    console.print()


def main():
    parser = argparse.ArgumentParser(description="Impact Measurement Agent — Demo CLI")
    parser.add_argument("--query", type=str, help="Run a single custom query")
    parser.add_argument("--demo", type=int, choices=[1, 2, 3, 4, 5],
                        help="Run a specific demo scenario (1–5)")
    parser.add_argument("--diagram", action="store_true",
                        help="Print the agent graph diagram")
    parser.add_argument("--thread", type=str, default="demo",
                        help="Thread ID for conversation memory (default: 'demo')")
    args = parser.parse_args()

    console.print(Panel.fit(
        "[bold green]Impact Measurement Agent[/bold green]\n"
        "[dim]Digital Skills Workshops · Geneva · LangGraph + LangFuse[/dim]",
        border_style="green",
    ))

    if args.diagram:
        from agent.graph import get_graph_diagram
        console.print(get_graph_diagram())
        sys.exit(0)

    if args.query:
        from agent.graph import run
        console.print(Rule("[bold cyan]Custom Query[/bold cyan]"))
        response = run(args.query, thread_id=args.thread)
        console.print(Markdown(response))
        output_path = _save_result("custom_query", args.query, response, args.thread)
        console.print(f"\n[dim]Saved output to {output_path}[/dim]")
        sys.exit(0)

    if args.demo:
        run_demo(DEMOS[args.demo], thread_id=args.thread)
        sys.exit(0)

    # Run all demos
    for demo_num, demo_fn in DEMOS.items():
        run_demo(demo_fn, thread_id=f"demo_{demo_num}")

    console.print(Rule("[bold green]All demos complete[/bold green]"))


if __name__ == "__main__":
    main()
