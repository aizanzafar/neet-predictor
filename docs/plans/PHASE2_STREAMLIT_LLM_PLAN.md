# Phase 2: Streamlit UI + LLM Integration — Execution Plan

> Created: 2026-05-19
> Status: READY TO IMPLEMENT
> Prerequisite: Phase 1A-1F complete (prediction engine + counsellor module built)

---

## 0. Current State (What We Have)

### Working Components
| Component | Status | Location |
|-----------|--------|----------|
| Rank Estimator | ✅ Fixed, 5% accuracy | `src/neet_predictor/rank/estimator.py` |
| College Predictor | ✅ MCC + KEA | `src/neet_predictor/college/predictor.py` |
| Integrated Pipeline | ✅ UnifiedInput → UnifiedResult | `src/neet_predictor/integrated/pipeline.py` |
| Counsellor 6-Layer | ✅ All layers built | `src/neet_predictor/counsellor/` |
| LLM Client (Siemens) | ✅ Ready | `src/neet_predictor/counsellor/llm_client.py` |
| R2 Round Intelligence | ✅ Added | `src/neet_predictor/counsellor/reasoner.py` |
| Tests | ✅ 402 passing | `tests/` |

### Key Gap: `target_year` Not Flowing Through Counsellor
- `UnifiedInput.target_year` exists (defaults to 2025)
- `ScenarioSpec` does NOT have `target_year`
- `StudentIntent` does NOT have `target_year`
- Intent parser prompt does NOT extract year
- This means: "627 marks in 2022" → always predicts against 2025

---

## 1. Critical User Query Types

| # | Query Type | Example | Year Handling | Engine Path |
|---|-----------|---------|---------------|-------------|
| 1 | **Forward prediction** | "450 marks in 2026, what colleges?" | 2026 (no data) → weighted cross-year | Marks → Rank → Colleges |
| 2 | **Current year** | "I got 580 marks, what rank?" | 2025 (default, has 530 calibration points) | Marks → Rank |
| 3 | **Historical validation** | "I scored 627 in 2022" | 2022 (dense data, direct interpolation) | Marks → Rank → Colleges |
| 4 | **Have rank already** | "AIR 15000, General, Karnataka" | Year irrelevant for college pred | AIR → Colleges |
| 5 | **Comparison** | "580 marks OBC, MCC vs KEA?" | Extract from context or default 2025 | Multi-scenario |
| 6 | **Just rank** | "What rank for 550 in 2025?" | Explicit | Marks → Rank only |
| 7 | **Vague/incomplete** | "I'll get around 500" | Default 2025 | Clarification needed |
| 8 | **College-specific** | "Can I get Mysore MC with 627?" | Need year + category + domicile | Targeted lookup |

### Edge Cases the LLM Must Handle
- "2026" → No historical data → Must warn "forward prediction, high uncertainty"
- "2022" → Dense data → High confidence (direct interpolation activates)
- No year mentioned → Default to CURRENT year (2025)
- "Last year" / "This year" → Resolve relative references
- "NEET 2024 result" → Year = 2024

---

## 2. Architecture Changes Required

### 2.1 Add `target_year` to StudentIntent
```python
# models.py
@dataclass(frozen=True)
class StudentIntent:
    ...
    target_year: int | None  # None = current year (2025)
    ...
```

### 2.2 Add `target_year` to ScenarioSpec
```python
# models.py
@dataclass(frozen=True)
class ScenarioSpec:
    ...
    target_year: int | None  # Passed to UnifiedInput
    ...
```

### 2.3 Update Intent Parser Prompt
Add to extraction slots:
```
- target_year: integer (the NEET exam year, 2020-2026). If not stated, null.
  - "in 2022" → 2022
  - "last year" → 2024 (relative to current year 2025)
  - "next year" → 2026
  - If no year context at all → null (system defaults to 2025)
```

### 2.4 Update Executor
```python
def _spec_to_unified_input(spec: ScenarioSpec) -> UnifiedInput:
    ...
    target_year = spec.target_year or VALIDATION_YEAR
    return UnifiedInput(..., target_year=target_year)
```

### 2.5 Update Slot Resolver
Pass `intent.target_year` through to all ScenarioSpec instances.

---

## 3. Streamlit UI Design

