# NEET UG College Predictor (Karnataka Edition)

## 📌 Project Overview

This project builds a data-driven NEET UG college prediction system starting with **Karnataka (KEA counselling)**.

The system:
- Collects official counselling data (2020–2025)
- Normalizes allotment & cutoff information
- Stores structured data in a relational database
- Provides a predictive API (cutoff-based + probabilistic)
- Offers a web interface for students

⚠️ No LLM is used for numeric prediction.  
LLMs (optional) are used only for explanation and conversational UI.

---

# 🎯 Goal

Build a reliable NEET UG college prediction engine that:

Input:
- Rank Type: AIR or State Rank
- Rank Value
- Category
- Quota
- State (Karnataka for Phase-1)

Output:
- Ranked list of possible colleges
- Safe / Moderate / Risk classification
- Historical cutoff references
- Confidence score

---

# 🧱 Architecture Overview

Data Layer:
- Raw PDFs (immutable)
- Extracted tables (intermediate)
- Normalized DB tables
- Derived cutoff views

Prediction Layer:
- Cutoff Matching Engine (V1 baseline)
- Probabilistic ML model (V2)
- Explanation generator

API Layer:
- FastAPI backend
- Predict endpoint
- Metadata endpoints

UI Layer:
- React/Next.js frontend

Optional:
- LLM interface for conversational explanation only

---

# 📂 Repository Structure
neet-predictor/
├─ README.md
├─ pyproject.toml                 # or requirements.txt
├─ .env.example                   # DB creds, storage path, etc.
├─ docker/
│  ├─ Dockerfile.api
│  ├─ Dockerfile.worker
│  └─ docker-compose.yml
│
├─ data/                          # (gitignored) local dev storage
│  ├─ raw/                        # immutable raw downloads
│  │  ├─ kea_karnataka/
│  │  │  ├─ 2020/
│  │  │  ├─ 2021/
│  │  │  ├─ 2022/
│  │  │  ├─ 2023/
│  │  │  ├─ 2024/
│  │  │  └─ 2025/
│  │  └─ mcc_aiq/                 # optional later
│  │     ├─ 2020/ ... 2025/
│  │
│  ├─ interim/                    # extracted tables (csv/json) before cleaning
│  ├─ curated/                    # normalized parquet/csv ready for model
│  └─ artifacts/                  # trained models, scalers, cutoff indices
│
├─ configs/
│  ├─ sources.yaml                # source registry (URLs/patterns per year/round)
│  ├─ schema.yaml                 # canonical enums (category/quota/round)
│  └─ colleges_map.yaml           # alias→canonical college_id mapping (manual fixes)
│
├─ pipelines/                     # EVERYTHING about data
│  ├─ __init__.py
│  ├─ common/
│  │  ├─ http.py                  # downloader with retries, hashing
│  │  ├─ pdf_extract.py           # tabula/camelot/pdfplumber wrappers
│  │  ├─ normalize.py             # category/quota/college normalization
│  │  ├─ validators.py            # sanity checks (rank monotonicity, duplicates)
│  │  └─ logging.py
│  │
│  ├─ kea_karnataka/
│  │  ├─ discover.py              # find links per year/round (crawl seed pages)
│  │  ├─ download.py              # fetch PDFs, store + metadata
│  │  ├─ parse_allotment.py       # seat allotment list PDFs → rows
│  │  ├─ parse_cutoff.py          # cutoff rank PDFs → rows
│  │  ├─ build_colleges.py        # build / update college table from KEA artifacts
│  │  └─ run.py                   # one command pipeline entrypoint for KEA
│  │
│  ├─ mcc_aiq/                    # optional later
│  │  ├─ discover.py
│  │  ├─ download.py
│  │  ├─ parse_allotment.py
│  │  └─ run.py
│  │
│  └─ jobs/
│     ├─ backfill_year.py         # run for a specific year
│     └─ rebuild_curated.py       # regenerate curated datasets
│
├─ db/
│  ├─ migrations/                 # alembic or sql migrations
│  ├─ schema.sql                  # canonical schema (tables below)
│  └─ seed/                       # initial enums, states, quotas, categories
│
├─ services/
│  ├─ predictor/                  # inference logic
│  │  ├─ cutoff_engine.py         # baseline: rank vs cutoff rules
│  │  ├─ probabilistic.py         # v2 model (lightgbm/xgb) optional
│  │  └─ explain.py               # generate explanation text (no LLM required)
│  │
│  ├─ indexing/
│  │  └─ build_cutoff_index.py    # fast lookup structures (per year/round)
│  │
│  └─ llm/                        # optional: natural language UI helper
│     ├─ prompt_templates/
│     └─ router.py                # decides when to use LLM (explanations only)
│
├─ api/
│  ├─ main.py                     # FastAPI entry
│  ├─ routes/
│  │  ├─ health.py
│  │  ├─ metadata.py              # states/categories/quotas/years/rounds
│  │  ├─ colleges.py
│  │  ├─ predict.py               # main endpoint
│  │  └─ admin_ingest.py          # trigger pipeline runs (protected)
│  ├─ models/                     # pydantic request/response schemas
│  └─ deps.py                     # DB session, auth
│
├─ worker/
│  ├─ main.py                     # Celery/RQ/Arq worker entry
│  └─ tasks.py                    # async pipeline tasks (download/parse/build)
│
├─ ui/
│  ├─ web/                        # Next.js/React
│  │  ├─ pages/
│  │  ├─ components/
│  │  ├─ lib/api.ts
│  │  └─ styles/
│  └─ admin/                      # simple admin dashboard (optional)
│
└─ tests/
   ├─ unit/
   ├─ integration/
   └─ fixtures/




