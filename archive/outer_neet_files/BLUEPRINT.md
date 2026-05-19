# NEET Rank + College Prediction System: Master Blueprint

> Single source of truth. All other planning docs (`plan.md`, `NEET_Project_Brief_for_Claude_Opus.md`, `Claude_Opus_NEET_Architecture_Review_Prompt.md`, `neet-predictor/NEET_rank_prediction_plan.md`, `neet-predictor/README.md`) are superseded by this document.

---

## Part A: Audit of Existing Workspace

### A1. Problems Found in Existing Documents

| # | Issue | Where | Severity |
|---|-------|-------|----------|
| 1 | **4 overlapping plan docs with conflicting architecture** — `plan.md` says SQLite + Streamlit; `README.md` says PostgreSQL + FastAPI + Next.js + Docker + Celery. No single source of truth. | All plan files | Critical |
| 2 | **README.md describes a production-grade system, not an MVP** — Docker, Celery workers, React/Next.js frontend, LightGBM model, admin dashboards. This is premature over-engineering. | `neet-predictor/README.md` | Critical |
| 3 | **`round1_2024_mbbs.csv` is corrupted** — College name field contains unescaped commas that shift all downstream columns (`allotted_quota`, `seat_category` etc. contain garbage values). ~26K rows but many have incorrect column alignment. | `2024/round1_2024_mbbs.csv` | Critical |
| 4 | **`Final_round1_2024_rank_college.csv` has multi-line issues** — Reports 50K lines but actual row count is lower because college names contain embedded newlines inside quoted fields. Missing quota/category/course columns (only has s_no, rank, allotted_institute). | `2024/Final_round1_2024_rank_college.csv` | High |
| 5 | **Manifest has only 1 entry** — `mcc_manifest_2020_2025.jsonl` contains a single JSON line (2024 R2 only) despite filename suggesting 2020–2025 coverage. | `neet-predictor/mcc_aiq/mcc_manifest_2020_2025.jsonl` | High |
| 6 | **No marks-to-rank data exists anywhere** — No NTA result data, no exam_years CSV, no marks_rank_points CSV. The existing CSVs are MCC allotment lists, not marks→rank mappings. The entire rank-prediction module has zero training data. | Entire workspace | Critical |
| 7 | **Missing year coverage in PDFs** — MCC: 2020 has 2 PDFs, 2025 has 2. Karnataka: missing 2021 and 2022 entirely. Bihar: missing 2021. Coverage is incomplete and inconsistent. | `neet-predictor/mcc_aiq/` and `states/` | High |
| 8 | **Bihar state data exists with no explanation** — Plan says MVP covers only MCC + Karnataka, but Bihar data is present. No doc explains its purpose. | `neet-predictor/states/bihar/` | Medium |
| 9 | **Rank column uses decimal notation** — Ranks like 1.01, 1.02 represent tied candidates sharing rank 1. This must be handled explicitly — they are not regular decimal numbers. | `2024/round1_2024_mbbs.csv` | Medium |
| 10 | **`plan.md` says 2025 is validation year, but no 2025 marks-rank data exists** — Cannot validate the rank predictor without ground truth. | `plan.md` | High |
| 11 | **Schema definitions vary across documents** — Different table names, different columns, different normalization approaches in each plan doc. | All plan files | Medium |
| 12 | **No code exists at all** — Despite 4 plan docs and a full README, zero Python files, zero configs, zero tests. | Entire workspace | Info |

### A2. What Actually Exists (Usable Assets)

| Asset | Location | Status | Usable? |
|-------|----------|--------|---------|
| MCC AIQ Round 1 allotment data (2024, MBBS) | `2024/round1_2024_mbbs.csv` | Corrupted CSV — needs re-parsing from source PDF | After fix |
| MCC AIQ rank→college mapping (2024, R1) | `2024/Final_round1_2024_rank_college.csv` | Multi-line issues, missing key columns | After fix |
| MCC AIQ allotment PDFs (2020–2025) | `neet-predictor/mcc_aiq/2020–2025/` | 25 PDFs total, inconsistent coverage | Yes — need parsing |
| Karnataka KEA allotment PDFs (2020, 2023–2025) | `neet-predictor/states/karnataka/` | 9 PDFs, missing 2021–2022 | Partial |
| Bihar UGMAC PDFs (2020, 2022–2025) | `neet-predictor/states/bihar/` | 18 PDFs, missing 2021 | Out of MVP scope |
| Manifest file | `neet-predictor/mcc_aiq/mcc_manifest_2020_2025.jsonl` | 1 of ~25 entries populated | Needs rebuilding |
| `bihar_state_data.zip` | Root of workspace | Unknown contents | Needs inspection |

---

## Part B: What We Are Building

### B1. Product in One Sentence

A prediction tool that takes a NEET student's marks/rank + profile and returns estimated AIR range, likely MCC All India college options, likely Karnataka KEA college options, with Safe/Likely/Borderline/Unlikely labels backed by previous-year cutoff evidence.

