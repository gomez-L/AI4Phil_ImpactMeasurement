# Impact Measurement Agent

Production-grade impact analytics + reasoning agent for a digital-skills nonprofit programme in Geneva.

Stack: Python, LangGraph ReAct, LangChain tools, Gemini (`gemma-4-31b-it`), local ChromaDB RAG, optional LangFuse tracing.

---

## What This Project Answers (Q1–Q8)

This repository is organized around 8 programme-evaluation questions:

1. Is the programme financially sustainable?
2. What is participant satisfaction?
3. Do attendees learn?
4. Which workshops are most successful?
5. How much budget is available for the next iteration?
6. How much can free-seat share increase while staying sustainable?
7. How many additional free seats can be funded from Q1 2026 surplus?
8. Which feedback themes should drive improvements?

Notebook mapping:

| Notebook | Questions covered | Analytical lens |
|---|---|---|
| `nb_01_financial_sustainability.ipynb` | Q1, Q5, Q6, Q7 | Revenue/cost/surplus, break-even, free-seat frontier |
| `nb_02_learning_outcomes.ipynb` | Q3 + part of Q4 | Pre/post gain stats, paired tests, effect size |
| `nb_03_satisfaction_reputation.ipynb` | Q2 + part of Q4 | NPS, dimension scores, reputation index |
| `nb_04_feedback_nlp.ipynb` | Q8 | TF-IDF, LDA topics, improvement priorities |

---

## System Architecture

```mermaid
flowchart LR
    U["User Query"] --> M["main.py CLI"]
    M --> G["agent/graph.py ReAct Agent"]
    G --> P["agent/prompts.py SYSTEM_PROMPT"]
    G --> T["tools/__init__.py ALL_TOOLS"]

    T --> A["tools/assessment.py"]
    T --> S["tools/satisfaction.py"]
    T --> R["tools/reputation.py"]
    T --> F["tools/feedback.py"]
    T --> Fin["tools/financial.py"]
    T --> KBQ["tools/kb_query.py"]
    T --> Rep["tools/reporting.py"]

    KBQ --> KBS["knowledge_base/store.py"]
    KBS --> KBL["knowledge_base/loader.py"]
    KBL --> KBTxt["knowledge_base files (.txt)"]

    G --> OBS["observability.py build_run_config and observe"]
    M --> OUT["data/generated JSON outputs"]

    SD["sample_data.py"] --> M
    CFG["config.py and .env"] --> G
    CFG --> SD
```

---

## Flow Diagram: What Happens When `main.py` Runs

The diagram below is file-level and execution-ordered.

```mermaid
sequenceDiagram
    autonumber
    participant CLI as main.py
    participant CFG as config.py
    participant SD as sample_data.py
    participant AG as agent/graph.py
    participant PR as agent/prompts.py
    participant TO as tools/__init__.py
    participant TL as tools/*.py
    participant KB as knowledge_base/store.py
    participant LD as knowledge_base/loader.py
    participant OB as observability.py
    participant DG as data/generated/*.json

    CLI->>CFG: Load env + constants (DATA_DIR, MODEL_NAME, prices, flags)
    CLI->>CLI: Parse args (--demo/--query/--diagram/--thread)

    alt --diagram
        CLI->>AG: get_graph_diagram()
        AG-->>CLI: Mermaid graph text
    else --demo or --query
        opt Demo mode
            CLI->>SD: Import workshop/reputation objects
            SD-->>CLI: Structured payload inputs
        end

        CLI->>AG: run(query, thread_id, session_name)
        AG->>PR: Load SYSTEM_PROMPT
        AG->>TO: Load ALL_TOOLS
        AG->>OB: Attach callbacks/config (LangFuse optional)

        loop ReAct iterations
            AG->>TL: Call selected tool
            opt Tool needs knowledge base
                TL->>KB: get_vectorstore()
                KB->>LD: Load 8 documents if rebuild/index needed
            end
            TL-->>AG: JSON/tool result
        end

        AG-->>CLI: Final answer text
        CLI->>DG: Save query + response JSON artifact
    end
```

---

## Project Structure (Updated)

