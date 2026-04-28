IMPACT MEASUREMENT PROJECT - FULL PROGRAMME GUIDE, METHODS, AND RESULTS
========================================================================

This document is the complete narrative and technical reference for the
Impact Measurement Agent project. It is written so that a new reader can
understand:

1. The nonprofit story and operating model
2. The exact research questions (Q1 to Q8)
3. Which notebook answers which question
4. How data is generated and stored
5. How metrics are calculated
6. What the current results mean for decision making
7. How to reproduce all outputs


0) QUICK CONTEXT SNAPSHOT
-------------------------
Programme location: Geneva, Switzerland
Programme type: digital-skills workshops for social impact
Measurement period represented in the synthetic dataset: Q1 2026
Workshop portfolio in current dataset: 8 workshops
Participants per workshop: 30 (25 paid + 5 free)

Current core pricing (corrected and validated):
- ONSITE_PRICE_CHF = 15.0
- ONLINE_PRICE_CHF = 5.0

Current model/provider stack:
- LLM provider: Google Gemini API
- Main model configured: gemma-4-31b-it
- API key env var: GEMINI_API_KEY (fallback GOOGLE_API_KEY)
- Agent framework: LangGraph ReAct
- Observability: LangFuse is optional and can be disabled


1) STORY OF THE NONPROFIT
-------------------------
The nonprofit is a Geneva-based digital inclusion initiative. Its mission is
to help people gain practical digital skills that improve employability,
everyday digital autonomy, and civic participation.

The programme design is intentionally dual-objective:
- Inclusion objective: always protect access for people with limited means
- Sustainability objective: remain financially viable across repeated cohorts

Operating policy per workshop:
- 30 seats total
- 25 paid seats
- 5 free seats (reserved for financially constrained participants)

This project turns that mission into measurable evidence across learning,
satisfaction, reputation, and financial sustainability.


2) RESEARCH QUESTIONS (Q1 TO Q8)
--------------------------------
The full impact exercise is structured around the following eight questions:

Q1. Is the nonprofit programme for digital skills financially sustainable?
Q2. What is participant satisfaction?
Q3. Do attendees actually learn?
Q4. Which workshops are the most successful?
Q5. How much money is available for the next programme iteration?
Q6. By how much can we increase the percentage of free seats while remaining
    financially sustainable and still growing?
Q7. How many extra free seats can be offered using the Q1 2026 surplus?
Q8. Which feedback aspects should be used to improve the programme?


3) ANALYTICAL LENS AND NOTEBOOK MAPPING
---------------------------------------
The analysis is intentionally split into four notebooks so each thematic lens
is coherent and deep.

Notebook 1: nb_01_financial_sustainability.ipynb
- Questions answered: Q1, Q5, Q6, Q7
- Lens:
  - revenue/cost/surplus at workshop and portfolio level
  - cumulative surplus and runway logic
  - break-even and sensitivity frontier for free-seat expansion
  - scenario analysis for growth vs inclusion trade-offs

Notebook 2: nb_02_learning_outcomes.ipynb
- Questions answered: Q3 and part of Q4 (success measured by learning)
- Lens:
  - pre-post learning gains
  - paired t-test, Wilcoxon test, Cohen's d effect size
  - per-workshop learning success ranking with uncertainty

Notebook 3: nb_03_satisfaction_reputation.ipynb
- Questions answered: Q2 and part of Q4 (success measured by participant
  experience and reputation)
- Lens:
  - multi-dimensional satisfaction (content, organization, instructor,
    materials, platform, overall)
  - NPS decomposition
  - workshop-level satisfaction heatmaps
  - external reputation indicators and composite reputation index

Notebook 4: nb_04_feedback_nlp.ipynb
- Questions answered: Q8
- Lens:
  - open-text feedback mining
  - frequency analysis and bigrams
  - TF-IDF for workshop-distinctive terms
  - LDA topic modelling for latent themes
  - actionable improvement plan with effort/impact prioritization

How Q4 is operationalized in practice:
- There is no single definition of "most successful".
- This project treats Q4 as multi-criteria success:
  - learning success (Notebook 2)
  - satisfaction success (Notebook 3)
  - financial contribution (Notebook 1)


4) DATA GENERATION DESIGN (sample_data.py)
-------------------------------------------
The synthetic generator in sample_data.py defines a fixed simulation policy.

Portfolio scope:
- 8 workshops in total
- 3 original/core workshops
- 5 additional online workshops:
  1) Statistics Beginners
  2) Statistics Intermediate
  3) Intro to Programming in R
  4) Hypothesis Testing
  5) Data Quality

