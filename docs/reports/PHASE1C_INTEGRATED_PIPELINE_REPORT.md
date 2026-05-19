# Phase 1C: Integrated Marks/AIR → College Prediction Pipeline Report

**Date**: 2025-05-17  
**Status**: ACCEPTED  
**Test Suite**: 268 tests passing (43 new + 225 existing, zero regressions)

---

## 1. Summary

Phase 1C delivers a unified prediction pipeline that accepts either NEET marks, actual AIR, or both — and produces college eligibility predictions with appropriate confidence labeling and warnings.

No UI was built. No data was modified. No safety wording was weakened.

---

## 2. Architecture

```
UnifiedInput
    │
    ├── marks provided? ──→ RankEstimator (AFFINE_TWO_POINT)
    │                            │
    │                        RankEstimate
    │                        (best / median / conservative AIR)
    │
    ├── actual_air provided? ──→ Use directly
    │
    ▼
Determine AIR for college prediction:
    ├── actual_air available → use actual_air
    └── marks only           → use conservative_air
    │
    ▼
CandidateProfile(air=...) → college predictor → PredictionResult
    │
    ▼
UnifiedResult
    ├── rank_estimate (if marks provided)
    ├── rank_used (source + air value + explanation)
    ├── college_predictions (MCC + KEA)
    └── warnings[]
```

---

## 3. Three Flows

### Flow A: Actual AIR Only

- Marks-based estimation skipped entirely
- `rank_used.source = "actual"`
- College predictions use actual AIR directly
- No experimental/estimated warnings emitted

### Flow B: Marks Only

- RankEstimator produces best/median/conservative AIR
- `rank_used.source = "estimated_conservative"`
- College predictions use **conservative** AIR (worst-case)
- Warnings include: experimental estimator, estimated AIR in use

### Flow C: Marks + Actual AIR

- Marks-based estimate computed for comparison
- `rank_used.source = "actual"` — actual AIR used for college prediction
- Warning clarifies actual AIR is being used, not estimate

---

## 4. Input Model: `UnifiedInput`

| Field | Type | Required | Default | Validation |
|-------|------|----------|---------|------------|
| marks | int \| None | One of marks/air | None | 0–720 |
| actual_air | int \| None | One of marks/air | None | ≥ 1 |
| national_category | str | Yes | — | General/OBC/SC/ST/EWS |
| home_state | str | Yes | — | Free text |
| pwd | bool | No | False | — |
| karnataka_interest | bool | No | False | — |
| karnataka_domicile | bool | No | False | — |
| karnataka_category | str \| None | No | None | GM/1/2A/2B/3A/3B/SC/ST |
| course_pref | str | No | MBBS | — |
| college_type_pref | str | No | any | any/government/deemed/central/AIIMS |
| target_year | int | No | 2025 | — |
| normalization | NormalizationMode | No | AFFINE_TWO_POINT | Enum |

**Key design decisions:**
- Karnataka category is **never** auto-derived from national category
- Default normalization is AFFINE_TWO_POINT (accepted in Phase 1B-D)
- `frozen=True` dataclass — immutable after construction

---

## 5. Output Model: `UnifiedResult`

| Field | Type | Description |
|-------|------|-------------|
| input | UnifiedInput | Echo of input for traceability |
| rank_estimate | RankEstimate \| None | None when actual AIR only |
| rank_used | RankUsed | AIR value + source + explanation |
| college_predictions | PredictionResult | MCC + KEA predictions |
| warnings | list[str] | All applicable warnings |

---

## 6. Warnings (Always Present)

1. "Prediction is based on historical data and is not an admission guarantee."
2. "MCC and KEA eligibility/category rules must be verified from official documents."
3. "KEA predictions are limited because KEA R1 data is sparse."

### Conditional Warnings

- Marks provided: "Marks-to-AIR estimator is experimental and medium confidence..."
- Estimated AIR used: "College prediction uses conservative estimated AIR..."
- Actual AIR with marks: "Actual AIR was provided, so college prediction uses actual AIR..."

---

## 7. Test Coverage (43 tests)

| Test Class | Count | Purpose |
|-----------|-------|---------|
| TestInputValidation | 12 | All validation rules |
| TestDefaults | 3 | Default normalization, year, course |
| TestFlowActualAIR | 6 | Flow A behavior |
| TestFlowMarksOnly | 7 | Flow B: conservative AIR, warnings |
| TestFlowMarksAndAIR | 4 | Flow C: actual AIR takes precedence |
| TestCategoryBehavior | 2 | Category doesn't affect AIR; KEA not inferred |
| TestWarnings | 3 | Required warnings always present |
| TestResultStructure | 3 | Result has rank + college sections |
| TestExplainer | 3 | Formatted output for all 3 flows |

---

## 8. CLI Verification

```bash
# Flow A: Actual AIR only
python scripts/integrated_cli_demo.py --air 15000 --category OBC --state Karnataka \
    --karnataka-interest --karnataka-domicile --karnataka-category 2A
# → Source: actual, AIR: 15,000, MCC: 1277 predictions, KEA: 192

# Flow B: Marks only
python scripts/integrated_cli_demo.py --marks 620 --category General --state Delhi
# → Conservative AIR: 34,316, Source: estimated_conservative, MCC: 780 predictions

# Flow C: Marks + Actual AIR
python scripts/integrated_cli_demo.py --marks 620 --air 25000 --category General --state Delhi
# → Source: actual, AIR: 25,000, estimate shown for comparison
```

---

## 9. Files Created

| File | Purpose |
|------|---------|
| `src/neet_predictor/integrated/__init__.py` | Package exports |
| `src/neet_predictor/integrated/pipeline.py` | UnifiedInput, UnifiedResult, run_prediction() |
| `src/neet_predictor/integrated/explainer.py` | format_unified_result() |
| `scripts/integrated_cli_demo.py` | CLI for all 3 flows |
| `tests/test_integrated_pipeline.py` | 43 tests |
| `docs/reports/PHASE1C_INTEGRATED_PIPELINE_REPORT.md` | This report |

---

## 10. What Was NOT Done (By Design)

- No Streamlit UI
- No new data scraped or curated data modified
- No safety/disclaimer wording weakened
- No existing Phase 1B-A or 1B-D behavior changed
- No inference of KEA category from national category

---

## 11. Full Test Suite

```
268 passed in 62.42s
```

Zero regressions across all existing phases.