```text
impact_agent/
├── main.py                          # CLI entry point + demo runner + JSON output persistence
├── config.py                        # env settings, model config, pricing, LangFuse flag
├── schemas.py                       # domain data models (Pydantic)
├── sample_data.py                   # 8-workshop synthetic dataset + CSV/JSONL export
├── observability.py                 # LangFuse callbacks / observe decorator
├── requirements.txt
├── README.md
├── README.txt
│
├── agent/
│   ├── prompts.py                   # SYSTEM_PROMPT with domain instructions
│   └── graph.py                     # ReAct agent (run/stream/get_graph_diagram)
│
├── tools/
│   ├── __init__.py                  # ALL_TOOLS registry
│   ├── assessment.py                # learning impact stats
│   ├── satisfaction.py              # NPS + dimension analysis
│   ├── reputation.py                # reputation index logic
│   ├── feedback.py                  # empirical improvement synthesis
│   ├── financial.py                 # Monte Carlo free-seat capacity forecast
│   ├── kb_query.py                  # RAG query tool
│   └── reporting.py                 # markdown impact reporting
│
├── knowledge_base/
│   ├── loader.py                    # 8 framework documents
│   ├── store.py                     # ChromaDB init/retrieval
│   └── loader_doc_*.txt             # exported plain-text framework docs
│
├── data/
│   ├── workshops.csv
│   ├── workshop_participants.csv
│   ├── reputation_summary.csv
│   ├── reputation_testimonials.csv
│   ├── reputation_social_mentions.csv
│   ├── upcoming_workshops.csv
│   ├── workshops_structured.jsonl
│   ├── reputation_structured.jsonl
│   ├── upcoming_workshops_structured.jsonl
│   ├── chroma_db/
│   └── generated/                   # demo/custom-query outputs from main.py
│
├── nb_01_financial_sustainability.ipynb
├── nb_02_learning_outcomes.ipynb
├── nb_03_satisfaction_reputation.ipynb
└── nb_04_feedback_nlp.ipynb
```

---

## Rich Domain Schemas (Updated)

### 1) Pydantic Domain Model (`schemas.py`)

```mermaid
classDiagram
    class SatisfactionSurvey {
        +float content (0..5)
        +float organization (0..5)
        +float instructor (0..5)
        +float materials (0..5)
        +float? platform (0..5, online)
        +float overall (0..5)
        +int nps (0..10)
        +str? open_feedback
    }

    class Participant {
        +str id
        +str payment_type (paid|free)
        +str modality (onsite|online)
        +float pre_score (0..10)
        +float post_score (0..10)
    }

    class WorkshopCosts {
        +float venue
        +float materials
        +float instructor
        +float marketing
        +float admin
        +float total (derived)
    }

    class Workshop {
        +str id
        +str name
        +str date
        +str topic
        +int n_paid_onsite (derived)
        +int n_paid_online (derived)
        +int n_free (derived)
        +float revenue (derived)
        +float surplus (derived)
    }

    class ReputationData {
        +str period
        +str city
        +float nps_stakeholders (-100..100)
        +list testimonials
        +list social_mentions
        +list partner_ratings (0..5)
        +int press_coverage_count
        +float? municipal_engagement_score (0..5)
    }

    class ImpactReport {
        +str workshop_id
        +float knowledge_gain_mean
        +float knowledge_gain_effect_size
        +float knowledge_gain_pvalue
        +dict satisfaction_scores
        +float nps
        +float? reputation_index
        +list recommendations
        +float financial_surplus_chf
        +int free_capacity_forecast
        +str narrative
    }

    Participant --> SatisfactionSurvey : contains
    Workshop --> Participant : participants[*]
    Workshop --> WorkshopCosts : costs
```

### 2) Synthetic Programme Policy Schema (`sample_data.py`)

```mermaid
flowchart TD
    A[Workshop Policy] --> B[Participants per workshop = 30]
    B --> C[Paid = 25]
    B --> D[Free = 5]

    A --> E[Cost Policy]
    E --> E1[Venue <= 150 CHF]
    E --> E2[Instructor = 100 CHF]
    E --> E3[Materials = 0 CHF]
    E --> E4[Marketing = 0 CHF]
    E --> E5[Admin = 0 CHF]

    A --> F[Pricing]
    F --> F1[Onsite paid = 15 CHF]
    F --> F2[Online paid = 5 CHF]
```

