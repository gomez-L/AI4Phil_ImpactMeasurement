"""
Tool: calculate_free_workshop_capacity
Projects revenue, costs, and free-spot capacity for upcoming workshops
using historical attendance statistics and Monte Carlo simulation.

Pricing:
    Onsite paid: 15 CHF
    Online paid: 5 CHF
  Free: cost covered by surplus from paid participants
"""
from __future__ import annotations

import json
from typing import Annotated

import numpy as np
from langchain_core.tools import tool

from config import ONSITE_PRICE_CHF, ONLINE_PRICE_CHF
from observability import observe


# ──────────────────────────────────────────────────────────────────────────────
# Monte Carlo projection
# ──────────────────────────────────────────────────────────────────────────────

def _monte_carlo(
    onsite_paid_hist: list[float],
    online_paid_hist: list[float],
    fixed_cost_per_ws: float,
    variable_cost_per_head: float,
    n_upcoming: int,
    n_simulations: int = 10_000,
    prudence_discount: float = 0.10,
    buffer_reserve: float = 0.20,
) -> dict:
    rng = np.random.default_rng(42)

    op_mean, op_std = np.mean(onsite_paid_hist), np.std(onsite_paid_hist, ddof=1)
    oo_mean, oo_std = np.mean(online_paid_hist), np.std(online_paid_hist, ddof=1)

    # Simulate attendance for each upcoming workshop
    onsite_sim = rng.normal(op_mean, op_std + 1e-6, (n_simulations, n_upcoming)).clip(0)
    online_sim = rng.normal(oo_mean, oo_std + 1e-6, (n_simulations, n_upcoming)).clip(0)

    # Revenue per simulation (with prudence discount)
    revenue_sim = (
        onsite_sim * ONSITE_PRICE_CHF + online_sim * ONLINE_PRICE_CHF
    ) * (1 - prudence_discount)

    # Costs per simulation
    total_participants_sim = onsite_sim + online_sim
    cost_sim = fixed_cost_per_ws + total_participants_sim * variable_cost_per_head
    cost_total_sim = cost_sim.sum(axis=1)

    # Surplus
    revenue_total_sim = revenue_sim.sum(axis=1)
    surplus_sim = (revenue_total_sim - cost_total_sim).clip(0)

    # Reserve 20% operational buffer
    allocatable_sim = surplus_sim * (1 - buffer_reserve)

    # Free spots (divide by variable cost per head, since fixed already covered by paid)
    free_spots_sim = (allocatable_sim / variable_cost_per_head).clip(0)

    return {
        "expected_revenue_chf": round(float(revenue_total_sim.mean()), 2),
        "expected_cost_chf": round(float(cost_total_sim.mean()), 2),
        "expected_surplus_chf": round(float(surplus_sim.mean()), 2),
        "expected_free_spots": int(free_spots_sim.mean()),
        "pessimistic_free_spots_p10": int(np.percentile(free_spots_sim, 10)),
        "optimistic_free_spots_p90": int(np.percentile(free_spots_sim, 90)),
        "revenue_p10_chf": round(float(np.percentile(revenue_total_sim, 10)), 2),
        "revenue_p90_chf": round(float(np.percentile(revenue_total_sim, 90)), 2),
        "probability_surplus_positive": round(float((surplus_sim > 0).mean()) * 100, 1),
    }


