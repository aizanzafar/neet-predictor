# Phase 1B-A: AIR-Based College Predictor — Report

## Status: COMPLETE

**Date:** 2025-05-17
**Tests:** 126/126 pass (65 Phase 1A + 61 Phase 1B-A)

---

## What Was Built

### Files Created/Modified

| File | Purpose |
|------|---------|
| `src/neet_predictor/college/eligibility.py` | Candidate profile, MCC/KEA category mapping |
| `src/neet_predictor/college/predictor.py` | Core prediction engine: data loading, normalization, chance classification |
| `src/neet_predictor/college/explainer.py` | Human-readable output formatting |
| `src/neet_predictor/college/__init__.py` | Package exports |
| `tests/test_predictor.py` | 61 tests covering all required scenarios |
| `cli_demo.py` | CLI interface for running predictions |

### Architecture

```
CandidateProfile (input)
  → eligibility.py   (category/quota mapping)
  → predictor.py     (R1 data → chance classification)
  → explainer.py     (formatted output)
```

---

## Input Specification

| Field | Type | Required | Values |
|-------|------|----------|--------|
| AIR | int | Yes | Actual All India Rank |
| national_category | str | Yes | General, OBC, SC, ST, EWS |
| home_state | str | Yes | Any Indian state |
| pwd | bool | No | Person with Disability |
| course_pref | str | No | MBBS (default), BDS |
| college_type_pref | str | No | any (default), government, deemed, central, AIIMS |
| karnataka_interest | bool | No | Interest in KEA counselling |
| karnataka_domicile | bool | No | Karnataka domicile status |
| karnataka_category | str | No | KEA category: GM, 2A, 2B, 3A, 3B, SC, ST, 1 |

**Not used:** NEET marks. AIR is never estimated.

---

## Prediction Algorithm

### Primary Signal: Round 1 Closing Ranks Only

For each (college, seat_category, quota) combination:

1. Gather R1 closing ranks across all available years
2. If < 2 R1 years → **"Insufficient data"**
3. Compute margin per year: `(closing_rank - AIR) / closing_rank`
   - Positive margin = candidate's rank is better → would have been admitted
   - Negative margin = candidate's rank is worse → would not have been admitted
4. Apply year weights: 2024=0.40, 2023=0.25, 2022=0.18, 2021=0.10, 2020=0.07

### Chance Labels (Conservative)

| Label | Criteria |
|-------|----------|
| **Safe** | Admitted ALL years AND min margin ≥ 20% AND 3+ years of R1 data |
| **Likely** | Admitted ALL years (any positive margin) |
| **Borderline** | Admitted SOME years, OR weighted margin ≥ −10% |
| **Unlikely** | Everything else |

### Conservative Bias

- **Safe requires 3+ years**: Even with 20%+ margin, 2 years of data caps at "Likely"
- **Min-margin gate**: Safe requires the *worst* year to still have 20% margin
- **Trending-down caught**: Declining closing ranks reduce min_margin, preventing false Safe
- **Later rounds never averaged**: R2/MOPUP/STRAY shown as supplementary only

---

## Category System Separation

### MCC (All-India) Categories

| National Category | Eligible MCC Seat Categories |
|-------------------|------------------------------|
| General | Open |
| OBC | OBC, Open |
| SC | SC, Open |
| ST | ST, Open |
| EWS | EWS, Open |
| Any + PwD | PwD variant + base categories |

### KEA (Karnataka) Categories

| Scenario | Eligible KEA Categories |
|----------|------------------------|
| No Karnataka interest | (empty — no KEA predictions) |
| Interest but no domicile | GM only |
| Domicile + category=2A | 2AG, GM |
| Domicile + category=SC | SCG, GM |
| Domicile + category=None | GM only (exploratory) |

### Hard Rules Enforced

- MCC categories never include KEA categories (and vice versa)
- National OBC is **never** auto-mapped to KEA 2A/2B/3A/3B
- Non-domicile candidates see only GM in KEA
- Category=None (Not Sure) shows KEA as exploratory with warning

---

## MCC Quota Filtering

| college_type_pref | Quotas Shown |
|-------------------|-------------|
| any | All India, Open Seat Quota, Deemed/Paid Seats Quota, AMS |
| government | All India |
| deemed | Deemed/Paid Seats Quota |
| central | AMS, Open Seat Quota |
| AIIMS | AMS |

