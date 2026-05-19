# LLM Reasoning Layer — Detailed Implementation Plan

> Created: 2026-05-18
> Status: READY TO IMPLEMENT
> Dependencies: All prediction infrastructure complete (Phase 1A-1D)

---

## 0. What We Have (Before This Phase)

### 0.1 Existing Prediction Engine (WORKING)

```
src/neet_predictor/
├── integrated/
│   ├── pipeline.py      → UnifiedInput → run_prediction() → UnifiedResult
│   └── summary.py       → build_student_result() → StudentResult
├── rank/
│   └── estimator.py     → RankEstimator.estimate(marks) → RankEstimate
├── college/
│   ├── predictor.py     → predict(CandidateProfile) → PredictionResult
│   └── eligibility.py   → get_mcc_eligible_categories() / get_kea_eligible_categories()
└── config.py            → Year weights, category systems, thresholds
```

**Key existing dataclasses:**
- `UnifiedInput(marks, actual_air, national_category, home_state, pwd, karnataka_*, course_pref, college_type_pref)`
- `UnifiedResult(input, rank_estimate, rank_used, college_predictions, warnings)`
- `StudentResult(input_summary, rank_summary, rank_used, shortlist, mcc_summary, kea_summary, warnings, limitations)`
- `CollegeEntry(college_name, college_id, state, course, authority, category, quota, chance, r1_closing_ranks, ...)`

### 0.2 Curated Data (9 FILES, ALL COMPLETE)

| File | Rows | Key Columns |
|------|------|-------------|
| `closing_ranks.csv` | 28,396 | year, round, college_id, course, category, quota, closing_rank |
| `allotments.csv` | 308,888 | year, round, air, college_id, course, status |
| `colleges.csv` | 1,422 | college_id, college_name, state, ownership, counselling |
| `exam_years.csv` | 6 | year, registered, appeared, qualified, cutoffs, highest_marks |
| `marks_rank_points.csv` | 61 | year, marks_min, marks_max, rank_min, rank_max |
| `category_cutoff_stats.csv` | 54 | year, category, percentile_threshold, marks_min |
| `college_aliases.csv` | 2,243 | college_id, alias_name |
| `tie_breaking_rules.csv` | 11 | years_effective, priority, criterion |
| `seat_matrix.csv` | 1 | (placeholder — not populated) |

### 0.3 Analysis Intelligence (96KB INSIGHTS)

File: `data/analysis/air_insights_log.md` — 18 sections including:
- Marks-to-rank curve shape and thresholds
- Category multipliers (OBC ~1.5x, SC ~4x, ST ~5x General)
- College tiers (Elite/T1/T2/T3/T4/T5/T6)
- YoY volatility by tier (CV=0.003 to CV=1.8)
- Round dynamics (R2 adds +3,944 median, STRAY +14,522)
- New colleges trajectory (159 in 2025, first-year median ~15k-16k)
- Competition ratio (43:1 → 51:1 → 46:1)
- Candidate journey across rounds (STRAY = 94% new entries)

### 0.4 Available LLM Models (Siemens API)

| Model | Best For | Speed | Notes |
|-------|----------|-------|-------|
| `deepseek-v4-flash` | Structured output, reasoning | Fast | **PRIMARY — intent parsing + fallback reasoning** |
| `gpt-oss-120b` | Long narrative, nuanced text | Slow | **Narrative generation** |
| `qwen-3.6-27b` | Balanced reasoning | Medium | Fallback if others fail |
| `glm-5` | Chinese-origin, decent EN | Medium | Backup |
| `ministral-3-14b-instruct-2512` | Quick tasks | Fast | Could do intent parsing |
| `mistral-7b-instruct` | Lightweight | Fastest | Too small for counselling |
| `whisper-large-v3-turbo` | Audio | — | Not relevant |

**API Key:** Stored in `.env` (never committed to Git)

---

## 1. Architecture (6 Layers)