### B2. Two-Module Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      USER INPUT                              │
│  Marks, AIR (optional), Category, State, Karnataka info,     │
│  Course preference, Budget, College type preference           │
└──────────────────────┬──────────────────────────────────────┘
                       │
          ┌────────────▼────────────┐
          │  MODULE 1: Rank Estimator│
          │  Marks → AIR range       │
          │  (skipped if AIR given)  │
          └────────────┬────────────┘
                       │
          ┌────────────▼────────────┐
          │  MODULE 2: College       │
          │  Predictor               │
          │                          │
          │  ┌──────────────────┐   │
          │  │ MCC AIQ Predictor │   │
          │  └──────────────────┘   │
          │  ┌──────────────────┐   │
          │  │ KEA KA Predictor  │   │
          │  └──────────────────┘   │
          └────────────┬────────────┘
                       │
          ┌────────────▼────────────┐
          │  OUTPUT                   │
          │  - AIR range + confidence │
          │  - College list with      │
          │    Safe/Likely/Border/    │
          │    Unlikely labels        │
          │  - Cutoff evidence        │
          │  - Explanation            │
          └──────────────────────────┘
```

### B3. MVP Scope (Hard Boundaries)

**IN scope:**
- NEET UG only
- MBBS and BDS only
- MCC All India Quota counselling (15% AIQ + AIIMS/JIPMER/Central/Deemed/ESIC)
- Karnataka KEA state counselling
- Historical data: 2020–2024 for training/fitting
- 2025 for validation/backtesting
- Simple Python stack: Pandas + SQLite + Streamlit
- Conservative prediction with confidence bands

**OUT of scope (do not build):**
- Any state besides Karnataka
- AYUSH/nursing/other courses
- Payment system, user accounts
- LLM-based chatbot
- Docker/Celery/workers
- React/Next.js frontend
- LightGBM/ML model (start with rule-based)
- Real-time counselling tracking
- Mobile app

---

## Part C: Data Architecture

### C1. Data We Need (Complete List)

#### Layer 1: Marks-to-Rank Data (DOES NOT EXIST YET — Must Be Created)

| Dataset | Source | Priority | Status |
|---------|--------|----------|--------|
| Year-wise marks vs AIR anchor points (2020–2025) | NTA result PDFs, press releases, verified scorecards, secondary portals | P0 | **MISSING** |
| Total registered/appeared/qualified candidates per year (2020–2025) | NTA press releases | P0 | **MISSING** |
| Highest score, topper count per year | NTA press releases | P1 | **MISSING** |
| Category-wise qualifying cutoff marks per year | NTA result notices | P1 | **MISSING** |
| Percentile-to-marks mapping per year | NTA result notices | P2 | **MISSING** |
| Tie-breaking rules per year | NTA information bulletins | P2 | **MISSING** |

#### Layer 2: MCC Allotment Data (PARTIALLY EXISTS)

| Dataset | Source | Priority | Status |
|---------|--------|----------|--------|
| MCC round-wise allotment results (2020–2025) | MCC portal PDFs | P0 | **25 PDFs collected, not parsed** |
| MCC seat matrices per round/year | MCC portal | P1 | **MISSING** |
| MCC opening/closing rank per college/course/category/round | Derived from allotment PDFs | P0 | **MISSING** (must derive) |
| College master list with metadata | MCC + NMC | P1 | **MISSING** |

#### Layer 3: Karnataka KEA Data (PARTIALLY EXISTS)

| Dataset | Source | Priority | Status |
|---------|--------|----------|--------|
| KEA round-wise allotment lists (2020–2025) | KEA UGNEET portal | P0 | **9 PDFs collected, gaps in 2021–2022** |
| KEA seat matrices per round/year | KEA portal | P1 | **MISSING** |
| KEA closing rank per college/course/category/seat-type | Derived from allotment PDFs or cutoff PDFs | P0 | **MISSING** |
| KEA college master list | KEA portal | P1 | **MISSING** |
| Karnataka category mapping (GM, 2A, 2B, 3A, 3B, SCG, STG, etc.) | KEA information bulletin | P1 | **MISSING** |

#### Layer 4: Reference Data

| Dataset | Source | Priority | Status |
|---------|--------|----------|--------|
| College metadata (name, state, city, ownership, courses, intake, fees) | NMC + MCC + KEA | P1 | **MISSING** |
| MCC quota types mapping | MCC counselling guide | P1 | **MISSING** |
| KEA quota/seat-type mapping | KEA information bulletin | P1 | **MISSING** |
| National category ↔ KEA category mapping | KEA rules | P1 | **MISSING** |

### C2. Data Source Priority

```
Priority 1 (High confidence):  Official NTA/MCC/KEA PDFs and press releases
Priority 2 (Medium confidence): Verified anonymized student scorecards
Priority 3 (Low-medium):        Secondary portals (Careers360, Shiksha, etc.) — gap-filling only
```

Every data point must carry provenance:
```
source_type:  OFFICIAL_NTA | OFFICIAL_MCC | OFFICIAL_KEA | VERIFIED_SCORECARD | SECONDARY_PORTAL
source_url:   direct link
source_file:  local path to PDF
confidence:   high | medium | low
accessed_date
notes
```

### C3. Database Schema (SQLite for MVP)

```sql
-- Source provenance for every data point
CREATE TABLE data_sources (
    source_id       INTEGER PRIMARY KEY AUTOINCREMENT,
    source_type     TEXT NOT NULL,  -- OFFICIAL_NTA, OFFICIAL_MCC, OFFICIAL_KEA, VERIFIED_SCORECARD, SECONDARY_PORTAL
    source_name     TEXT NOT NULL,
    source_url      TEXT,
    source_file     TEXT,           -- local file path
    sha256          TEXT,
    publisher       TEXT,
    published_date  TEXT,
    accessed_date   TEXT,
    confidence      TEXT NOT NULL,  -- high, medium, low
    parse_quality   TEXT,           -- clean, minor_issues, major_issues, unverified
    verified_by     TEXT,           -- who verified (person or "automated")
    verified_at     TEXT,           -- timestamp of verification
    row_count       INTEGER,        -- how many data rows extracted from this source
    notes           TEXT
);

