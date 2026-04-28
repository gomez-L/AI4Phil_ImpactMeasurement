"""
Static knowledge documents pre-loaded into the vector store.

Topics:
  1. Impact measurement frameworks (Kirkpatrick, Theory of Change)
  2. Digital skills education best practices
  3. NPS & satisfaction measurement in non-formal education
  4. Community reputation building for NGOs
  5. Feedback-driven continuous improvement
  6. Financial sustainability models for non-profits
  7. Free / subsidised access models
"""
from __future__ import annotations

from langchain_core.documents import Document


KNOWLEDGE_DOCUMENTS: list[Document] = [

    # ── 1. Kirkpatrick's Four Levels ──────────────────────────────────────────
    Document(
        page_content="""
Kirkpatrick's Four-Level Training Evaluation Model
===================================================
Level 1 – Reaction: Measures how participants feel about the training.
Collected via satisfaction surveys immediately after the session.
Key metrics: overall satisfaction score, NPS (Net Promoter Score), open feedback.

Level 2 – Learning: Assesses the increase in knowledge, skills, or attitudes.
Collected via pre- and post-workshop knowledge tests (0–10 scale).
Key metrics: mean score gain, Cohen's d effect size, % of learners with ≥ 2-point gain.
A paired t-test (p < 0.05) confirms whether improvement is statistically significant.

Level 3 – Behaviour: Evaluates whether participants apply what they learned.
Best measured via follow-up surveys 30–90 days after the workshop.
Key metrics: self-reported application rate, manager observation ratings.

Level 4 – Results: Measures the organisational or social impact.
For digital skills non-profits this includes: employment outcomes, community digital
literacy index, partner institution ratings, reduction in digital exclusion.
        """,
        metadata={"source": "Kirkpatrick Partners", "category": "impact_framework"},
    ),

    # ── 2. Theory of Change ───────────────────────────────────────────────────
    Document(
        page_content="""
Theory of Change for Digital Skills Non-Profits
================================================
Inputs: Funding (paid registrations + grants), volunteer instructors, venue/platform,
curriculum materials.

Activities: Delivering workshops on Python, cybersecurity, data literacy, AI tools,
Excel, digital marketing. Offering both onsite (15 CHF) and online (5 CHF) formats.
Providing free spots financed by surplus from paid registrations.

Outputs: Number of workshops, participants trained, free spots offered,
curriculum modules developed.

Outcomes (short-term, 0–6 months):
  • Improved digital knowledge (measured via pre/post tests)
  • Increased confidence with digital tools (Likert self-assessment)
  • New professional skills for job market

Outcomes (medium-term, 6–18 months):
  • Career advancement or employment for participants
  • Increased digital literacy in the community

Impact (long-term, 18+ months):
  • Reduced digital divide in Geneva
  • Recognised city-wide reputation as a trusted digital education provider
        """,
        metadata={"source": "Theory of Change Institute", "category": "impact_framework"},
    ),

    # ── 3. NPS in Non-Formal Education ────────────────────────────────────────
    Document(
        page_content="""
Using NPS (Net Promoter Score) in Workshop Settings
====================================================
NPS = % Promoters (score 9–10) − % Detractors (score 0–6)
Range: −100 to +100. A score above 50 is considered excellent for educational programmes.

Interpretation for digital skills workshops:
  ≥ 70  : World-class. Participants are enthusiastic advocates.
  50–69 : Excellent. Strong word-of-mouth expected.
  30–49 : Good. Room for improvement in specific dimensions.
  0–29  : Acceptable. Significant issues need addressing.
  < 0   : Poor. Systemic problems require urgent action.

Best practices:
  • Collect NPS at end of session AND 30 days later (loyalty NPS).
  • Always pair NPS with a qualitative "Why did you give this score?" prompt.
  • Segment NPS by modality (onsite vs online) — online sessions typically score 5–10 pts lower
    due to engagement and technical barriers.
  • Track trend over time, not just absolute score.
        """,
        metadata={"source": "Bain & Company — NPS Methodology", "category": "satisfaction"},
    ),

    # ── 4. Multi-Dimensional Satisfaction ─────────────────────────────────────
    Document(
        page_content="""
Multi-Dimensional Satisfaction Measurement for Training Programmes
==================================================================
Measure satisfaction across at least five dimensions (1–5 scale):

1. Content quality: Relevance, accuracy, depth, real-world applicability.
   Alert threshold: < 3.5/5. Action: curriculum review with subject matter experts.

2. Organisation: Scheduling, communications, registration process, timing.
   Alert threshold: < 3.5/5. Action: improve admin processes and communications.

3. Instructor/Facilitator: Clarity of explanation, engagement, responsiveness to questions.
   Alert threshold: < 4.0/5. Action: instructor coaching or reassignment.

4. Materials: Slides, handouts, exercises, reference guides.
   Alert threshold: < 3.5/5. Action: materials refresh with participant input.

5. Online platform (for remote sessions): Technical quality, ease of use, interactivity.
   Alert threshold: < 3.5/5. Action: platform change or enhanced tech support.

Aggregate scoring:
  Weighted average = 0.25*content + 0.15*organisation + 0.30*instructor + 0.15*materials + 0.15*overall
  A score ≥ 4.0 represents high satisfaction.
        """,
        metadata={"source": "Training Industry Best Practices", "category": "satisfaction"},
    ),

    # ── 5. Reputation Measurement ─────────────────────────────────────────────
    Document(
        page_content="""
Measuring Community Reputation for NGOs and Non-Profits
========================================================
A Reputation Index for a city-based non-profit can be constructed from four pillars:

1. Stakeholder NPS (weight 35%): Survey of partner organisations, municipalities,
   schools, employers — asking if they would recommend the NGO's programmes.

2. Partner satisfaction (weight 25%): Average rating from institutional partners (0–5).

3. Social & media sentiment (weight 20%): Ratio of positive to total mentions
   across LinkedIn, Twitter, local press, Google Reviews. Score: (pos / total) * 5.

4. Municipal / institutional engagement (weight 20%): Quality and regularity of
   formal relationships with public bodies (0–5 self-assessment or external audit).

Composite formula:
  Reputation Index (0–100) =
    (stakeholder_nps_normalised * 0.35) +
    (partner_satisfaction / 5 * 100 * 0.25) +
    (social_sentiment_score / 5 * 100 * 0.20) +
    (municipal_engagement / 5 * 100 * 0.20)

Benchmarks for Geneva civil society organisations:
  ≥ 75 : Strong civic reputation — eligible for municipal grants
  60–74: Solid — continue building partnerships
  45–59: Moderate — proactive communication campaigns needed
  < 45 : Weak — reputation recovery plan required
        """,
        metadata={"source": "Swiss NPO Reputation Guide", "category": "reputation"},
    ),

    # ── 6. Empirical Feedback Loop ────────────────────────────────────────────
    Document(
        page_content="""
Empirical Continuous Improvement for Training Programmes
=========================================================
An evidence-based feedback loop follows four steps:

COLLECT → ANALYSE → HYPOTHESISE → TEST

1. Collect: Gather post-workshop surveys, open feedback, and follow-up check-ins.
   Collect at two intervals: immediately after session and 30–60 days later.

2. Analyse: Identify recurring patterns.
   - Frequency analysis: which issues are mentioned in ≥ 20% of feedback?
   - Dimension scoring: which satisfaction dimension falls below threshold?
   - Correlation: does low instructor score correlate with low knowledge gain?

3. Hypothesise: For each problem, define a testable improvement hypothesis.
   Example: "If we add a Q&A buffer of 15 min at the end, organisation score will rise ≥ 0.3 pts."

4. Test: Implement change in next 2 workshops, compare results with control cohort.
   Statistical significance threshold: Cohen's d ≥ 0.2 (small effect) or p < 0.10.

Prioritisation matrix (Impact × Effort):
  High impact / Low effort  → Do immediately
  High impact / High effort → Plan for next quarter
  Low impact / Low effort   → Nice to have
  Low impact / High effort  → Deprioritise

Track all implemented changes in a Programme Improvement Log with dates,
hypothesis, result, and decision (keep / revert / iterate).
        """,
        metadata={"source": "Continuous Improvement Handbook for NGOs", "category": "feedback"},
    ),

    # ── 7. Free Spots Financial Model ─────────────────────────────────────────
    Document(
        page_content="""
Financial Sustainability and Free Access Model for Digital Skills Workshops
===========================================================================
Pricing structure (Geneva context):
  • Onsite participation: 15 CHF
  • Online participation: 5 CHF
  • Free spots: funded by surplus from paid registrations

Revenue calculation per workshop:
  Revenue = (n_paid_onsite × 15 CHF) + (n_paid_online × 5 CHF)

Typical cost structure:
  Fixed costs: instructor fee (250–400 CHF), venue rental (0–250 CHF)
  Variable costs: materials per participant (3–8 CHF), admin overhead per participant (2–5 CHF)
  Total cost = fixed + (n_total × variable_per_head)

Free capacity formula:
  Surplus = Revenue − Total cost
  Cost per free participant = variable_per_head (fixed costs already covered by paid attendees)
  Max free spots = max(0, floor(Surplus / cost_per_free_head))

Best practice: Maintain a rolling fund.
  Accumulate surplus from multiple workshops.
  Reserve 20% of surplus as operational buffer.
  Allocate 80% to free spots and bursaries.

Forecasting for upcoming workshops:
  Use historical mean ± 1 std of paid attendance (onsite and online separately).
  Apply a 10% discount to expected revenue for conservative planning (prudence principle).
  Project cost using fixed structure + estimated participants.
  Report: expected free capacity, pessimistic (p10) and optimistic (p90) scenarios.
        """,
        metadata={"source": "Social Enterprise Finance Guide — Switzerland", "category": "financial"},
    ),

    # ── 8. Digital Skills Curriculum Best Practices ───────────────────────────
    Document(
        page_content="""
Best Practices in Digital Skills Curriculum Design
===================================================
Modular curriculum structure (recommended for non-profits):
  Tier 1 – Foundations: digital safety, email, office tools, cloud storage (4h)
  Tier 2 – Productivity: Excel/Sheets, data visualisation, collaboration tools (6h)
  Tier 3 – Professional: Python basics, data literacy, cybersecurity, AI tools (8h)
  Tier 4 – Advanced: web development, automation, data analysis (12h+)

Pedagogical principles:
  • 70-20-10 rule: 70% hands-on exercises, 20% discussion, 10% lecture.
  • Real-world projects: use datasets and scenarios from participants' actual contexts.
  • Peer learning: pair novices with intermediate learners.
  • Spaced repetition: short follow-up exercises sent by email 1 week post-workshop.

Assessment design:
  • Pre-test: 10 questions, mix of conceptual and applied. Administered 10 min before start.
  • Post-test: equivalent difficulty (different questions), administered at end.
  • Minimum detectable effect: 2 points on 0–10 scale = practically significant.

Online adaptation:
  • Max 3h per session (attention fatigue beyond this point).
  • Use breakout rooms for exercises (groups of 3–4).
  • Provide asynchronous recording for review within 72h.
  • Platform latency check: join 10 min early, test audio/video.
        """,
        metadata={"source": "Digital Skills Alliance — Curriculum Framework", "category": "curriculum"},
    ),
]