```
Student Query (natural language)
        │
        ▼
┌─────────────────────────────────────┐
│  LAYER 1: INTENT PARSER             │
│  Model: deepseek-v4-flash           │
│  Input: raw text                    │
│  Output: StudentIntent (JSON)       │
│  Fallback: form-based input         │
└───────────────┬─────────────────────┘
                ▼
┌─────────────────────────────────────┐
│  LAYER 2: SLOT RESOLVER             │
│  No LLM — pure Python logic         │
│  Input: StudentIntent               │
│  Output: list[ScenarioSpec]         │
│  Logic: branch on uncertainties     │
└───────────────┬─────────────────────┘
                ▼
┌─────────────────────────────────────┐
│  LAYER 3: DETERMINISTIC EXECUTOR    │
│  No LLM — calls run_prediction()    │
│  Input: ScenarioSpec[]              │
│  Output: ScenarioResult[]           │
│  Uses: UnifiedInput → StudentResult │
└───────────────┬─────────────────────┘
                ▼
┌─────────────────────────────────────┐
│  LAYER 4: SCENARIO COMPARATOR       │
│  No LLM — pure Python logic         │
│  Input: ScenarioResult[]            │
│  Output: ScenarioComparison         │
│  Logic: compare safe/likely/border  │
└───────────────┬─────────────────────┘
                ▼
┌─────────────────────────────────────┐
│  LAYER 5: LLM REASONER              │
│  Model: gpt-oss-120b                │
│  Input: Intent + Results + Insights │
│  Output: CounsellingNarrative       │
│  Fallback: show raw tables          │
└───────────────┬─────────────────────┘
                ▼
┌─────────────────────────────────────┐
│  LAYER 6: OUTPUT VALIDATOR          │
│  No LLM — regex + set checks        │
│  Input: Narrative + Ground Truth    │
│  Output: ValidatedResponse          │
│  Action: strip narrative if invalid │
└─────────────────────────────────────┘
```

**Only 2 LLM calls total.** Everything else is deterministic.

---

## 2. File Plan

```
src/neet_predictor/counsellor/
├── __init__.py              # Public API exports
├── models.py                # All dataclasses (StudentIntent, ScenarioSpec, etc.)
├── intent_parser.py         # Layer 1: LLM-based intent extraction
├── slot_resolver.py         # Layer 2: Scenario branching logic
├── executor.py              # Layer 3: Run prediction engine per scenario
├── comparator.py            # Layer 4: Compare scenario results
├── reasoner.py              # Layer 5: LLM narrative generation
├── validator.py             # Layer 6: Output safety checks
├── llm_client.py            # Siemens API client (OpenAI-compatible wrapper)
├── prompts.py               # All prompt templates
├── knowledge.py             # Injects analysis insights into prompts
└── orchestrator.py          # Top-level pipeline: ties layers 1-6

tests/counsellor/
├── __init__.py
├── test_models.py           # Dataclass validation
├── test_intent_parser.py    # Intent extraction (mocked LLM)
├── test_slot_resolver.py    # Scenario generation logic
├── test_executor.py         # Prediction execution
├── test_comparator.py       # Result comparison
├── test_validator.py        # Safety checks (fake colleges, label upgrades)
├── test_knowledge.py        # Knowledge injection
└── test_orchestrator.py     # End-to-end (mocked LLM)

scripts/
└── counsellor_demo.py       # CLI demo with real API
```

---

## 3. Data Flow — What Feeds Into Each Layer

### Layer 1 (Intent Parser)

**Input Data:**
- Raw student query (string)
- System prompt defining extraction rules

**Output:**
```python
StudentIntent(
    marks=620,
    actual_air=None,
    national_category="OBC",
    home_state="Karnataka",
    pwd=False,
    karnataka_interest=True,
    karnataka_domicile=None,       # not stated
    karnataka_category="2A",       # uncertain
    course_pref="MBBS",
    college_type_pref="government",
    bds_backup=True,
    missing_slots=["karnataka_domicile"],
    uncertain_slots=["karnataka_category"],
    ambiguity_notes=["Student said 'maybe 2A'"],
    raw_query="I have 620 marks, OBC, Karnataka..."
)
```