-- ========== MODULE 1: MARKS-TO-RANK ==========

-- Exam year statistics
CREATE TABLE exam_years (
    year                    INTEGER PRIMARY KEY,
    max_marks               INTEGER DEFAULT 720,
    registered_candidates   INTEGER,
    appeared_candidates     INTEGER,
    qualified_candidates    INTEGER,
    highest_marks           INTEGER,
    toppers_at_highest      INTEGER,  -- how many shared AIR 1
    cutoff_ur               INTEGER,
    cutoff_obc              INTEGER,
    cutoff_sc               INTEGER,
    cutoff_st               INTEGER,
    cutoff_ews              INTEGER,
    result_date             TEXT,
    source_id               INTEGER REFERENCES data_sources(source_id),
    notes                   TEXT
);

-- Marks-to-rank anchor points (the core training data)
CREATE TABLE marks_rank_points (
    point_id           INTEGER PRIMARY KEY AUTOINCREMENT,
    year               INTEGER NOT NULL,
    marks_min          INTEGER NOT NULL,  -- lower bound of marks range (marks_min <= marks_max always)
    marks_max          INTEGER NOT NULL,  -- upper bound of marks range (= marks_min for exact values)
    rank_min           INTEGER NOT NULL,  -- best (lowest) rank at this marks
    rank_max           INTEGER NOT NULL,  -- worst (highest) rank at this marks
    rank_median        INTEGER,
    candidate_count    INTEGER,           -- how many at this exact marks, if known
    percentile         REAL,
    data_granularity   TEXT,              -- exact, range, bucket, estimated
    extraction_method  TEXT,              -- manual, pdf_table, web_table, scorecard, derived, official_published
    source_id          INTEGER REFERENCES data_sources(source_id),
    confidence         TEXT NOT NULL,     -- high, medium, low
    notes              TEXT,
    UNIQUE(year, marks_min, marks_max, source_id),
    CHECK(marks_min <= marks_max),
    CHECK(marks_min >= 0 AND marks_max <= 720),
    CHECK(rank_min >= 1 AND rank_min <= rank_max)
);

-- Tie-breaking rules per year
CREATE TABLE tie_breaking_rules (
    rule_id     INTEGER PRIMARY KEY AUTOINCREMENT,
    year        INTEGER NOT NULL,
    priority    INTEGER NOT NULL,      -- 1 = first tiebreaker
    criterion   TEXT NOT NULL,         -- e.g., "Higher Biology marks"
    source_id   INTEGER REFERENCES data_sources(source_id),
    notes       TEXT
);

-- ========== MODULE 2: COLLEGE PREDICTION ==========

-- College master
CREATE TABLE colleges (
    college_id      INTEGER PRIMARY KEY AUTOINCREMENT,
    college_code    TEXT,               -- MCC or KEA code
    college_name    TEXT NOT NULL,
    name_normalized TEXT NOT NULL,      -- cleaned, lowercase, alias-resolved
    state           TEXT NOT NULL,
    city            TEXT,
    ownership       TEXT NOT NULL,      -- government, private, deemed, central, AIIMS, JIPMER
    counselling     TEXT NOT NULL,      -- MCC, KEA, BOTH
    courses         TEXT,               -- comma-separated: MBBS, BDS
    annual_intake   INTEGER,
    fee_govt_quota  INTEGER,            -- annual fee for govt quota seat
    fee_private     INTEGER,            -- annual fee for private/mgmt seat
    nmc_approved    INTEGER DEFAULT 1,
    source_id       INTEGER REFERENCES data_sources(source_id),
    notes           TEXT
);

-- Allotment records (parsed from PDFs)
CREATE TABLE allotments (
    allotment_id    INTEGER PRIMARY KEY AUTOINCREMENT,
    year            INTEGER NOT NULL,
    round           TEXT NOT NULL,      -- R1, R2, R3, MOPUP, STRAY
    authority       TEXT NOT NULL,      -- MCC, KEA
    counselling_scope TEXT NOT NULL,    -- AIQ, STATE_KA
    rank_raw        TEXT NOT NULL,      -- original rank string from PDF: "1.01", "18.0"
    air             INTEGER NOT NULL,   -- actual AIR (integer part): 1, 18
    rank_type       TEXT DEFAULT 'AIR', -- AIR or STATE_RANK
    allotted_quota  TEXT NOT NULL,      -- Open Seat Quota, Delhi Univ, Deemed, NRI, etc.
    college_id      INTEGER REFERENCES colleges(college_id),
    college_raw     TEXT,               -- raw college name from PDF before normalization
    course          TEXT NOT NULL,      -- MBBS, BDS
    seat_category   TEXT NOT NULL,      -- Open, OBC, SC, ST, EWS (or KEA: GM, 2A, 2B, etc.)
    candidate_category TEXT,            -- actual category of candidate
    seat_type       TEXT,               -- government, private_govt_quota, private_open, management, NRI
    fee             INTEGER,
    status          TEXT,               -- Allotted, Not Reported, Cancelled, Upgraded, Resigned
    source_id       INTEGER REFERENCES data_sources(source_id),
    notes           TEXT,
    CHECK(air >= 1),
    CHECK(year BETWEEN 2020 AND 2025),
    CHECK(round IN ('R1', 'R2', 'R3', 'MOPUP', 'STRAY')),
    CHECK(course IN ('MBBS', 'BDS'))
);