### 3.1 Layout
```
┌─────────────────────────────────────────────────────┐
│  🏥 NEET UG College Predictor                        │
│  Powered by historical data (2020-2025)             │
├─────────────────────────────────────────────────────┤
│                                                      │
│  ┌─────────────────────────────────────────────┐    │
│  │  💬 Ask anything about NEET admissions...    │    │
│  │  [___________________________________] [Ask] │    │
│  └─────────────────────────────────────────────┘    │
│                                                      │
│  ─── OR fill the form below ───                     │
│                                                      │
│  NEET Marks: [___] Year: [2025▾] AIR: [___]         │
│  Category: [General▾]  State: [___________]         │
│  Karnataka: ☐ Interest  ☐ Domicile  KEA Cat: [▾]   │
│  Course: ○MBBS ○BDS ○Both  Type: [Any▾]            │
│                                                      │
│  [🔍 Predict]                                       │
├─────────────────────────────────────────────────────┤
│                                                      │
│  📊 RESULTS                                         │
│  ┌─────────────────────────────────────────────┐    │
│  │ Rank Estimate                                │    │
│  │ ████████░░ AIR 8,892 - 10,445 (median 9,668)│    │
│  │ Confidence: HIGH (direct interpolation)      │    │
│  └─────────────────────────────────────────────┘    │
│                                                      │
│  ┌─────────────────────────────────────────────┐    │
│  │ 🏫 College Predictions                       │    │
│  │ [Tab: MCC AIQ] [Tab: KEA Karnataka]          │    │
│  │                                              │    │
│  │ ✅ Safe (143) | 🟡 Likely (156) | ⚠️ Border. │    │
│  │                                              │    │
│  │ Sortable table with columns:                 │    │
│  │ College | State | Chance | Margin | R1 Ranks │    │
│  └─────────────────────────────────────────────┘    │
│                                                      │
│  ┌─────────────────────────────────────────────┐    │
│  │ 🤖 AI Analysis (powered by Siemens LLM)     │    │
│  │                                              │    │
│  │ "Based on your marks of 627 in 2022..."      │    │
│  │ [Full narrative from reasoner]               │    │
│  └─────────────────────────────────────────────┘    │
│                                                      │
│  ⚠️ Disclaimer: Not an admission guarantee.         │
└─────────────────────────────────────────────────────┘
```

### 3.2 Two Input Modes
1. **Chat mode**: Natural language → LLM intent parser → full pipeline
2. **Form mode**: Direct structured input → skip LLM call #1 → faster

### 3.3 Key UI Features
- Real-time rank estimation as user types marks
- Year selector (2020-2026) with confidence indicators
- Expandable college cards with R1/R2 round data
- "R2 Opportunities" section for Unlikely colleges
- Download results as PDF/CSV
- Session history (compare different scenarios)

---

## 4. File Plan

```
app/
├── streamlit_app.py           # Main Streamlit entry point
├── components/
│   ├── __init__.py
│   ├── chat_input.py          # Natural language input box
│   ├── form_input.py          # Structured form input
│   ├── rank_display.py        # Rank estimation visualization
│   ├── college_table.py       # Filterable/sortable college table
│   ├── narrative_display.py   # LLM narrative card
│   └── sidebar.py             # Config & session info
├── config.py                  # Streamlit settings
└── utils.py                   # Session state helpers
```

---

## 5. Execution Steps (Build Order)

### Step 1: Add `target_year` to Counsellor Pipeline
- Add field to `StudentIntent`, `ScenarioSpec`
- Update intent parser prompt
- Update slot resolver to propagate
- Update executor to pass to `UnifiedInput`
- Update tests
- **Estimated complexity**: Small (6 files, ~30 lines each)

### Step 2: Build Minimal Streamlit App (Form Mode Only)
- Install streamlit
- Build form input → UnifiedInput → run_prediction → display
- No LLM needed yet (direct structured input)
- Shows: rank estimate + college table + filters
- **Deliverable**: Working local UI with `streamlit run app/streamlit_app.py`

### Step 3: Add Chat Mode (LLM Integration)
- Add chat input component
- Wire to `run_counsellor()` pipeline
- Display narrative + structured results
- Handle ClarificationNeeded (show follow-up questions)
- **Requires**: Siemens API accessible locally

### Step 4: Polish & Edge Cases
- Year-aware confidence messaging:
  - 2022: "HIGH confidence (dense RTI data)"
  - 2025: "HIGH confidence (530 calibration points)"
  - 2026: "LOW confidence (forward extrapolation)"
- R2 opportunity badges on college cards
- Error handling for API timeouts
- Rate limiting awareness