**What LLM needs to know:**
- Valid national categories: General, OBC, SC, ST, EWS
- Valid KEA categories: GM, 1, 2A, 2B, 3A, 3B, SC, ST
- Marks range: 0-720
- Never infer KEA category from national category
- Never assume domicile from home_state

---

### Layer 2 (Slot Resolver)

**Input Data:**
- `StudentIntent` from Layer 1
- Rules about what's required vs optional

**Logic:**
```
IF missing critical slots (marks AND actual_air both null):
    → return ClarificationNeeded(questions=[...])

IF uncertain slots:
    → create scenario branches WITH and WITHOUT that slot

IF bds_backup:
    → add MBBS+BDS scenario alongside MBBS-only

IF karnataka_interest AND karnataka_domicile unknown:
    → branch: one scenario assuming domicile, one without
```

**Output:**
```python
[
    ScenarioSpec(label="MBBS, MCC AIQ (OBC)", ...),
    ScenarioSpec(label="MBBS, KEA GM (no domicile)", ...),
    ScenarioSpec(label="MBBS, KEA 2A (if domicile)", ...),
    ScenarioSpec(label="MBBS+BDS, MCC AIQ (OBC)", ...),
]
```

---

### Layer 3 (Executor)

**Input Data:**
- `ScenarioSpec[]` from Layer 2
- Each spec contains a ready-to-use `UnifiedInput`

**What it does:**
```python
for spec in scenarios:
    unified_result = run_prediction(spec.unified_input)
    student_result = build_student_result(unified_result)
    results.append(ScenarioResult(spec=spec, student_result=student_result))
```

**Data accessed (via existing engine):**
- `data/curated/closing_ranks.csv` → historical rank data for prediction
- `data/curated/colleges.csv` → college names, states, ownership
- `data/curated/marks_rank_points.csv` → marks-to-AIR conversion (if marks-only)
- Year weights: {2024: 0.40, 2023: 0.25, 2022: 0.18, 2021: 0.10, 2020: 0.07}

**Output:**
```python
ScenarioResult(
    spec=ScenarioSpec(...),
    student_result=StudentResult(
        shortlist=[
            CollegeEntry(college_name="AIIMS Delhi", chance="Safe", ...),
            CollegeEntry(college_name="GMC Chandigarh", chance="Likely", ...),
            ...
        ],
        mcc_summary=AuthoritySummary(total=45, by_chance=[Safe:5, Likely:12, ...]),
        warnings=[...],
        limitations=[...],
    )
)
```

---

### Layer 4 (Comparator)

**Input Data:**
- `ScenarioResult[]` from Layer 3

**What it computes:**
```
For each scenario:
  - Count of Safe + Likely + Borderline colleges
  - Best government MBBS option (lowest rank in shortlist)
  - Authority split (MCC vs KEA)
  - Course split (MBBS vs BDS)

Cross-scenario:
  - Which scenario gives the MOST safe options?
  - What does KEA add over MCC-only?
  - What does BDS backup add?
  - Does confirmed 2A domicile unlock significantly more?
```

**Output:**
```python
ScenarioComparison(
    scenarios=[...],
    comparison_table=[
        {"label": "MBBS MCC OBC", "safe": 5, "likely": 12, "borderline": 8, "best_govt": "GMC Chandigarh (rank 8651)"},
        {"label": "MBBS KEA 2A",  "safe": 3, "likely": 8,  "borderline": 5, "best_govt": "BMCRI Bangalore (rank 4510)"},
        ...
    ],
    best_scenario_label="MBBS MCC OBC",
    notes=["KEA with confirmed 2A adds 11 more options", "BDS backup adds 23 more colleges"]
)
```

---

### Layer 5 (Reasoner)

**Input Data (injected into LLM prompt):**
1. `StudentIntent` — what student asked
2. `ScenarioComparison` — all results + comparison table
3. **Knowledge context** (from `air_insights_log.md`):
   - Category multipliers for the student's category
   - Tier classification of their predicted range
   - Round dynamics advice (R2/R3 chances)
   - Volatility of their target colleges
   - Marks-to-rank mapping confidence level
   - Competition ratio for their year