-- Derived closing ranks (computed from allotments or parsed from cutoff PDFs)
-- IMPORTANT: Closing rank = MAX(air) among VALID allotments per group.
-- Status rules for derivation:
--   INCLUDE: 'Allotted' (regardless of later reporting)
--   EXCLUDE: 'Cancelled', 'Resigned', 'Seat Surrendered'
--   CAREFUL: 'Upgraded' counts for BOTH the old and new college's closing rank
-- Round-specific: NEVER merge R1 and Mop-up closing ranks.
CREATE TABLE closing_ranks (
    closing_id        INTEGER PRIMARY KEY AUTOINCREMENT,
    year              INTEGER NOT NULL,
    round             TEXT NOT NULL,
    authority         TEXT NOT NULL,      -- MCC, KEA
    counselling_scope TEXT NOT NULL,
    college_id        INTEGER REFERENCES colleges(college_id),
    course            TEXT NOT NULL,
    quota             TEXT NOT NULL,
    category          TEXT NOT NULL,
    seat_type         TEXT,
    opening_rank      INTEGER,
    closing_rank      INTEGER NOT NULL,
    seats_total       INTEGER,
    seats_filled      INTEGER,
    derivation_method TEXT,               -- 'derived_from_allotments' or 'direct_from_cutoff_pdf'
    statuses_included TEXT,               -- which allotment statuses were counted, e.g. 'Allotted'
    source_id         INTEGER REFERENCES data_sources(source_id),
    notes             TEXT,
    UNIQUE(year, round, authority, college_id, course, quota, category, seat_type),
    CHECK(closing_rank >= opening_rank OR opening_rank IS NULL),
    CHECK(seats_filled <= seats_total OR seats_total IS NULL)
);

-- Seat matrix per year/round
CREATE TABLE seat_matrix (
    matrix_id       INTEGER PRIMARY KEY AUTOINCREMENT,
    year            INTEGER NOT NULL,
    round           TEXT NOT NULL,
    authority       TEXT NOT NULL,
    counselling_scope TEXT NOT NULL,
    college_id      INTEGER REFERENCES colleges(college_id),
    course          TEXT NOT NULL,
    quota           TEXT NOT NULL,
    category        TEXT NOT NULL,
    seat_type       TEXT,
    seats_available INTEGER NOT NULL,
    fee             INTEGER,
    source_id       INTEGER REFERENCES data_sources(source_id),
    notes           TEXT
);

-- College name aliases for cross-year/cross-authority normalization
CREATE TABLE college_aliases (
    alias_id        INTEGER PRIMARY KEY AUTOINCREMENT,
    college_id      INTEGER NOT NULL REFERENCES colleges(college_id),
    alias_name      TEXT NOT NULL,       -- raw name as it appears in a specific source
    alias_normalized TEXT NOT NULL,      -- lowercase, stripped, standardized version
    authority       TEXT,                -- MCC, KEA, or NULL if general
    year            INTEGER,             -- year this alias was seen, or NULL if general
    source_id       INTEGER REFERENCES data_sources(source_id),
    notes           TEXT
);

-- Policy/rule changes per year (eligibility, domicile, conversion rules)
CREATE TABLE counselling_rules (
    rule_id     INTEGER PRIMARY KEY AUTOINCREMENT,
    year        INTEGER NOT NULL,
    authority   TEXT NOT NULL,
    rule_type   TEXT NOT NULL,  -- eligibility, conversion, tiebreak, fee, domicile
    description TEXT NOT NULL,
    applies_to  TEXT,           -- category/quota/round this applies to
    source_id   INTEGER REFERENCES data_sources(source_id),
    notes       TEXT
);
```

### C4. Category Mapping (Critical for Correctness)

MCC and KEA use **different category systems**. The system must NEVER mix them.

| MCC National Category | KEA Karnataka Category | Notes |
|----------------------|------------------------|-------|
| General / UR | GM (General Merit) | GM is Karnataka-specific |
| OBC / OBC-NCL | 2A, 2B, 3A, 3B | KEA subdivides OBC into 4 groups |
| SC | SCG (SC General) | Different notation |
| ST | STG (ST General) | Different notation |
| EWS | — | EWS may not directly map to a KEA category |
| — | GMR (General Merit Rural) | Karnataka-only reservation |
| — | GMK (General Merit Kannada) | Karnataka-only reservation |
| — | 1G (Category 1 General) | KEA-only |
| — | HK (Hyderabad-Karnataka) | Regional reservation |

**Rule**: When predicting MCC outcomes, use MCC categories. When predicting KEA outcomes, use KEA categories. Never cross-map for prediction — only for display/explanation.

### C5. Hard Validation Rules (Must-Implement Before Any Prediction)

All data must pass these checks at load time. Fail loudly, never silently accept bad data.

```
── Marks-to-Rank Data ──
marks_min >= 0 AND marks_max <= 720
marks_min <= marks_max
rank_min >= 1
rank_min <= rank_max
Per year: marks↑ must imply rank↓ (monotonicity). If row A has marks_min > row B's marks_max,
  then row A's rank_max must be <= row B's rank_min. Flag violations, do not silently drop.
source_id IS NOT NULL (every row needs provenance)

── Allotment Data ──
air >= 1
year BETWEEN 2020 AND 2025
round IN ('R1', 'R2', 'R3', 'MOPUP', 'STRAY')
course IN ('MBBS', 'BDS')
Per (year, round, authority): same air should map to at most ONE college
  (one student gets one seat per round)