### Step 5: Validation & Testing
- Test all 8 query types from Section 1
- Compare predictions against RTI ground truth
- Performance benchmarking (response time < 3s for form, < 8s with LLM)

---

## 6. Forward Prediction Strategy (2026 / Unknown Years)

For years with NO training data (e.g., 2026):
1. RankEstimator falls back to weighted cross-year percentile method
2. Year weights still apply: 2024 gets 40%, 2023 gets 25%, etc.
3. **LLM should communicate**: "This is a forward projection. Actual ranks depend on 2026 paper difficulty and candidate pool."
4. Confidence label: "medium" or "low" (not "high")
5. Wider confidence band (best-case to conservative range is larger)

For years WITH dense data (e.g., 2022, 2025):
1. Direct interpolation activates
2. Tight confidence band
3. Label: "high"

---

## 7. Data Assets Available for LLM Context

| Asset | Size | Use Case |
|-------|------|----------|
| `marks_rank_points.csv` | 687 rows | Rank estimation anchors |
| `closing_ranks.csv` | 45,139 rows | College prediction ground truth |
| `colleges.csv` | 1,422 colleges | College metadata |
| `exam_years.csv` | 6 years | Competition stats per year |
| `air_insights_log.md` | 96KB | Domain knowledge for LLM |
| `allotments.csv` | 308,888 rows | Historical allotment data |

The LLM never queries these directly — the deterministic engine does all data lookups. The LLM only receives pre-computed results and explains them.

---

## 8. Success Criteria

| Criterion | Target |
|-----------|--------|
| Form mode response time | < 3 seconds |
| Chat mode response time (with LLM) | < 8 seconds |
| Rank accuracy (known years) | < 10% error |
| Rank accuracy (forward) | < 30% error |
| College prediction: RTI match | Ground truth colleges appear in Safe/Likely |
| R2 intelligence | Mysore MC shows as "achievable in R2" |
| Validation pass rate | > 95% (LLM doesn't hallucinate) |

---

## 9. Dependencies

| Dependency | Status | Notes |
|-----------|--------|-------|
| Python 3.12 | ✅ | Installed |
| streamlit | ❌ Need install | `pip install streamlit` |
| httpx | ✅ | For Siemens API |
| pandas/numpy | ✅ | Data processing |
| Siemens API key | ✅ | In `.env` |
| Network (local) | ✅ | User confirms API works locally |

---

## 10. Start Command

```bash
cd neet-predictor
pip install streamlit
streamlit run app/streamlit_app.py
```

Opens browser at http://localhost:8501










## Architecture: Hybrid Prediction Agent

```
User Query: "625 marks in 2022, General"
         │
         ▼
┌──────────────────────┐     ┌────────────────────────┐
│  Dataset Estimator   │     │    Web Search Module    │
│  (verified 6yr data) │     │  (public rank tables)  │
│  AIR: 10,323         │     │  AIR: ~11,777          │
│  Range: 9,525-11,120 │     │  Range: 10,000-14,000  │
└──────────┬───────────┘     └──────────┬─────────────┘
           │                            │
           ▼                            ▼
      ┌─────────────────────────────────────┐
      │         Hybrid Agent (merge)         │
      │  Agreement: STRONG (12.3% diverge)   │
      │  Final: 9,525 - 10,323 - 11,120     │
      │  + percentile context (top 0.59%)    │
      │  + counselling advice                │
      │  + tie-breaking notes                │
      └──────────────────┬──────────────────┘
                         ▼
              Reasoning Output (enriched)
```

**Files created:**
- src/neet_predictor/integrated/web_search.py — Web search module with SerpAPI, DuckDuckGo, and built-in public rank tables
- src/neet_predictor/integrated/hybrid_agent.py — Merges dataset + web with confidence weighting

**Files modified:**
- src/neet_predictor/integrated/reasoning.py — Added `_augment_with_web_search()`, web cross-check in output
- app/streamlit_app.py — Shows agreement badge in UI

**Key design decisions:**
1. **Dataset is always primary** — verified data wins when sources diverge
2. **Web adds context** — percentile, counselling advice, tie-breaking (what Gemma does well)
3. **Agreement scoring** — tells user how much sources align (strong/moderate/divergent)
4. **Graceful fallback** — if web fails, dataset alone still works (all 393 tests pass)
5. **When real SerpAPI/DuckDuckGo is available** (set `SERP_API_KEY`), it'll use live search results instead of the built-in tables