---

## Data Normalization

Applied at prediction time (curated data unchanged):

- **PwD categories**: "Open PwD" → "PwD Open" (both forms exist in data)
- **Quota artifacts**: "Deemed/Pai d Seats Quota" → "Deemed/Paid Seats Quota" (PDF parsing)
- **Pseudo-categories**: "Reported" removed
- **Null quotas**: Filled with empty string (KEA has no quota column)

---

## Test Results

### 61 Phase 1B-A Tests

| Test Class | Count | Coverage |
|------------|-------|----------|
| TestMCCCategories | 12 | MCC category mapping, PwD variants, no KEA leakage |
| TestKEACategories | 14 | KEA category mapping, domicile logic, no MCC leakage, OBC isolation |
| TestClassifyChance | 16 | All chance labels, conservative downgrades, margins, false-safe prevention |
| TestNormalization | 4 | PwD normalization, Reported removal, quota artifacts, null handling |
| TestPredictorIntegration | 15 | End-to-end with real data, category separation, R1-only, supplementary, KEA insufficient |

### Full Suite

```
126 passed in 22.60s
```

---

## Demo Examples

### Example 1: General, AIR 5000, Government Colleges

```
python cli_demo.py --air 5000 --category General --state Delhi --college-type government
```

| Chance | Count |
|--------|-------|
| Safe | 179 |
| Likely | 95 |
| Borderline | 19 |
| Unlikely | 57 |
| Insufficient data | 312 |
| **Total** | **662** |

### Example 2: OBC, AIR 15000, Karnataka Domicile (KEA 2A)

```
python cli_demo.py --air 15000 --category OBC --state Karnataka \
    --karnataka-interest --karnataka-domicile --karnataka-category 2A
```

| Authority | Chance | Count |
|-----------|--------|-------|
| MCC | Safe | 39 |
| MCC | Likely | 152 |
| MCC | Borderline | 107 |
| MCC | Unlikely | 492 |
| MCC | Insufficient data | 487 |
| KEA | Insufficient data | 192 |

### Example 3: SC, AIR 100, Government Colleges

| Chance | Count |
|--------|-------|
| Safe | 525 |
| Likely | 173 |
| Borderline | 1 |
| Insufficient data | 606 |

### Example 4: General, AIR 50000, Government Colleges

| Chance | Count |
|--------|-------|
| Unlikely | 350 |
| Insufficient data | 312 |

### Example 5: Karnataka Exploratory (category=None)

```
AIR=10000, Domicile=True, Category=None → kea_exploratory=True, all 97 KEA = Insufficient data
```

---

## Known Limitations

### Data Coverage

1. **No 2021 or 2025 R1 data** — only years 2020, 2022, 2023, 2024 have R1 closing ranks
2. **KEA has only 2023 R1 data** — ALL KEA predictions are "Insufficient data"
3. **Max 3 R1 years per college** — no college has 4+ years of R1 data
4. **312 MCC combos have only 1 R1 year** — flagged as Insufficient data
5. **College ownership all "government"** — field not reliable; college_type_pref filters by quota instead

### Prediction Scope

6. **No marks-to-rank estimation** — deliberate; Phase 1B-B scope
7. **Special quotas excluded** — NRI, DU, IP, ESI, AMU, Muslim/Jain minority quotas not in default predictions
8. **Management quota excluded** — MNG seats not shown by default
9. **No state-quota predictions for non-Karnataka states** — only MCC AIQ and KEA STATE_KA
10. **No fee information** — deemed/paid quota fees not displayed in predictions

### Classification Accuracy

11. **Year-to-year fluctuation** — closing ranks can shift ±10-20% between years
12. **New colleges** — colleges with only 1 year of data get "Insufficient data"
13. **Category migration** — some PwD categories changed naming convention across years (normalized but edge cases may remain)
14. **Institutional quota nuances** — AMU/Jamia/JNU quotas have complex eligibility rules not modeled

### Planned Improvements (Future Phases)

- Phase 1B-B: Marks-to-rank estimation
- Phase 2: State-level counselling for additional states
- Phase 3: Fee display and affordability filtering
- Phase 4: Trend analysis and rank inflation detection