**System Prompt Rules:**
- ONLY mention colleges from shortlists
- NEVER upgrade chance labels
- NEVER state probability percentages
- NEVER say "guaranteed", "will definitely get", "assured admission"
- NEVER invent rank numbers not from engine output
- ALWAYS include disclaimer
- ALWAYS preserve engine warnings
- If marks-based → label as "experimental"
- If KEA data sparse → explicitly say "KEA predictions are low-confidence due to limited R1 data"
- KEA narrative must stay CONSERVATIVE until KA2020-2022 and KEA R1 data repair is complete

**Output:**
```python
CounsellingNarrative(
    summary="With 620 marks (estimated AIR ~5,000-7,000), you have strong MBBS options...",
    primary_path="Apply MCC AIQ in OBC category...",
    backup_path="If MCC doesn't work, KEA 2A (if domicile confirmed) adds...",
    top_colleges=["GMC Chandigarh", "MAMC Delhi", ...],
    risk_areas=["Marks-based AIR is experimental", "KEA 2A depends on domicile..."],
    full_narrative="...(complete counselling text)...",
    model_used="gpt-oss-120b",
)
```

---

### Layer 6 (Validator)

**Input Data:**
- `CounsellingNarrative` from Layer 5
- `ScenarioComparison` (ground truth) from Layer 4

**Checks:**

| # | Rule | How | On Failure |
|---|------|-----|------------|
| 1 | No fake colleges | Every college in narrative ∈ union of all shortlists | Strip narrative, show raw results |
| 2 | No upgraded labels | If LLM says "Safe", engine must also say "Safe" | Strip narrative |
| 3 | No probabilities | Regex: no "X% chance", "probability of" | Remove offending sentence |
| 4 | Disclaimer present | "not.*guarantee" in text | Append disclaimer |
| 5 | Experimental label | If marks-based, "experimental\|estimated" in text | Append warning |
| 6 | KEA grounding | If mentions KEA college, KEA data must exist | Strip KEA claims |
| 7 | Warnings preserved | All engine warnings present | Append missing ones |
| 8 | No guaranteed admission | Regex: no "guaranteed", "will definitely get", "100%", "assured" | Strip sentence |
| 9 | No invented rank range | No rank numbers in narrative unless they came from engine output | Strip sentence |

**Output:**
```python
ValidatedResponse(
    narrative=CounsellingNarrative(...) or None,  # None if stripped
    scenarios=ScenarioComparison(...),
    validation_passed=True/False,
    violations=["Mentioned 'XYZ College' not in shortlists"],
    fallback_used=False/True,
    warnings=[...],
    limitations=[...],
)
```

---

## 4. Knowledge Injection Strategy

The LLM reasoner needs domain knowledge to give good advice. Instead of fine-tuning, we **inject relevant facts** into the system prompt based on the student's profile.

### What gets injected (dynamically per query):

```python
# knowledge.py builds a context string based on student profile

def build_knowledge_context(intent: StudentIntent, comparison: ScenarioComparison) -> str:
    """
    Selects relevant facts from air_insights_log.md analysis
    and formats them for the LLM system prompt.
    """
    sections = []

    # 1. Category-specific multiplier
    if intent.national_category == "OBC":
        sections.append("OBC closing ranks are typically 1.3-1.8x General rank for same college.")

    # 2. Marks-to-rank context (if marks-only)
    if intent.marks and not intent.actual_air:
        sections.append(f"At {intent.marks} marks (2025), approximate AIR ≈ {lookup_approx_air(intent.marks)}.")
        sections.append("Marks-to-AIR conversion is EXPERIMENTAL. Real AIR can differ by ±30%.")

    # 3. Tier context
    air_used = comparison.scenarios[0].student_result.rank_used.air
    if air_used <= 1000:
        sections.append("Student is in ELITE tier. Colleges here have very stable ranks (CV<0.02).")
    elif air_used <= 5000:
        sections.append("Student is in Tier 1. Most colleges stable (CV 0.01-0.05). Very competitive.")
    elif air_used <= 15000:
        sections.append("Student is in Tier 2 (most predictable, median error ~9.5%).")
    # ...

    # 4. Round dynamics
    sections.append("If not allotted in R1: R2 adds ~4,000 to closing rank (median). STRAY adds ~14,500.")
    sections.append("94% of STRAY round candidates are new entries (not from R1).")

    # 5. Competition context
    sections.append("2025 competition: 46:1 (1.2M qualified for 26K AIQ seats).")

    # 6. New colleges warning
    sections.append("159 new colleges in 2025 have NO historical data — predictions may be unavailable.")

    return "\n".join(f"• {s}" for s in sections)
```