Participant logic per workshop:
- total participants = 30
- first 25 are paid, last 5 are free
- minimum participant constraint respected (>= 30)

Cost logic per workshop:
- venue <= 150 CHF (onsite only; online venue cost is 0)
- instructor = 100 CHF
- materials = 0 CHF
- marketing = 0 CHF
- admin = 0 CHF

Financial intent of this simulation:
- keep costs explicit and simple
- isolate pricing/mix effects on sustainability
- preserve guaranteed inclusion via 5 free seats per workshop


5) PRICING AND FINANCIAL FORMULAS
---------------------------------
Current participant prices:
- paid onsite: 15 CHF
- paid online: 5 CHF
- free seat: 0 CHF

Core formulas:
- Revenue = (n_paid_onsite * 15) + (n_paid_online * 5)
- Total Cost = venue + instructor + materials + marketing + admin
- Surplus = Revenue - Total Cost

Example economics under current rules:
- Typical onsite (25 paid onsite, venue 150):
  - Revenue = 25 * 15 = 375 CHF
  - Cost = 150 + 100 = 250 CHF
  - Surplus = +125 CHF
- Typical online (25 paid online):
  - Revenue = 25 * 5 = 125 CHF
  - Cost = 0 + 100 = 100 CHF
  - Surplus = +25 CHF

Important interpretation:
- Onsite workshops now carry stronger unit surplus than online workshops.
- Online workshops remain useful for scale and accessibility, but with lower
  margin in this configuration.


6) WHAT IS STORED IN data/
--------------------------
CSV outputs:
- data/workshops.csv
- data/workshop_participants.csv
- data/reputation_summary.csv
- data/reputation_testimonials.csv
- data/reputation_social_mentions.csv
- data/upcoming_workshops.csv

Structured JSONL outputs:
- data/workshops_structured.jsonl
- data/reputation_structured.jsonl
- data/upcoming_workshops_structured.jsonl

