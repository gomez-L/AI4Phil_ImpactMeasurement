"""
Pydantic data models for the impact measurement domain.
All monetary values are in CHF.
"""
from __future__ import annotations

from typing import Optional
from pydantic import BaseModel, Field


# ──────────────────────────────────────────────────────────────────────────────
# Participant-level models
# ──────────────────────────────────────────────────────────────────────────────

class SatisfactionSurvey(BaseModel):
    content: float = Field(..., ge=0, le=5, description="Content quality (0–5)")
    organization: float = Field(..., ge=0, le=5, description="Workshop organisation (0–5)")
    instructor: float = Field(..., ge=0, le=5, description="Instructor/facilitator (0–5)")
    materials: float = Field(..., ge=0, le=5, description="Materials & resources (0–5)")
    platform: Optional[float] = Field(None, ge=0, le=5, description="Online platform (0–5, online only)")
    overall: float = Field(..., ge=0, le=5, description="Overall experience (0–5)")
    nps: int = Field(..., ge=0, le=10, description="Net Promoter Score (0–10)")
    open_feedback: Optional[str] = Field(None, description="Free-text feedback")


class Participant(BaseModel):
    id: str
    payment_type: str = Field(..., pattern="^(paid|free)$")
    modality: str = Field(..., pattern="^(onsite|online)$")
    pre_score: float = Field(..., ge=0, le=10, description="Pre-workshop test score (0–10)")
    post_score: float = Field(..., ge=0, le=10, description="Post-workshop test score (0–10)")
    survey: SatisfactionSurvey


# ──────────────────────────────────────────────────────────────────────────────
# Workshop-level model
# ──────────────────────────────────────────────────────────────────────────────

class WorkshopCosts(BaseModel):
    venue: float = Field(default=0.0, description="Venue rental (CHF)")
    materials: float = Field(default=0.0, description="Printed / digital materials (CHF)")
    instructor: float = Field(default=0.0, description="Instructor fee (CHF)")
    marketing: float = Field(default=0.0, description="Marketing & outreach (CHF)")
    admin: float = Field(default=0.0, description="Admin & overhead (CHF)")

    @property
    def total(self) -> float:
        return self.venue + self.materials + self.instructor + self.marketing + self.admin


class Workshop(BaseModel):
    id: str
    name: str
    date: str  # ISO format YYYY-MM-DD
    topic: str
    participants: list[Participant]
    costs: WorkshopCosts

    # ── Derived helpers ──────────────────────────────────────────────────────
    @property
    def n_paid_onsite(self) -> int:
        return sum(1 for p in self.participants if p.payment_type == "paid" and p.modality == "onsite")

    @property
    def n_paid_online(self) -> int:
        return sum(1 for p in self.participants if p.payment_type == "paid" and p.modality == "online")

    @property
    def n_free(self) -> int:
        return sum(1 for p in self.participants if p.payment_type == "free")

    @property
    def revenue(self) -> float:
        from config import ONSITE_PRICE_CHF, ONLINE_PRICE_CHF
        return self.n_paid_onsite * ONSITE_PRICE_CHF + self.n_paid_online * ONLINE_PRICE_CHF

    @property
    def surplus(self) -> float:
        return self.revenue - self.costs.total


# ──────────────────────────────────────────────────────────────────────────────
# Reputation data
# ──────────────────────────────────────────────────────────────────────────────

class ReputationData(BaseModel):
    period: str
    city: str = "Geneva"
    nps_stakeholders: float = Field(..., ge=-100, le=100, description="NPS from city stakeholders")
    testimonials: list[str] = Field(default_factory=list)
    social_mentions: list[dict] = Field(
        default_factory=list,
        description="Each item: {text: str, sentiment: pos/neg/neu, platform: str}"
    )
    partner_ratings: list[float] = Field(default_factory=list, description="Partner satisfaction (0–5)")
    press_coverage_count: int = Field(default=0)
    municipal_engagement_score: Optional[float] = Field(None, ge=0, le=5)


# ──────────────────────────────────────────────────────────────────────────────
# Impact report
# ──────────────────────────────────────────────────────────────────────────────

class ImpactReport(BaseModel):
    workshop_id: str
    knowledge_gain_mean: float
    knowledge_gain_effect_size: float
    knowledge_gain_pvalue: float
    satisfaction_scores: dict[str, float]
    nps: float
    reputation_index: Optional[float]
    recommendations: list[str]
    financial_surplus_chf: float
    free_capacity_forecast: int
    narrative: str