---

## 5. LLM Client Configuration

### API Format (OpenAI-compatible, model-agnostic)

```python
# llm_client.py — model-agnostic client
# API key loaded from environment variable ONLY (never hardcoded)

import os
import httpx

# Loaded from .env via python-dotenv or os.environ
SIEMENS_API_KEY = os.environ["SIEMENS_API_KEY"]

# Endpoint URL (to be confirmed during API discovery)
# Typical: https://api.siemens.ai/v1/chat/completions
SIEMENS_ENDPOINT = os.environ.get("SIEMENS_API_ENDPOINT", "")

# Model routing — configured via .env, not hardcoded
# All calls go through the same model-agnostic client.
# The caller specifies model + params; client handles transport only.
DEFAULT_MODELS = {
    "primary": os.environ.get("LLM_MODEL_PRIMARY", "deepseek-v4-flash"),
    "narrative": os.environ.get("LLM_MODEL_NARRATIVE", "gpt-oss-120b"),
    "fallback": os.environ.get("LLM_MODEL_FALLBACK", "qwen-3.6-27b"),
}

# Model-agnostic call interface:
def chat_completion(
    model: str,
    messages: list[dict],
    temperature: float = 0.3,
    max_tokens: int = 2000,
    timeout: int = 30,
) -> dict:
    """Single model-agnostic entry point. Any available model can be passed."""
    ...
```

### Retry & Fallback Strategy (model-agnostic)

```
Call intent_parser (model=DEFAULT_MODELS["primary"])
    → If fails: retry once with same model
    → If still fails: try DEFAULT_MODELS["fallback"]
    → If all fail: return ClarificationNeeded("Please fill form manually")

Call reasoner (model=DEFAULT_MODELS["narrative"])
    → If fails: retry once with same model
    → If still fails: try DEFAULT_MODELS["primary"] as reasoner
    → If all fail: return raw StudentResult tables (no narrative)

Any model in the available list can be swapped in via .env without code changes.
```

---

## 6. Implementation Steps (Build Order)

| Step | File | LLM? | Testable Offline? | Dependencies |
|------|------|-------|-------------------|--------------|
| **1** | `models.py` | No | Yes | None |
| **2** | `slot_resolver.py` | No | Yes | models.py |
| **3** | `executor.py` | No | Yes | models.py, existing pipeline |
| **4** | `comparator.py` | No | Yes | models.py |
| **5** | `validator.py` | No | Yes | models.py |
| **6** | `knowledge.py` | No | Yes | analysis data |
| **7** | `prompts.py` | No | Yes | Static strings |
| **8** | `llm_client.py` | Config | Mock | API key |
| **9** | `intent_parser.py` | Yes | Mock | llm_client, models, prompts |
| **10** | `reasoner.py` | Yes | Mock | llm_client, models, prompts, knowledge |
| **11** | `orchestrator.py` | Yes | Mock | All above |
| **12** | Tests (all) | No | Yes | Mocked LLM responses |
| **13** | `counsellor_demo.py` | Yes | No | Real API |

**Steps 1-7 are 100% deterministic. Steps 8-13 use LLM but are testable with mocks.**

---

## 7. Dataclass Definitions (Complete)

### StudentIntent (Layer 1 output)

