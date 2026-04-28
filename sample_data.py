"""
Realistic synthetic data for demonstration and testing.

Generation logic (enforced for every workshop):
    - 8 workshops in total (3 original + 5 additional online workshops)
    - Minimum 30 participants per workshop
    - Last 5 participants are always free slots (payment_type="free")
    - Venue cost is capped at 150 CHF
    - Instructor cost is fixed at 100 CHF (good-cause pricing)
    - Materials, marketing, and admin costs are always 0 CHF

Exports when run as a script:
    - Excel-friendly CSV files (UTF-8 BOM, flat tabular structure)
    - Human-readable structured JSONL files (nested by sections)
"""
from __future__ import annotations

import csv
import json
import random
from pathlib import Path

import config
from schemas import (
    Participant, SatisfactionSurvey, Workshop, WorkshopCosts, ReputationData
)

random.seed(42)

MIN_PARTICIPANTS_PER_WORKSHOP = 30
FREE_PARTICIPANTS_PER_WORKSHOP = 5
PAID_PARTICIPANTS_PER_WORKSHOP = MIN_PARTICIPANTS_PER_WORKSHOP - FREE_PARTICIPANTS_PER_WORKSHOP

INSTRUCTOR_COST_CHF = 100.0
MATERIALS_COST_CHF = 0.0
MARKETING_COST_CHF = 0.0
ADMIN_COST_CHF = 0.0


# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────

def _make_participant(pid: str, modality: str, payment: str,
                      pre: float, gain: float, sat_boost: float = 0.0) -> Participant:
    post = min(10.0, pre + gain + random.uniform(-0.5, 0.5))
    return Participant(
        id=pid,
        payment_type=payment,
        modality=modality,
        pre_score=round(pre, 1),
        post_score=round(max(0, post), 1),
        survey=SatisfactionSurvey(
            content=round(min(5, 3.8 + sat_boost + random.uniform(-0.4, 0.4)), 1),
            organization=round(min(5, 4.2 + sat_boost + random.uniform(-0.3, 0.3)), 1),
            instructor=round(min(5, 4.5 + sat_boost + random.uniform(-0.3, 0.3)), 1),
            materials=round(min(5, 3.5 + sat_boost + random.uniform(-0.5, 0.5)), 1),
            platform=round(min(5, 3.9 + random.uniform(-0.4, 0.4)), 1) if modality == "online" else None,
            overall=round(min(5, 4.0 + sat_boost + random.uniform(-0.3, 0.3)), 1),
            nps=int(min(10, max(0, round(7.5 + sat_boost * 1.5 + random.uniform(-1.5, 1.5))))),
            open_feedback=random.choice([
                "Very practical exercises, I could apply them the same day.",
                "The instructor explained complex concepts clearly.",
                "Would benefit from more hands-on time.",
                "Excellent introduction — looking forward to advanced sessions.",
                "Materials were slightly outdated, but overall very useful.",
                "Great atmosphere, well-organised.",
                "Content was good but we ran out of time at the end.",
                "Would have liked smaller group for Q&A.",
                None,
            ])
        )
    )