college_id IS NOT NULL after normalization (flag unresolved college names)
authority-category consistency:
  - MCC record must NOT use KEA categories (GM, 2A, 2B, 3A, 3B, SCG, STG, etc.)
  - KEA record must NOT use MCC-only categories without documented mapping

── Closing Rank Data ──
closing_rank >= opening_rank (numerically — worse rank has higher number)
seats_filled <= seats_total (where both are known)
derivation_method IS NOT NULL

── College Data ──
college_name IS NOT NULL
name_normalized IS NOT NULL
state IS NOT NULL
ownership IN ('government', 'private', 'deemed', 'central', 'AIIMS', 'JIPMER')

── Cross-Table ──
Every college_id in allotments/closing_ranks must exist in colleges table
Every source_id in any table must exist in data_sources table
No orphan records
```

---

## Part D: Module 1 — Marks-to-Rank Estimator

### D1. What It Does

```
Input:  NEET marks (0–720)
Output: { best_case_AIR, median_AIR, conservative_AIR, confidence, explanation }
```

If the student provides their actual AIR, this module is **skipped** and actual AIR is used directly.

### D2. Training Data Required

For each year 2020–2024, we need a set of (marks, rank) anchor points. Sources in priority order:

1. **NTA official press releases**: candidate count, topper data, qualifying cutoffs
2. **NTA official result statistics PDFs**: marks-vs-rank distribution if published
3. **Verified anonymized scorecards**: marks + AIR pairs from real students
4. **Secondary portal tables**: Careers360, Shiksha, etc. (medium confidence only)

Minimum viable anchor points per year (at least 15–20 points spanning the marks range):
```
720, 700, 690, 680, 670, 660, 650, 640, 630, 620,
610, 600, 580, 560, 540, 520, 500, 480, 450, 400,
350, 300, qualifying_cutoff
```

### D3. Algorithm

**Critical design decision: Interpolate in PERCENTILE space, not raw rank space.**

Raw ranks are not comparable across years. 2020 had ~14 lakh candidates; 2024 had ~24 lakh. Rank 20,000 in 2020 (top 1.4%) ≠ rank 20,000 in 2024 (top 0.8%). Percentile-space interpolation handles this correctly.

```
Step 1: Load marks_rank_points for 2020–2024.
        Load exam_years for appeared_candidates per year.

Step 2: For each year, convert rank to percentile:
            pct_min = rank_min / appeared_candidates
            pct_max = rank_max / appeared_candidates
            pct_median = rank_median / appeared_candidates (if known)
        For range-based marks (marks_min != marks_max), use midpoint for interpolation anchor.

Step 3: For each year, build a monotonic interpolation curve in (marks → percentile) space.
        Use piecewise linear interpolation.
        Enforce monotonicity: higher marks → better (lower) percentile. Always.
        Use isotonic regression fallback if raw data violates monotonicity.

Step 4: For a given input marks value:
        - Evaluate percentile on each year's curve
        - Weight years: 2024=0.40, 2023=0.25, 2022=0.18, 2021=0.10, 2020=0.07
        - weighted_pct_best   = weighted average of pct_min across years
        - weighted_pct_median = weighted average of pct_median across years
        - weighted_pct_conservative = weighted average of pct_max across years

Step 5: Convert back to rank using expected candidate count.
        - If predicting for a known year: use that year's appeared_candidates
        - If predicting for current/unknown year: use latest year's count
        - best_case_AIR   = round(weighted_pct_best × appeared_candidates)
        - median_AIR       = round(weighted_pct_median × appeared_candidates)
        - conservative_AIR = round(weighted_pct_conservative × appeared_candidates)

Step 6: Assign confidence label based on:
        - Distance to nearest anchor points (closer = higher confidence)
        - Number of years with data at that marks level
        - Source quality (official > secondary)
        - Agreement across years (low cross-year percentile variance = higher confidence)
```

### D4. Confidence Labels

```
HIGH:    ≥3 years have official anchor points within ±5 marks; cross-year variance < 20%
MEDIUM:  ≥2 years have data within ±10 marks; some secondary sources used
LOW:     sparse data; extrapolation; only secondary sources; high cross-year variance
```

### D5. Validation (2025)

Train on 2020–2024. For every 2025 anchor point:
- Predict rank range
- Check if actual 2025 rank falls within predicted range

Key metric: **coverage rate** (% of 2025 points where actual rank is within predicted best–conservative range). Target: ≥80%.

### D6. Edge Cases

- Marks = 720: may map to rank 1 or rank 1–67 depending on year. Output a range.
- Marks below qualifying cutoff: output "Below qualifying cutoff for [category]. No rank assigned."
- Marks in very low range (< 200): output "Low confidence — sparse historical data in this range."
- Tie-breaking: state clearly "Exact rank depends on subject-wise marks and tie-breaking rules. This is an estimate from total marks only."

---

## Part E: Module 2 — College Predictor

### E1. What It Does

```
Input:  AIR (actual or estimated range), category, state, Karnataka info, preferences
Output: List of (college, course, quota, category, seat_type, round, chance_label, cutoff_evidence)
```

### E2. Eligibility Filter (Layer 2a)

Before predicting, filter what the student is actually eligible for:

```
1. Every NEET qualifier is eligible for MCC AIQ.
2. Karnataka state counselling requires Karnataka domicile.
3. KEA category determines which reservation seats are available.
4. College type filter applies (govt, private, deemed, NRI, management).
5. Course preference filter applies (MBBS, BDS, both).
6. Budget filter removes colleges with fees above threshold.
```

### E3. Chance Prediction (Layer 2b)

For each eligible (college, course, quota, category, seat_type) combination:

```
1. Look up historical closing ranks for 2020–2024, for the matching:
     - authority (MCC or KEA)
     - college
     - course
     - quota
     - category
     - seat_type
     - ROUND 1 ONLY for primary prediction (see round strategy below)