```python
@dataclass(frozen=True)
class StudentIntent:
    marks: int | None
    actual_air: int | None
    national_category: str | None       # General/OBC/SC/ST/EWS
    home_state: str | None
    pwd: bool
    karnataka_interest: bool
    karnataka_domicile: bool | None     # None = not stated
    karnataka_category: str | None      # GM/1/2A/2B/3A/3B/SC/ST
    course_pref: str                    # "MBBS" | "BDS" | "MBBS+BDS"
    college_type_pref: str              # "any" | "government" | "deemed"
    bds_backup: bool
    missing_slots: tuple[str, ...]      # required but not provided
    uncertain_slots: tuple[str, ...]    # hedged by student
    ambiguity_notes: tuple[str, ...]    # human-readable notes
    raw_query: str                      # original text
```

### ScenarioSpec (Layer 2 output)

```python
@dataclass(frozen=True)
class ScenarioSpec:
    label: str                          # "MBBS, MCC OBC"
    description: str                    # why this scenario exists
    marks: int | None
    actual_air: int | None
    national_category: str
    home_state: str
    pwd: bool
    karnataka_interest: bool
    karnataka_domicile: bool
    karnataka_category: str | None
    course_pref: str
    college_type_pref: str
```

### ScenarioResult (Layer 3 output)

```python
@dataclass(frozen=True)
class ScenarioResult:
    spec: ScenarioSpec
    student_result: StudentResult       # from existing engine
    error: str | None                   # None if success
```

### ScenarioComparison (Layer 4 output)

```python
@dataclass(frozen=True)
class ComparisonRow:
    label: str
    safe_count: int
    likely_count: int
    borderline_count: int
    total_options: int
    best_college: str | None
    best_chance: str | None
    authority_split: str                # "MCC: 15, KEA: 8"

@dataclass(frozen=True)
class ScenarioComparison:
    results: tuple[ScenarioResult, ...]
    comparison_table: tuple[ComparisonRow, ...]
    best_scenario_label: str | None
    notes: tuple[str, ...]
```

### CounsellingNarrative (Layer 5 output)

```python
@dataclass
class CounsellingNarrative:
    summary: str                        # 2-3 sentence conclusion
    primary_path: str                   # recommended strategy
    backup_path: str | None             # alternative
    top_colleges: list[str]             # from shortlists ONLY
    risk_areas: list[str]
    missing_data_caveats: list[str]
    full_narrative: str                 # complete LLM text
    model_used: str
    raw_llm_response: str               # for debugging
    tokens_used: int | None
```

### ValidatedResponse (Layer 6 output / FINAL)

```python
@dataclass
class ValidatedResponse:
    narrative: CounsellingNarrative | None   # None if validation failed
    scenarios: ScenarioComparison
    validation_passed: bool
    violations: list[str]                    # what LLM got wrong
    fallback_used: bool                      # True = narrative stripped
    warnings: list[str]                      # merged from engine
    limitations: list[str]                   # always shown
    processing_time_ms: int
```

---

## 8. Prompt Templates

### Intent Parser (System)

```
You are an intake parser for a NEET UG college prediction system.
Extract structured fields from the student's message into JSON.

EXTRACTION RULES:
- If a field is not mentioned → null
- If hedged ("maybe", "I think", "probably") → extract value AND add to uncertain_slots
- Never assume Karnataka domicile from home_state alone
- Never infer KEA category from national category (they are separate systems)
- "BDS backup" / "BDS fallback" → course_pref="MBBS", bds_backup=true
- marks must be 0-720 integer
- actual_air must be positive integer

VALID VALUES:
- national_category: General, OBC, SC, ST, EWS
- karnataka_category: GM, 1, 2A, 2B, 3A, 3B, SC, ST
- course_pref: MBBS, BDS, MBBS+BDS
- college_type_pref: any, government, deemed

OUTPUT: Valid JSON matching StudentIntent schema. No markdown, no explanation.
```

### Reasoner (System)