def _build_workshop(
    workshop_id: str,
    name: str,
    date: str,
    topic: str,
    modality: str,
    venue_cost_chf: float,
    pre_base: float,
    gain_base: float,
    sat_boost: float,
) -> Workshop:
    """Create a workshop with fixed participant/cost constraints.

    Participant rule:
      - total participants = 30
      - last 5 are free participants

    Cost rule:
      - venue <= 150
      - instructor = 100
      - materials = marketing = admin = 0
    """
    if venue_cost_chf > 150:
        raise ValueError("venue_cost_chf must be <= 150")

    participants: list[Participant] = []

    for i in range(PAID_PARTICIPANTS_PER_WORKSHOP):
        participants.append(
            _make_participant(
                pid=f"{workshop_id}_p{i + 1:02d}",
                modality=modality,
                payment="paid",
                pre=min(9.5, pre_base + (i % 12) * 0.2),
                gain=gain_base,
                sat_boost=sat_boost,
            )
        )

    # The final 5 entries are always free participants.
    for i in range(FREE_PARTICIPANTS_PER_WORKSHOP):
        idx = PAID_PARTICIPANTS_PER_WORKSHOP + i + 1
        participants.append(
            _make_participant(
                pid=f"{workshop_id}_p{idx:02d}",
                modality=modality,
                payment="free",
                pre=max(1.5, pre_base - 0.8),
                gain=gain_base + 0.3,
                sat_boost=sat_boost + 0.1,
            )
        )

    return Workshop(
        id=workshop_id,
        name=name,
        date=date,
        topic=topic,
        participants=participants,
        costs=WorkshopCosts(
            venue=venue_cost_chf,
            materials=MATERIALS_COST_CHF,
            instructor=INSTRUCTOR_COST_CHF,
            marketing=MARKETING_COST_CHF,
            admin=ADMIN_COST_CHF,
        ),
    )


# ──────────────────────────────────────────────────────────────────────────────
# Workshops (3 original + 5 additional online workshops)
# ──────────────────────────────────────────────────────────────────────────────

WORKSHOP_1 = _build_workshop(
    workshop_id="ws_2026_001",
    name="Python Basics for Beginners",
    date="2026-01-20",
    topic="Python programming",
    modality="onsite",
    venue_cost_chf=150.0,
    pre_base=3.0,
    gain_base=3.1,
    sat_boost=0.2,
)

WORKSHOP_2 = _build_workshop(
    workshop_id="ws_2026_002",
    name="Cybersecurity Essentials",
    date="2026-02-10",
    topic="Cybersecurity awareness",
    modality="online",
    venue_cost_chf=0.0,
    pre_base=3.9,
    gain_base=2.7,
    sat_boost=-0.1,
)

WORKSHOP_3 = _build_workshop(
    workshop_id="ws_2026_003",
    name="Data Literacy for Non-Profits",
    date="2026-03-15",
    topic="Data literacy",
    modality="onsite",
    venue_cost_chf=120.0,
    pre_base=3.4,
    gain_base=2.5,
    sat_boost=0.1,
)

WORKSHOP_4 = _build_workshop(
    workshop_id="ws_2026_004",
    name="Statistics Beginners",
    date="2026-04-05",
    topic="statistics beginners",
    modality="online",
    venue_cost_chf=0.0,
    pre_base=2.6,
    gain_base=2.9,
    sat_boost=0.0,
)

WORKSHOP_5 = _build_workshop(
    workshop_id="ws_2026_005",
    name="Statistics Intermediate",
    date="2026-04-25",
    topic="statistics intermediate",
    modality="online",
    venue_cost_chf=0.0,
    pre_base=4.4,
    gain_base=2.3,
    sat_boost=0.0,
)

WORKSHOP_6 = _build_workshop(
    workshop_id="ws_2026_006",
    name="Introduction to Programming in R",
    date="2026-05-12",
    topic="introduction to programming in R",
    modality="online",
    venue_cost_chf=0.0,
    pre_base=2.9,
    gain_base=3.0,
    sat_boost=0.1,
)

WORKSHOP_7 = _build_workshop(
    workshop_id="ws_2026_007",
    name="Hypothesis Testing",
    date="2026-05-30",
    topic="hypothesis testing",
    modality="online",
    venue_cost_chf=0.0,
    pre_base=3.8,
    gain_base=2.6,
    sat_boost=0.0,
)

WORKSHOP_8 = _build_workshop(
    workshop_id="ws_2026_008",
    name="Data Quality",
    date="2026-06-18",
    topic="data quality",
    modality="online",
    venue_cost_chf=0.0,
    pre_base=3.3,
    gain_base=2.8,
    sat_boost=0.1,
)