### 3) Exported Data Schemas (`data/*.csv`)

`workshops.csv`

| Column | Type | Description |
|---|---|---|
| workshop_id | string | Workshop identifier |
| name | string | Workshop name |
| date | date | Workshop date |
| topic | string | Theme/topic |
| participants_total | int | Total participants |
| n_paid_onsite | int | Paid onsite count |
| n_paid_online | int | Paid online count |
| n_free | int | Free-seat count |
| revenue_chf | float | Revenue in CHF |
| cost_venue_chf | float | Venue cost |
| cost_materials_chf | float | Materials cost |
| cost_instructor_chf | float | Instructor cost |
| cost_marketing_chf | float | Marketing cost |
| cost_admin_chf | float | Admin cost |
| total_cost_chf | float | Total cost |
| surplus_chf | float | Revenue - total cost |

`workshop_participants.csv`

| Column group | Fields |
|---|---|
| Identity | workshop_id, workshop_name, workshop_date, participant_id |
| Access | payment_type, modality |
| Learning | pre_score, post_score, knowledge_gain |
| Satisfaction | survey_content, survey_organization, survey_instructor, survey_materials, survey_platform, survey_overall, survey_nps |
| Qualitative | survey_open_feedback |

`reputation_summary.csv`

| Column | Description |
|---|---|
| period, city | Snapshot scope |
| nps_stakeholders | Stakeholder NPS |
| partner_ratings_count, partner_ratings_mean | Partner evaluation summary |
| social_mentions_count, testimonials_count | External voice volume |
| press_coverage_count | Media mentions |
| municipal_engagement_score | Institutional relationship strength |

---

## Tooling Schema (Agent Capability Surface)

| Tool | Inputs (high level) | Output |
|---|---|---|
| `analyze_knowledge_impact` | `workshop_id`, `pre_scores`, `post_scores` | gain stats, p-value, Cohen's d |
| `analyze_satisfaction` | `workshop_id`, survey rows, modality | NPS, dimension means, warnings |
| `measure_reputation` | stakeholder NPS, partner ratings, mentions | reputation index and interpretation |
| `synthesize_feedback_improvements` | multi-workshop feedback + metrics | prioritized improvement actions |
| `calculate_free_workshop_capacity` | historical attendance/costs + upcoming plan | Monte Carlo free-seat forecast |
| `query_knowledge_base` | natural language query | retrieved framework evidence |
| `generate_impact_report` | combined tool outputs | formatted impact narrative |

---

## Setup

### 1) Environment

```bash
python3.12 -m venv .venv312
source .venv312/bin/activate
pip install -r requirements.txt
```

### 2) Configuration

```bash
cp .env.example .env
```

Required keys/vars:

```dotenv
GEMINI_API_KEY=...
MODEL_NAME=gemma-4-31b-it
LANGFUSE_ENABLED=false
ONSITE_PRICE_CHF=15.0
ONLINE_PRICE_CHF=5.0
```

---

## Running

Run all demos:

```bash
set -a && source .env.example && set +a && LANGFUSE_ENABLED=false ./.venv312/bin/python main.py
```

Run one demo:

```bash
./.venv312/bin/python main.py --demo 3
```

Run custom question:

```bash
./.venv312/bin/python main.py --query "How many free seats can we add next quarter?"
```

Generate/refresh tabular data:

```bash
./.venv312/bin/python sample_data.py
```

---

## Outputs Produced by Execution

1. Terminal-rendered markdown responses via `rich`
2. Timestamped JSON artifacts in `data/generated/`
3. If enabled, LangFuse traces/spans/metrics via `observability.py`

---

## Notes

- The repository contains both operational agent code and analysis notebooks.
- For comprehensive interpretation of Q1–Q8, run the notebooks in sequence (`nb_01` to `nb_04`).
- `main.py` demos use scenario payloads from `sample_data.py` and can be re-run safely.

---

## License

MIT