```
You are a NEET UG counselling advisor. You have been given:
1. The student's query and intent
2. Deterministic prediction results from our engine (college shortlists with chance labels)
3. Scenario comparisons
4. Domain knowledge about NEET patterns

YOUR JOB: Write clear, student-friendly counselling advice based ONLY on the provided data.

STRICT RULES (VIOLATIONS = RESPONSE WILL BE DISCARDED):
1. ONLY mention colleges that appear in the provided shortlists
2. NEVER upgrade a chance label (if engine says "Borderline", you say "Borderline" or "Uncertain")
3. NEVER state probability percentages ("30% chance", "7 out of 10")
4. NEVER claim exact AIR from marks
5. ALWAYS include: "This is not an admission guarantee. Verify from official sources."
6. If marks-based AIR was used, ALWAYS say "estimated/experimental"
7. If KEA data shows "Insufficient data", do NOT make KEA college claims
8. PRESERVE all warnings from the prediction engine
9. Do NOT invent round-specific advice unless supported by data
10. Be honest about uncertainty — "we cannot predict" is a valid answer

REQUIRED SECTIONS:
- Summary (2-3 sentences: what's the student's situation?)
- Primary Recommendation (best path with top colleges)
- Backup Path (if applicable)
- Top 5-10 Colleges (name + chance label from shortlist)
- Risk Areas (what could go wrong)
- What to Verify (official sources to check)

DOMAIN CONTEXT (use this for richer advice):
{knowledge_context}
```

---

## 9. What the LLM is FORBIDDEN From

| Forbidden Action | Why | Enforcement |
|-----------------|-----|-------------|
| Predict rank from marks | Deterministic engine does this | Layer 3 |
| Look up closing ranks | Deterministic engine does this | Layer 3 |
| Classify chance labels | Engine: Safe/Likely/Borderline/Unlikely | Validator rule |
| Invent colleges | Must exist in curated colleges.csv | Validator rule |
| Override/remove warnings | Safety requirement | Validator rule |
| Skip disclaimer | Legal/ethical | Validator rule |
| Derive KEA category from national | Separate systems | Intent parser rules |
| State % probabilities | We don't compute these | Validator regex |
| Claim certainty | Historical data ≠ guarantee | Prompt rules |

---

## 10. Test Strategy

| Test File | What It Tests | LLM Needed? |
|-----------|--------------|-------------|
| `test_models.py` | Dataclass creation, validation, edge cases | No |
| `test_slot_resolver.py` | Scenario branching: missing slots, uncertain, BDS backup | No |
| `test_executor.py` | Scenarios produce valid StudentResults | No |
| `test_comparator.py` | Comparison table, best scenario, notes | No |
| `test_validator.py` | Fake college detection, label upgrades, regex checks | No |
| `test_knowledge.py` | Knowledge context varies by profile | No |
| `test_intent_parser.py` | JSON extraction from mocked LLM responses | Mock |
| `test_orchestrator.py` | End-to-end with mocked LLM | Mock |

**Target: 40-50 new tests, ALL runnable without API key.**

---

## 11. Acceptance Criteria

- [ ] All existing 310+ tests still pass (no regression)
- [ ] 40+ new counsellor tests pass (mocked LLM)
- [ ] Validator catches: fake college, upgraded label, missing disclaimer, probability claims
- [ ] Fallback works: if LLM fails → structured result still shown
- [ ] CLI demo works with real Siemens API (manual test)
- [ ] No prediction logic modified
- [ ] No curated data modified
- [ ] Response time < 10s for full pipeline (2 LLM calls)

---

## 12. Example End-to-End Flow

**Student says:** "I scored 580 in NEET, I'm SC category from Bihar, want government MBBS only"

**Layer 1 (Intent Parser) → deepseek-v4-flash:**
```json
{
    "marks": 580,
    "actual_air": null,
    "national_category": "SC",
    "home_state": "Bihar",
    "pwd": false,
    "karnataka_interest": false,
    "karnataka_domicile": null,
    "karnataka_category": null,
    "course_pref": "MBBS",
    "college_type_pref": "government",
    "bds_backup": false,
    "missing_slots": [],
    "uncertain_slots": [],
    "ambiguity_notes": []
}
```