# ──────────────────────────────────────────────────────────────────────────────
# Historical workshop index (for financial forecasting)
# ──────────────────────────────────────────────────────────────────────────────

ALL_WORKSHOPS: list[Workshop] = [
    WORKSHOP_1,
    WORKSHOP_2,
    WORKSHOP_3,
    WORKSHOP_4,
    WORKSHOP_5,
    WORKSHOP_6,
    WORKSHOP_7,
    WORKSHOP_8,
]

# ──────────────────────────────────────────────────────────────────────────────
# Reputation data for Geneva – Q1 2026
# ──────────────────────────────────────────────────────────────────────────────

REPUTATION_Q1_2026 = ReputationData(
    period="Q1 2026",
    city="Geneva",
    nps_stakeholders=62.0,
    testimonials=[
        "This organisation is filling a real gap in digital education in our city.",
        "The workshops helped our volunteers tremendously. Highly recommended.",
        "We've seen direct improvement in how our staff handles data after their programme.",
        "Affordable and accessible — exactly what the community needed.",
        "A bit more advanced content would be welcome for those who complete the basics.",
        "The free spots policy is admirable. It truly democratises digital skills.",
        "Their instructor was patient and knowledgeable. Will send more colleagues.",
    ],
    social_mentions=[
        {"text": "Loved the Python workshop! Learned more in one day than months self-studying. #DigitalSkills", "sentiment": "pos", "platform": "LinkedIn"},
        {"text": "Free digital skills workshops in Geneva — highly recommended for job seekers!", "sentiment": "pos", "platform": "Twitter"},
        {"text": "Registration process was a bit confusing but the content was great.", "sentiment": "neu", "platform": "Google"},
        {"text": "Excellent initiative, wish there were more sessions per month.", "sentiment": "pos", "platform": "LinkedIn"},
        {"text": "Online session had some audio issues but instructor handled it well.", "sentiment": "neu", "platform": "Twitter"},
        {"text": "Best investment of a Saturday in years. Great community too.", "sentiment": "pos", "platform": "LinkedIn"},
    ],
    partner_ratings=[4.5, 4.2, 4.8, 4.0, 4.6],
    press_coverage_count=3,
    municipal_engagement_score=4.1,
)

# ──────────────────────────────────────────────────────────────────────────────
# Upcoming workshops plan (for financial prediction)
# ──────────────────────────────────────────────────────────────────────────────

UPCOMING_WORKSHOPS_PLAN = [
    {"name": "Statistics Beginners",                 "modality": "online", "date": "2026-07-05"},
    {"name": "Statistics Intermediate",              "modality": "online", "date": "2026-07-19"},
    {"name": "Introduction to Programming in R",     "modality": "online", "date": "2026-08-03"},
    {"name": "Hypothesis Testing",                   "modality": "online", "date": "2026-08-17"},
    {"name": "Data Quality",                         "modality": "online", "date": "2026-08-31"},
]


# ──────────────────────────────────────────────────────────────────────────────
# Export utilities (CSV + JSONL)
# ──────────────────────────────────────────────────────────────────────────────