2. Check data sufficiency:
     - If < 2 years of R1 data: label = "Insufficient data" (skip Safe/Likely/Borderline/Unlikely)
     - If 2 years: use both with equal weight; mark confidence = LOW
     - If 3+ years: normal weighted prediction

3. Compute weighted closing rank trend:
     weighted_closing = 0.40 * CR_2024 + 0.25 * CR_2023 + 0.18 * CR_2022 + 0.10 * CR_2021 + 0.07 * CR_2020
     (Use only years where data exists; re-normalize weights.)

4. Compare student AIR against weighted_closing:
     ratio = student_AIR / weighted_closing

     Safe:        ratio ≤ 0.75   (rank is 25%+ better than historical closing)
     Likely:      0.75 < ratio ≤ 0.95
     Borderline:  0.95 < ratio ≤ 1.15
     Unlikely:    ratio > 1.15

5. If student AIR is estimated (not actual):
     Use conservative_AIR for the ratio computation.
     State: "Using conservative estimate. Actual rank may improve results."

6. Calibrate thresholds separately for:
     - AIQ government colleges (highly competitive → tighter thresholds)
     - Karnataka government colleges
     - Private govt-quota seats
     - Private open / management / NRI (more variable → wider thresholds)
```

#### E3a. Round-Aware Prediction Strategy

```
PRIMARY prediction: Based on Round 1 closing ranks ONLY.
  This answers: "Can I get this college in the main round?"
  This is displayed as the main prediction.

SECONDARY signal: If Round 2/Mop-up/Stray data exists:
  Show as: "Additional options may be available in later rounds."
  Display later-round closing ranks as supplementary evidence.
  Do NOT average R1 and Mop-up closing ranks — they are different decision contexts.
  Later rounds have vacancies from non-reporting/upgrades, so closing ranks can shift unpredictably.

DISPLAY: Show round-wise closing rank history in the evidence section:
  "R1: 16,500 (2024), 17,200 (2023) | Mop-up: 22,000 (2024), 19,800 (2023)"