---

# 🗃️ Database Schema

## Tables

### source_documents
Tracks every downloaded PDF.

- doc_id
- authority
- state
- year
- round
- doc_type
- url
- file_path
- sha256
- downloaded_at

---

### colleges

- college_id
- name_canonical
- state
- city
- college_type
- codes (jsonb)

---

### allotments

- year
- round
- counselling_scope
- state
- rank_type
- rank_value
- category
- quota
- college_id
- course
- seat_type
- doc_id

---

### cutoffs

- year
- round
- counselling_scope
- state
- category
- quota
- college_id
- course
- closing_rank

---

# 🤖 Data Collection Pipeline (Karnataka)

## Step 1 — Discover
Identify KEA PDFs for:
- Round-wise allotment lists
- Cutoff rank lists
For years 2020–2025.

## Step 2 — Download
- Store raw PDFs in immutable storage
- Compute SHA256 hash
- Store metadata in DB

## Step 3 — Parse
Extract:
- Rank
- College
- Category
- Quota
- Course
- Round
- Year

Normalize:
- College names
- Category codes (GM, 2AG, etc.)
- Quota buckets

## Step 4 — Validate
- Rank > 0
- No duplicate rows
- Closing rank monotonicity checks
- Year-round completeness checks

## Step 5 — Build Curated Dataset
Generate:
- Final normalized dataset
- Derived cutoff tables
- Feature dataset for ML

---

# 🔮 Prediction Strategy

## V1 (Baseline)
Cutoff Matching Engine:
- Compare user rank against historical closing ranks
- Classify:
  - Safe
  - Moderate
  - Risky

## V2
Train LightGBM model:
P(Seat | rank, category, quota, round, year_trend, college_features)

---

# 🌐 API Endpoints

POST /predict
{
"state": "Karnataka",
"rank_type": "STATE",
"rank_value": 12500,
"category": "OBC",
"quota": "StateGovtQuota",
"round_preference": ["R1","R2"]
}


Response:
- List of colleges
- Historical references
- Confidence score

---

# 🚀 MVP Scope

Phase-1:
- Karnataka only
- Cutoff PDFs only
- Baseline cutoff engine
- Simple UI

Phase-2:
- Add allotment lists
- Add probabilistic model
- Add MCC AIQ
- Add more states

---

# 🧠 Design Philosophy

- Deterministic > LLM for numeric prediction
- All data must be traceable to source PDF
- Year-to-year policy changes must be explicitly stored
- No silent data assumptions

---

# 📦 Tech Stack

Backend: Python + FastAPI  
DB: PostgreSQL  
Parser: pdfplumber / camelot  
ML: LightGBM  
Frontend: Next.js / React  
Queue: Celery / RQ  
Deployment: Docker  

---

# 🛠️ Run Pipeline (Example)

Backfill Karnataka 2020–2025:

```bash
python pipelines/kea_karnataka/run.py --years 2020 2021 2022 2023 2024 2025


# 📈 Future Extensions
- AIQ MCC integration
- State expansion
- Seat matrix simulation
- Counselling round simulation engine
- Real-time cutoff drift modeling

# 📜 License

Educational & Research Use Only.

---