def _write_csv(path: Path, rows: list[dict]) -> None:
    if not rows:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(rows[0].keys())
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def _write_jsonl(path: Path, records: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for record in records:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")


def _workshop_summary_rows() -> list[dict]:
    rows: list[dict] = []
    for ws in ALL_WORKSHOPS:
        rows.append(
            {
                "workshop_id": ws.id,
                "name": ws.name,
                "date": ws.date,
                "topic": ws.topic,
                "participants_total": len(ws.participants),
                "n_paid_onsite": ws.n_paid_onsite,
                "n_paid_online": ws.n_paid_online,
                "n_free": ws.n_free,
                "revenue_chf": round(ws.revenue, 2),
                "cost_venue_chf": ws.costs.venue,
                "cost_materials_chf": ws.costs.materials,
                "cost_instructor_chf": ws.costs.instructor,
                "cost_marketing_chf": ws.costs.marketing,
                "cost_admin_chf": ws.costs.admin,
                "total_cost_chf": round(ws.costs.total, 2),
                "surplus_chf": round(ws.surplus, 2),
            }
        )
    return rows


def _participant_rows() -> list[dict]:
    rows: list[dict] = []
    for ws in ALL_WORKSHOPS:
        for p in ws.participants:
            rows.append(
                {
                    "workshop_id": ws.id,
                    "workshop_name": ws.name,
                    "workshop_date": ws.date,
                    "participant_id": p.id,
                    "payment_type": p.payment_type,
                    "modality": p.modality,
                    "pre_score": p.pre_score,
                    "post_score": p.post_score,
                    "knowledge_gain": round(p.post_score - p.pre_score, 2),
                    "survey_content": p.survey.content,
                    "survey_organization": p.survey.organization,
                    "survey_instructor": p.survey.instructor,
                    "survey_materials": p.survey.materials,
                    "survey_platform": p.survey.platform,
                    "survey_overall": p.survey.overall,
                    "survey_nps": p.survey.nps,
                    "survey_open_feedback": p.survey.open_feedback,
                }
            )
    return rows


def _reputation_summary_rows() -> list[dict]:
    return [
        {
            "period": REPUTATION_Q1_2026.period,
            "city": REPUTATION_Q1_2026.city,
            "nps_stakeholders": REPUTATION_Q1_2026.nps_stakeholders,
            "partner_ratings_count": len(REPUTATION_Q1_2026.partner_ratings),
            "partner_ratings_mean": round(
                sum(REPUTATION_Q1_2026.partner_ratings) / max(len(REPUTATION_Q1_2026.partner_ratings), 1), 2
            ),
            "social_mentions_count": len(REPUTATION_Q1_2026.social_mentions),
            "testimonials_count": len(REPUTATION_Q1_2026.testimonials),
            "press_coverage_count": REPUTATION_Q1_2026.press_coverage_count,
            "municipal_engagement_score": REPUTATION_Q1_2026.municipal_engagement_score,
        }
    ]


def _reputation_testimonial_rows() -> list[dict]:
    return [
        {
            "period": REPUTATION_Q1_2026.period,
            "city": REPUTATION_Q1_2026.city,
            "testimonial_index": i,
            "testimonial_text": text,
        }
        for i, text in enumerate(REPUTATION_Q1_2026.testimonials, start=1)
    ]


def _reputation_mentions_rows() -> list[dict]:
    return [
        {
            "period": REPUTATION_Q1_2026.period,
            "city": REPUTATION_Q1_2026.city,
            "mention_index": i,
            "platform": mention.get("platform"),
            "sentiment": mention.get("sentiment"),
            "text": mention.get("text"),
        }
        for i, mention in enumerate(REPUTATION_Q1_2026.social_mentions, start=1)
    ]


def _upcoming_workshops_rows() -> list[dict]:
    return [
        {
            "sequence": i,
            "name": workshop["name"],
            "modality": workshop["modality"],
            "date": workshop["date"],
        }
        for i, workshop in enumerate(UPCOMING_WORKSHOPS_PLAN, start=1)
    ]


def _workshops_structured_jsonl() -> list[dict]:
    records: list[dict] = []
    for ws in ALL_WORKSHOPS:
        participants = []
        for p in ws.participants:
            participants.append(
                {
                    "participant": {
                        "id": p.id,
                        "payment_type": p.payment_type,
                        "modality": p.modality,
                    },
                    "scores": {
                        "pre": p.pre_score,
                        "post": p.post_score,
                        "gain": round(p.post_score - p.pre_score, 2),
                    },
                    "survey": {
                        "content": p.survey.content,
                        "organization": p.survey.organization,
                        "instructor": p.survey.instructor,
                        "materials": p.survey.materials,
                        "platform": p.survey.platform,
                        "overall": p.survey.overall,
                        "nps": p.survey.nps,
                        "open_feedback": p.survey.open_feedback,
                    },
                }
            )

        records.append(
            {
                "entity": "workshop",
                "workshop": {
                    "id": ws.id,
                    "name": ws.name,
                    "date": ws.date,
                    "topic": ws.topic,
                },
                "pricing": {
                    "onsite_price_chf": config.ONSITE_PRICE_CHF,
                    "online_price_chf": config.ONLINE_PRICE_CHF,
                },
                "attendance": {
                    "participants_total": len(ws.participants),
                    "n_paid_onsite": ws.n_paid_onsite,
                    "n_paid_online": ws.n_paid_online,
                    "n_free": ws.n_free,
                },
                "finance": {
                    "revenue_chf": round(ws.revenue, 2),
                    "costs": {
                        "venue_chf": ws.costs.venue,
                        "materials_chf": ws.costs.materials,
                        "instructor_chf": ws.costs.instructor,
                        "marketing_chf": ws.costs.marketing,
                        "admin_chf": ws.costs.admin,
                        "total_chf": round(ws.costs.total, 2),
                    },
                    "surplus_chf": round(ws.surplus, 2),
                },
                "participants": participants,
            }
        )
    return records


def _reputation_structured_jsonl() -> list[dict]:
    return [
        {
            "entity": "reputation_snapshot",
            "scope": {
                "period": REPUTATION_Q1_2026.period,
                "city": REPUTATION_Q1_2026.city,
            },
            "metrics": {
                "nps_stakeholders": REPUTATION_Q1_2026.nps_stakeholders,
                "partner_ratings": REPUTATION_Q1_2026.partner_ratings,
                "partner_ratings_mean": round(
                    sum(REPUTATION_Q1_2026.partner_ratings) / max(len(REPUTATION_Q1_2026.partner_ratings), 1), 2
                ),
                "press_coverage_count": REPUTATION_Q1_2026.press_coverage_count,
                "municipal_engagement_score": REPUTATION_Q1_2026.municipal_engagement_score,
            },
            "social_mentions": REPUTATION_Q1_2026.social_mentions,
            "testimonials": REPUTATION_Q1_2026.testimonials,
        }
    ]


def _upcoming_workshops_structured_jsonl() -> list[dict]:
    return [
        {
            "entity": "upcoming_workshop",
            "sequence": i,
            "workshop": {
                "name": workshop["name"],
                "modality": workshop["modality"],
                "date": workshop["date"],
            },
        }
        for i, workshop in enumerate(UPCOMING_WORKSHOPS_PLAN, start=1)
    ]


def export_sample_data(output_dir: Path | None = None) -> list[Path]:
    output_dir = output_dir or Path(config.DATA_DIR)
    output_dir.mkdir(parents=True, exist_ok=True)

    csv_outputs = {
        "workshops.csv": _workshop_summary_rows(),
        "workshop_participants.csv": _participant_rows(),
        "reputation_summary.csv": _reputation_summary_rows(),
        "reputation_testimonials.csv": _reputation_testimonial_rows(),
        "reputation_social_mentions.csv": _reputation_mentions_rows(),
        "upcoming_workshops.csv": _upcoming_workshops_rows(),
    }

    jsonl_outputs = {
        "workshops_structured.jsonl": _workshops_structured_jsonl(),
        "reputation_structured.jsonl": _reputation_structured_jsonl(),
        "upcoming_workshops_structured.jsonl": _upcoming_workshops_structured_jsonl(),
    }

    written_files: list[Path] = []
    for filename, rows in csv_outputs.items():
        path = output_dir / filename
        _write_csv(path, rows)
        written_files.append(path)

    for filename, records in jsonl_outputs.items():
        path = output_dir / filename
        _write_jsonl(path, records)
        written_files.append(path)

    return written_files


if __name__ == "__main__":
    generated = export_sample_data()
    print("Export complete. Files written:")
    for path in generated:
        print(f"- {path}")