```

### E4. Output Format

```json
{
  "rank_used": {
    "type": "estimated",
    "best_case": 15000,
    "median": 17000,
    "conservative": 19000,
    "confidence": "medium"
  },
  "eligible_paths": [
    {"authority": "MCC", "scope": "AIQ", "eligible": true},
    {"authority": "KEA", "scope": "Karnataka State", "eligible": true, "category": "2A"}
  ],
  "predictions": [
    {
      "college": "Bangalore Medical College",
      "course": "MBBS",
      "authority": "KEA",
      "quota": "Government",
      "category": "2A",
      "seat_type": "government",
      "chance": "Likely",
      "evidence": {
        "closing_ranks": {"2024": 16500, "2023": 17200, "2022": 15800},
        "weighted_closing": 16600,
        "rank_used": 19000,
        "ratio": 1.14
      },
      "explanation": "Your conservative AIR (19,000) is near the 2020–2024 weighted closing rank (16,600) for this college under 2A category. Borderline chance based on trend."
    }
  ],
  "warnings": [
    "Prediction based on 2020–2024 historical data. Not an admission guarantee.",
    "KEA category eligibility must be verified with official documents.",
    "Seat matrix and fees may change each year."
  ]
}
```

### E5. Sorting and Display

Sort predictions by:
1. Chance label (Safe first, then Likely, Borderline, Unlikely)
2. Within each label, sort by weighted closing rank (best fit first)

Group by counselling authority (MCC section, then KEA section).

---

## Part F: User Input Design

### F1. Mandatory Fields

| # | Field | Type | Values |
|---|-------|------|--------|
| 1 | NEET marks | Integer 0–720 | |
| 2 | NEET AIR | Integer (optional) | If provided, skip rank estimation |
| 3 | Home state | Dropdown | All Indian states + UTs |
| 4 | National category | Dropdown | General, OBC/OBC-NCL, SC, ST, EWS |
| 5 | Karnataka counselling interest | Yes/No | |

### F2. Conditional Fields (if Karnataka = Yes)

| # | Field | Type | Values |
|---|-------|------|--------|
| 6 | Karnataka domicile | Dropdown | Yes, No, Not Sure |
| 7 | Karnataka category | Dropdown | GM, 1G, 2A, 2B, 3A, 3B, SCG, STG, GMR, GMK, HK, Kannada Medium, Rural, Not Sure |

### F3. Optional Fields (with sensible defaults)

| # | Field | Default | Values |
|---|-------|---------|--------|
| 8 | Course preference | All | MBBS, BDS, Both |
| 9 | College type | All | Govt, Private-GQ, Private-Open, Management, NRI, Deemed |
| 10 | Max annual fee | No limit | Number or "No limit" |
| 11 | Preferred location | All | Free text or dropdown |

---

## Part G: Implementation Plan

### G1. Technology Stack (MVP)

```
Language:       Python 3.11+
Data:           Pandas + SQLite
PDF parsing:    pdfplumber (primary), camelot-py (fallback)
Interpolation:  scipy.interpolate + sklearn.isotonic
UI:             Streamlit
Testing:        pytest
```

No Docker, no Celery, no React, no PostgreSQL, no LightGBM for MVP.

### G2. Folder Structure

```
neet-predictor/
├── README.md
├── requirements.txt
├── pyproject.toml
├── .gitignore
│
├── data/
│   ├── raw/                        # Immutable downloaded PDFs (gitignored)
│   │   ├── nta/                    # NTA result notices
│   │   ├── mcc_aiq/                # MCC allotment PDFs (EXISTING — move here)
│   │   │   ├── 2020/ ... 2025/
│   │   └── kea_karnataka/          # KEA allotment/cutoff PDFs (EXISTING — move here)
│   │       ├── 2020/ ... 2025/
│   │
│   ├── parsed/                     # Extracted CSV/JSON from PDFs
│   │   ├── mcc_allotments/
│   │   └── kea_allotments/
│   │
│   ├── curated/                    # Final cleaned CSVs ready for prediction
│   │   ├── exam_years.csv
│   │   ├── marks_rank_points.csv
│   │   ├── colleges.csv
│   │   ├── allotments.csv
│   │   ├── closing_ranks.csv
│   │   └── seat_matrix.csv
│   │
│   ├── templates/                  # CSV templates with headers + example rows
│   │
│   └── sources/                    # Source provenance registry
│       └── data_sources.csv
│
├── src/
│   └── neet_predictor/
│       ├── __init__.py
│       ├── config.py               # constants, paths, weights
│       │
│       ├── data/
│       │   ├── __init__.py
│       │   ├── loader.py           # load CSVs into dataframes / SQLite
│       │   ├── validator.py        # validate marks 0–720, rank > 0, monotonicity, etc.
│       │   └── normalizer.py       # college name normalization, category mapping
│       │
│       ├── rank/
│       │   ├── __init__.py
│       │   ├── interpolator.py     # monotonic interpolation per year
│       │   ├── estimator.py        # weighted multi-year rank estimator
│       │   └── confidence.py       # confidence scoring
│       │
│       ├── college/
│       │   ├── __init__.py
│       │   ├── eligibility.py      # filter eligible paths (MCC/KEA/category/quota)
│       │   ├── predictor.py        # chance prediction engine
│       │   └── explainer.py        # generate human-readable explanations
│       │
│       └── ui/
│           └── app.py              # Streamlit app
│
├── pipelines/
│   ├── __init__.py
│   ├── parse_mcc_pdf.py            # MCC PDF → parsed CSV
│   ├── parse_kea_pdf.py            # KEA PDF → parsed CSV
│   ├── build_closing_ranks.py      # allotments → closing_ranks
│   ├── build_college_master.py     # extract and normalize college list
│   └── manifest.py                 # rebuild manifest JSONL
│
├── tests/
│   ├── test_validator.py
│   ├── test_interpolator.py
│   ├── test_estimator.py
│   ├── test_eligibility.py
│   ├── test_predictor.py
│   └── test_monotonicity.py
│
├── notebooks/
│   ├── 01_data_audit.ipynb
│   ├── 02_marks_rank_curves.ipynb
│   └── 03_backtest_2025.ipynb
│
└── docs/
    ├── DATA_SOURCES.md
    ├── METHODOLOGY.md
    ├── LIMITATIONS.md
    └── CATEGORY_MAPPING.md