**Layer 2 (Slot Resolver):**
```python
# No ambiguity → single scenario
scenarios = [
    ScenarioSpec(
        label="MBBS, MCC Government, SC category",
        description="Direct prediction using marks-estimated AIR",
        marks=580, national_category="SC", home_state="Bihar",
        karnataka_interest=False, course_pref="MBBS",
        college_type_pref="government", ...
    )
]
```

**Layer 3 (Executor):**
- Calls `run_prediction(UnifiedInput(marks=580, national_category="SC", ...))`
- Gets `StudentResult` with shortlist of ~15-25 government colleges in SC category
- Marks 580 → estimated AIR ~3,000-5,000 (conservative)
- SC category multiplier means accessing colleges up to rank ~20,000-30,000 in SC closing

**Layer 4 (Comparator):**
- Single scenario → simple table
- Notes: "SC category significantly expands options vs General"

**Layer 5 (Reasoner) → gpt-oss-120b:**
```
With 580 marks (estimated AIR ~3,500-5,000), you're in a strong position for
government MBBS through MCC AIQ in SC category. SC closing ranks are typically
4-6x the General closing rank for the same college, which significantly expands
your options.

**Top Colleges (from shortlist):**
1. GMC Bihar Sharif - Safe
2. Patna Medical College - Likely
3. IGIMS Patna - Likely
4. ...

**Risk Areas:**
- AIR estimation from marks is experimental (±30% uncertainty)
- Actual AIR may differ from estimate

**What to Verify:**
- Confirm your exact AIR when results are out
- Check MCC official counselling schedule
- Verify SC certificate validity for AIQ

This is not an admission guarantee. Verify from official sources.
```

**Layer 6 (Validator):**
- ✓ All colleges in shortlist
- ✓ No upgraded labels
- ✓ Disclaimer present
- ✓ "experimental/estimated" present
- ✓ Warnings preserved
- → validation_passed = True

---

## 13. Risk Mitigation

| Risk | Mitigation |
|------|-----------|
| Siemens API down | Fallback to raw StudentResult tables |
| LLM hallucinates colleges | Validator strips narrative |
| LLM upgrades safety labels | Validator strips narrative |
| Slow response (>30s) | Timeout + show partial results |
| API key expires | Clear error message + structured fallback |
| Model quality poor | Model fallback chain: gpt-oss-120b → deepseek-v4-flash → qwen-3.6-27b |

---

## 14. API Discovery (First Step Before Implementation)

Before building, we need to confirm:

1. **API endpoint URL** — What's the base URL for Siemens LLM API?
2. **Request format** — Is it OpenAI-compatible (`/v1/chat/completions`)?
3. **Authentication** — Header format (`Authorization: Bearer SIAK-...`)?
4. **Rate limits** — How many calls/minute?
5. **Model availability** — Do all listed models actually work?

**Test script to run first:**
```python
import os
import httpx
from dotenv import load_dotenv

load_dotenv()  # loads .env
api_key = os.environ["SIEMENS_API_KEY"]

# Try common Siemens AI endpoint patterns
endpoints = [
    "https://api.siemens.ai/v1/chat/completions",
    "https://llm.siemens.ai/v1/chat/completions",
    # ... other possibilities
]

headers = {"Authorization": f"Bearer {api_key}"}
payload = {
    "model": "deepseek-v4-flash",
    "messages": [{"role": "user", "content": "Hello"}],
    "max_tokens": 10,
}

for url in endpoints:
    try:
        r = httpx.post(url, json=payload, headers=headers, timeout=10)
        print(f"{url} → {r.status_code}")
    except Exception as e:
        print(f"{url} → {e}")
```

---

## Summary

- **Total new files**: 12 source + 8 test + 1 script = 21 files
- **LLM calls per query**: Exactly 2 (intent + narrative)
- **Fallback**: Always returns structured data even if LLM fails
- **Safety**: 7 validator rules prevent hallucination from reaching user
- **Testability**: 40+ tests run without API key
- **Models**: deepseek-v4-flash (parsing) + gpt-oss-120b (narrative) + qwen-3.6-27b (fallback)