@tool
@observe(name="tool_calculate_free_workshop_capacity")
def calculate_free_workshop_capacity(
    historical_workshops: Annotated[
        list[dict],
        (
            "Historical workshop records. Each dict: "
            "id (str), date (str), n_paid_onsite (int), n_paid_online (int), "
            "n_free (int), fixed_cost_chf (float), variable_cost_per_head_chf (float)."
        ),
    ],
    upcoming_workshops: Annotated[
        list[dict],
        (
            "Upcoming workshop plans. Each dict: name (str), modality ('onsite'|'online'|'hybrid'), date (str). "
            "Used for per-workshop breakdown."
        ),
    ],
    fixed_cost_per_workshop_chf: Annotated[
        float,
        "Estimated fixed cost per upcoming workshop in CHF (instructor + venue)."
    ] = 550.0,
    variable_cost_per_head_chf: Annotated[
        float,
        "Estimated variable cost per participant in CHF (materials + admin)."
    ] = 8.0,
    buffer_reserve_pct: Annotated[
        float,
        "Percentage of surplus kept as operational buffer (0–1, default 0.20)."
    ] = 0.20,
) -> str:
    """
    Forecast financial capacity to offer free workshop spots in upcoming sessions.

    Uses historical paid attendance (onsite: 15 CHF, online: 5 CHF) to project
    revenue minus costs, then calculates how many free spots can be funded.
    Monte Carlo simulation provides pessimistic (p10) and optimistic (p90) scenarios.
    """
    if not historical_workshops:
        return json.dumps({"error": "No historical workshop data provided."})

    # ── Historical summary ───────────────────────────────────────────────────
    onsite_paid_hist = [float(w.get("n_paid_onsite", 0)) for w in historical_workshops]
    online_paid_hist = [float(w.get("n_paid_online", 0)) for w in historical_workshops]

    past_revenues = [
        w.get("n_paid_onsite", 0) * ONSITE_PRICE_CHF + w.get("n_paid_online", 0) * ONLINE_PRICE_CHF
        for w in historical_workshops
    ]
    past_costs = [
        w.get("fixed_cost_chf", fixed_cost_per_workshop_chf)
        + (w.get("n_paid_onsite", 0) + w.get("n_paid_online", 0) + w.get("n_free", 0))
        * w.get("variable_cost_per_head_chf", variable_cost_per_head_chf)
        for w in historical_workshops
    ]
    past_surpluses = [r - c for r, c in zip(past_revenues, past_costs)]

    # ── Monte Carlo for upcoming workshops ──────────────────────────────────
    n_upcoming = len(upcoming_workshops)
    mc = _monte_carlo(
        onsite_paid_hist=onsite_paid_hist,
        online_paid_hist=online_paid_hist,
        fixed_cost_per_ws=fixed_cost_per_workshop_chf,
        variable_cost_per_head=variable_cost_per_head_chf,
        n_upcoming=n_upcoming,
        buffer_reserve=buffer_reserve_pct,
    )

    # ── Per-workshop expected breakdown ─────────────────────────────────────
    avg_onsite = float(np.mean(onsite_paid_hist))
    avg_online = float(np.mean(online_paid_hist))
    per_workshop = []
    for ws in upcoming_workshops:
        modality = ws.get("modality", "onsite")
        if modality == "online":
            exp_rev = avg_online * ONLINE_PRICE_CHF * 0.90
            exp_cost = fixed_cost_per_workshop_chf + avg_online * variable_cost_per_head_chf
        else:
            exp_rev = avg_onsite * ONSITE_PRICE_CHF * 0.90
            exp_cost = fixed_cost_per_workshop_chf + avg_onsite * variable_cost_per_head_chf
        surplus = max(0, exp_rev - exp_cost)
        free_spots = int(surplus * (1 - buffer_reserve_pct) / variable_cost_per_head_chf)
        per_workshop.append({
            "name": ws.get("name"),
            "date": ws.get("date"),
            "modality": modality,
            "expected_revenue_chf": round(exp_rev, 2),
            "expected_cost_chf": round(exp_cost, 2),
            "expected_surplus_chf": round(surplus, 2),
            "expected_free_spots": free_spots,
        })

    result = {
        "pricing": {
            "onsite_paid_chf": ONSITE_PRICE_CHF,
            "online_paid_chf": ONLINE_PRICE_CHF,
        },
        "historical_summary": {
            "n_workshops": len(historical_workshops),
            "avg_paid_onsite": round(float(np.mean(onsite_paid_hist)), 1),
            "avg_paid_online": round(float(np.mean(online_paid_hist)), 1),
            "avg_revenue_chf": round(float(np.mean(past_revenues)), 2),
            "avg_cost_chf": round(float(np.mean(past_costs)), 2),
            "avg_surplus_chf": round(float(np.mean(past_surpluses)), 2),
            "total_surplus_accumulated_chf": round(sum(max(0, s) for s in past_surpluses), 2),
        },
        "upcoming_forecast": {
            "n_upcoming_workshops": n_upcoming,
            "cost_assumptions": {
                "fixed_cost_per_workshop_chf": fixed_cost_per_workshop_chf,
                "variable_cost_per_head_chf": variable_cost_per_head_chf,
                "buffer_reserve_pct": buffer_reserve_pct * 100,
                "prudence_revenue_discount_pct": 10,
            },
            "monte_carlo_results": mc,
            "per_workshop_breakdown": per_workshop,
        },
        "interpretation": (
            f"Based on {len(historical_workshops)} historical workshops, "
            f"the expected revenue over {n_upcoming} upcoming workshops is "
            f"{mc['expected_revenue_chf']} CHF (after 10% prudence discount). "
            f"Estimated costs: {mc['expected_cost_chf']} CHF. "
            f"Expected surplus available for free spots: {mc['expected_surplus_chf']} CHF "
            f"({buffer_reserve_pct*100:.0f}% buffer reserved). "
            f"Projected free spots: {mc['expected_free_spots']} "
            f"(pessimistic p10: {mc['pessimistic_free_spots_p10']}, "
            f"optimistic p90: {mc['optimistic_free_spots_p90']}). "
            f"Probability of positive surplus: {mc['probability_surplus_positive']}%."
        ),
    }
    return json.dumps(result, indent=2)