```

### G3. Phased Implementation

**EXECUTION RULE: Phases are strictly sequential. Do NOT start a phase until its gate conditions are met. Do NOT allow Codex to jump to college prediction (Phase 3) until marks-rank data and parsed allotment data exist.**

#### Phase 0: Data Foundation (MUST DO FIRST)

**This is the critical blocker.** No prediction is possible without data.

| Task | Output | Priority |
|------|--------|----------|
| Collect NTA result notices (2020–2025) and extract exam_years data | `exam_years.csv` | P0 |
| Collect/compile marks-vs-rank anchor points (2020–2024) from NTA, verified scorecards, secondary portals | `marks_rank_points.csv` | P0 |
| Parse existing MCC allotment PDFs → structured CSV | `data/parsed/mcc_allotments/*.csv` | P0 |
| Parse existing KEA allotment PDFs → structured CSV | `data/parsed/kea_allotments/*.csv` | P0 |
| Fix the corrupted `round1_2024_mbbs.csv` by re-parsing from source PDF | Fixed CSV | P0 |
| Build college master from parsed allotments | `colleges.csv` | P0 |
| Build college_aliases from all observed name variants | `college_aliases` populated | P0 |
| Derive closing ranks from parsed allotments (R1 first) | `closing_ranks.csv` | P0 |
| Build complete manifest for all downloaded PDFs | `mcc_manifest_2020_2025.jsonl` | P1 |
| Populate `data_sources.csv` with provenance for every data file | `data_sources.csv` | P1 |
| Fill gaps: download missing MCC PDFs for 2020, 2025; missing KEA PDFs for 2021, 2022 | Additional PDFs | P1 |

**GATE → Phase 1**: `exam_years.csv` has 5+ years. `marks_rank_points.csv` has ≥15 anchor points per year for ≥3 years. `data_sources.csv` populated.

#### Phase 1: Data Loading + Validation

| Task | Output |
|------|--------|
| Implement `loader.py` — load all curated CSVs | Working loader |
| Implement `validator.py` — all hard validation rules from C5 | Working validator that fails loudly |
| Implement `normalizer.py` — college name normalization, category mapping, alias resolution | Working normalizer |
| Write tests for all above | Passing tests |

**GATE → Phase 2**: All curated CSVs pass validator. Zero unresolved college names. Zero category mismatches.

#### Phase 2: Rank Estimation

| Task | Output |
|------|--------|
| Implement `interpolator.py` — per-year monotonic interpolation in percentile space | Working interpolator |
| Implement `estimator.py` — weighted multi-year rank estimator with candidate-count normalization | `predict_rank_range(marks) → {best, median, conservative}` |
| Implement `confidence.py` — confidence scoring | Confidence labels |
| Backtest against 2025 anchor points | Coverage rate metric |
| Write tests for monotonicity, interpolation, estimation | Passing tests |

**GATE → Phase 3**: Rank estimator coverage rate ≥ 70% on 2025 validation points. Monotonicity tests pass.

#### Phase 3: College Prediction

**GATE to enter Phase 3**: `closing_ranks` has ≥500 rows covering ≥3 years. `colleges` table has all colleges resolved with aliases.

| Task | Output |
|------|--------|
| Implement `eligibility.py` — MCC/KEA eligibility filter | Eligible paths |
| Implement `predictor.py` — chance prediction engine | Safe/Likely/Borderline/Unlikely labels |
| Implement `explainer.py` — human-readable explanations | Explanation strings |
| Backtest: for known 2025 allotments, check if system would have predicted correctly | Accuracy metrics |
| Write tests | Passing tests |

#### Phase 4: Streamlit UI

| Task | Output |
|------|--------|
| Student input form | Working form |
| Rank prediction display | AIR range + confidence |
| MCC college prediction panel | College list with labels |
| KEA college prediction panel | College list with labels |
| Explanation panel | Cutoff evidence display |
| Disclaimer section | Proper warnings |

#### Phase 5: Validation + Documentation

| Task | Output |
|------|--------|
| Full backtest with 2025 data | Validation report |
| Tune confidence thresholds | Calibrated thresholds |
| Write `DATA_SOURCES.md` | Doc |
| Write `METHODOLOGY.md` | Doc |
| Write `LIMITATIONS.md` | Doc |
| Write `CATEGORY_MAPPING.md` | Doc |
| Final `README.md` | Doc |

---

## Part H: Key Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| **No marks-to-rank data exists** — module 1 cannot be built without it | Blocks entire rank predictor | P0: compile from NTA press releases + secondary portals + verified scorecards |
| CSV parsing corruption in existing data | Wrong predictions if used as-is | Re-parse from source PDFs with proper quote-aware CSV handling |
| Karnataka data gaps (2021, 2022 missing) | Fewer training years for KEA predictor | Accept reduced accuracy or fill from secondary sources |
| MCC category ↔ KEA category confusion | Completely wrong predictions | Strict separation in code — never mix category systems |
| College name inconsistency across years/PDFs | Same college not recognized across years | Normalize with alias mapping table |
| Seat matrix changes mid-counselling | Predictions based on stale matrix | Store round-specific matrices; warn user |
| Decimal rank format (1.01, 1.02) | Parsing errors if treated as regular float | Parse as composite (base_rank . sub_rank); use base rank for cutoff computation |
| User selects "Not Sure" for Karnataka category | Cannot predict KEA outcomes precisely | Show predictions for most common categories with explanation |
| False-safe predictions erode trust | Students rely on wrong advice | Use conservative thresholds; bias toward Borderline over Safe |

---

## Part I: Validation Methodology

### I1. Rank Predictor Validation

```
Training set: 2020–2024 marks-rank anchor points
Test set:     2025 marks-rank anchor points

For each 2025 anchor (marks_i, rank_i):
    predicted = predict_rank_range(marks_i)  # using 2020–2024 only
    check: predicted.best_case ≤ rank_i ≤ predicted.conservative

Metrics:
    coverage_rate:           fraction of 2025 points inside predicted range
    median_absolute_error:   median |predicted.median - actual|
    within_10pct_band:       fraction within 10% of actual rank
    within_20pct_band:       fraction within 20% of actual rank
```

### I2. College Predictor Validation

```
Training set: 2020–2024 closing ranks
Test set:     2025 actual allotments

For each 2025 allotted student (AIR, category, college, course):
    predictions = predict_colleges(AIR, category, ...)
    check: was actual college in predictions?
    check: what label was assigned? (Safe/Likely/Borderline/Unlikely)

Metrics:
    top_10_recall:    % of 2025 students whose actual college appeared in top-10 predictions
    top_25_recall:    % in top-25
    false_safe_rate:  % predicted "Safe" but student did NOT get that college
    calibration:      Safe predictions should come true >80% of the time
                      Likely > 50%
                      Borderline > 20%
```

### I3. Most Critical Metric

**False-safe rate must be minimized.** It is far better to say "Borderline" than to falsely say "Safe."

---

## Part J: What To Do Next (Ordered)

```
1. STOP writing more plan documents. This blueprint is the final plan.
2. Compile marks-rank anchor data for 2020–2024 (P0 blocker).
3. Parse existing MCC PDFs into structured CSVs.
4. Parse existing KEA PDFs into structured CSVs.
5. Fix the corrupted 2024 CSV.
6. Build the data loader + validator.
7. Build the rank estimator.
8. Build the college predictor.
9. Build the Streamlit UI.
10. Validate with 2025 data.
```

---

## Part K: Disclaimer (Must Appear in All UI)

> This prediction is based on historical counselling data from 2020–2024. It is **not an admission guarantee**. Actual allotment depends on official counselling rules, seat availability, candidate preferences, category verification, fee payment, document verification, and yearly competition. Always verify with official MCC/KEA/NTA notifications.