Agent run outputs (from main.py demos/custom query):
- data/generated/*.json

Vector database:
- data/chroma_db/
- collection name: workshop_knowledge


7) KNOWLEDGE BASE AND RAG CONTENT
---------------------------------
The project ships curated knowledge snippets (framework references) used by the
agent for retrieval-augmented answers.

Loader-defined document set:
- 8 documents loaded into the vector store
- mirrored as .txt files in knowledge_base/

Topics covered include:
- Kirkpatrick impact logic and theory of change
- NPS interpretation
- training quality best practices
- nonprofit reputation guidance
- continuous improvement methods
- social enterprise finance guidance
- curriculum framing for digital skills


8) PROGRAMME METRICS BY DIMENSION
---------------------------------
A) Learning (impact quality)
- Inputs: pre_score, post_score
- Derived metric: knowledge_gain = post_score - pre_score
- Statistical lens used:
  - paired t-test
  - Wilcoxon signed-rank test
  - Cohen's d

B) Satisfaction (participant experience)
- Survey dimensions:
  - content
  - organization
  - instructor
  - materials
  - platform (online)
  - overall
  - NPS item (0 to 10)
  - open feedback text

C) Reputation (external trust)
- Indicators:
  - stakeholder NPS
  - partner ratings
  - social mentions and sentiment
  - municipal engagement
  - testimonials
  - press coverage count

D) Financial sustainability and inclusion capacity
- Indicators:
  - workshop and portfolio surplus
  - cumulative surplus
  - free-seat expansion potential
  - scenario-based growth viability


9) CURRENT RESULTS (Q1 2026 DATA SNAPSHOT)
------------------------------------------
Portfolio composition:
- workshops: 8
- participants: 240 total
- paid participants: 200
  - paid onsite: 50
  - paid online: 150
- free participants: 40

Learning outcomes:
- average knowledge gain: 2.79 points

Satisfaction outcomes:
- mean overall satisfaction: 4.07 / 5
- mean NPS item score: 7.54 / 10

Reputation outcomes:
- stakeholder NPS: 62.0
- partner rating mean: 4.42 / 5
- social mentions: 6
- testimonials: 7
- press coverage: 3
- municipal engagement: 4.1 / 5

Financial outcomes:
- total revenue: 2,500 CHF
- total costs: 1,070 CHF
- total surplus: 1,430 CHF
- workshops with positive surplus: 6 / 8

Strategic reading of this result:
- Inclusion target is met (5 free seats per workshop).
- Portfolio sustainability is positive (surplus > 0).
- Quality signals are strong (learning gain + high satisfaction + strong
  reputation metrics).


10) DIRECT ANSWER SUMMARY FOR Q1 TO Q8
--------------------------------------
Q1 (sustainability):
- Yes in this scenario; total surplus is positive.

Q2 (satisfaction):
- High overall satisfaction with strong NPS profile.

Q3 (learning):
- Attendees learn; mean gain is positive and material.

Q4 (most successful workshops):
- Depends on criterion. "Most successful" is different by learning,
  satisfaction, and financial contribution. Use cross-notebook ranking.

Q5 (money for next iteration):
- Portfolio surplus from current cycle is available as reinvestment capacity.

Q6 (increase free-seat share while sustainable):
- Feasible up to scenario-specific thresholds; see Notebook 1 sensitivity
  frontier and break-even sections.

Q7 (extra free seats from Q1 2026 surplus):
- Quantified in Notebook 1 using surplus allocation logic and per-seat unit
  economics.

Q8 (feedback aspects to improve):
- Main improvement themes from NLP analysis:
  - increase hands-on time
  - refresh materials
  - improve pacing/time management
  - improve Q&A group structure
  - reinforce online platform quality controls


11) HOW TO RUN THE PROJECT END TO END
-------------------------------------
Environment setup:
1. Create or use Python 3.12 virtual env (project currently validated on
   .venv312)
2. Install dependencies:
   pip install -r requirements.txt
3. Load environment:
   cp .env.example .env
   set GEMINI_API_KEY=<your_key>

Run agent demos while disabling LangFuse tracing:
- set -a && source .env.example && set +a && LANGFUSE_ENABLED=false ./.venv312/bin/python main.py

Run a single demo:
- ./.venv312/bin/python main.py --demo 1

Run a custom query:
- ./.venv312/bin/python main.py --query "your question"

Regenerate dataset exports:
- ./.venv312/bin/python sample_data.py

Open and run the notebooks:
- nb_01_financial_sustainability.ipynb
- nb_02_learning_outcomes.ipynb
- nb_03_satisfaction_reputation.ipynb
- nb_04_feedback_nlp.ipynb


12) IMPLEMENTATION NOTES FOR READERS
------------------------------------
Agent/LLM stack:
- Provider migration completed from OpenAI path to Gemini path
- Chat model integration uses ChatGoogleGenerativeAI in agent/graph.py
- LangGraph create_react_agent uses prompt=SYSTEM_PROMPT

Observability behavior:
- LangFuse is behind a config gate (LANGFUSE_ENABLED)
- analyses were run with LANGFUSE_ENABLED=false in this exercise

Data persistence behavior:
- CLI outputs are saved to data/generated with timestamped json files
- vector store persists locally under data/chroma_db


13) LIMITATIONS AND HOW TO INTERPRET RESPONSIBLY
------------------------------------------------
This is a synthetic but structured exercise. Interpret with care:

1) Synthetic data limitation
- Values are generated from explicit rules and plausible ranges; they are not
  observed field data.

2) Causality limitation
- Pre-post improvements indicate positive movement but do not alone prove
  causal attribution without stronger experimental design.

3) Forecast uncertainty
- Free-seat expansion scenarios depend on assumptions for demand, workshop mix,
  and cost stability.

4) NLP corpus size limitation
- Text topic modeling is informative for pattern discovery but based on a small
  corpus in this simulation.


14) PRACTICAL MANAGEMENT TAKEAWAYS
----------------------------------
1. Preserve guaranteed inclusion (5 free seats minimum per workshop).
2. Keep a balanced portfolio mix and monitor unit economics continuously.
3. Use learning + satisfaction + financial + reputation together; avoid
   single-metric decisions.
4. Use Notebook 4 recommendations as the next-cycle quality backlog.
5. Re-run full measurement every cycle to track trend, not only one-off status.


15) FILES ADDED FOR IMPACT ANALYSIS COMMUNICATION
-------------------------------------------------
Analysis notebooks in project root:
- nb_01_financial_sustainability.ipynb
- nb_02_learning_outcomes.ipynb
- nb_03_satisfaction_reputation.ipynb
- nb_04_feedback_nlp.ipynb

Knowledge base plain-text exports in knowledge_base/:
- loader_doc_01_impact_framework_kirkpatrick_partners.txt
- loader_doc_02_impact_framework_theory_of_change_institute.txt
- loader_doc_03_satisfaction_bain_company_nps_methodology.txt
- loader_doc_04_satisfaction_training_industry_best_practices.txt
- loader_doc_05_reputation_swiss_npo_reputation_guide.txt
- loader_doc_06_feedback_continuous_improvement_handbook_for_ngos.txt
- loader_doc_07_financial_social_enterprise_finance_guide_switzerl.txt
- loader_doc_08_curriculum_digital_skills_alliance_curriculum_frame.txt


END OF DOCUMENT
