# Phase 1B-B Report: Marks-to-AIR Rank Estimator

**Date:** 2025-07-14  
**Status:** COMPLETE — all tests pass, validation run, known limitations documented

---

## 1. Files Created / Modified

### New files

| File | Purpose |
|------|---------|
| `src/neet_predictor/rank/estimator.py` | Core estimator: `RankEstimator`, `RankEstimate`, `run_validation()` |
| `src/neet_predictor/rank/__init__.py` | Package exports: `RankEstimator`, `RankEstimate`, `run_validation` |
| `tests/test_rank_estimator.py` | 47 tests across 12 test classes |
| `rank_cli_demo.py` | CLI demo with `--marks`, `--target-year`, `--category`, `--validate` |
| `PHASE1B_MARKS_TO_AIR_REPORT.md` | This report |

### Modified files

None. Phase 1B-A code was not modified. No changes to `config.py` or curated data files.

---

## 2. Algorithm Implemented

**Weighted Percentile-Space Interpolation with Proximity Decay and Min/Max Envelope**

### Step-by-step

1. **Load data:** Read `marks_rank_points.csv` for training years (2020–2024). 2021 has zero anchor points and is excluded automatically.

2. **Convert to percentile space:** For each year, convert `(marks, rank)` → `(marks, percentile)` where `percentile = rank / appeared_candidates`. This normalizes across years with different candidate counts.

3. **Build monotonic curves:** Per year, build piecewise-linear curves for `pct_best` (from `rank_min`), `pct_worst` (from `rank_max`), and `pct_mid` (average). Apply `_enforce_decreasing()` to guarantee monotonicity.

4. **Interpolate:** For input marks, interpolate each year's curve using `_interpolate_curve()` (linear interp, clamped at boundaries).

5. **Proximity weighting:** Weight each year's contribution by:
   ```
   effective_weight = base_weight × exp(−min_anchor_distance / 30.0)
   ```
   This downweights years whose nearest data anchor is far from the input marks. A year with anchors at marks [113, 147, 720] contributes negligibly for input marks=400.

6. **Significant-year filter:** Only years with `effective_weight ≥ 10%` of the best year's weight participate in the envelope (best/conservative) calculation.

7. **Combine:**
   - **Median AIR:** Weighted average of `pct_mid` across all years → convert to rank.
   - **Best-case AIR:** Minimum `pct_best` across *significant* years → convert to rank.
   - **Conservative AIR:** Maximum `pct_worst` across *significant* years → convert to rank.

8. **Scale to target year:** Multiply final percentile by target-year `appeared_candidates` to get AIR.

9. **Confidence assessment:** Based on number of significant years, minimum anchor distance, cross-year variance, and extrapolation status.

10. **Cutoff check:** If `category` is provided, compare marks against historical cutoffs and warn if below.

### Key constants

| Constant | Value | Rationale |
|----------|-------|-----------|
| `_PROXIMITY_DECAY` | 30.0 | Controls distance-based weight falloff; halves every ~21 marks |
| `_SIGNIFICANT_WEIGHT_FRACTION` | 0.10 | Year must have ≥10% of best year's weight to affect envelope |
| `YEAR_WEIGHTS` | {2024: 0.40, 2023: 0.25, 2022: 0.18, 2021: 0.10, 2020: 0.07} | Recency bias |

---

## 3. Data Used

| File | Rows | Usage |
|------|------|-------|
| `data/curated/marks_rank_points.csv` | 61 | Training anchors (40 for training, 21 for validation) |
| `data/curated/exam_years.csv` | 6 | Candidate counts for percentile scaling |
| `data/curated/category_cutoff_stats.csv` | 54 | Below-cutoff warnings only (not for AIR) |
| `data/curated/tie_breaking_rules.csv` | 11 | Referenced in explanations only |

### Per-year anchor counts (training)

| Year | Anchors | Marks range | Notes |
|------|---------|-------------|-------|
| 2020 | 3 | 113–720 | Very sparse (only 3 points) |
| 2021 | 0 | — | No data available; excluded automatically |
| 2022 | 7 | 117–715 | max_marks=715 (not 720) |
| 2023 | 15 | 101–720 | Good density |
| 2024 | 15 | 129–720 | Good density |

### Validation (held out)

| Year | Anchors | Marks range |
|------|---------|-------------|
| 2025 | 21 | 52–686 | max=686 (paper difficulty anomaly) |

---

## 4. Validation Results on 2025 Held-Out Data

### Summary metrics

| Metric | Value | Target |
|--------|-------|--------|
| Validation points | 21 | — |
| **Coverage rate** | **42.9%** (9/21) | ≥70% |
| Median absolute error | 53,058 | — |
| Mean absolute error | 66,193 | — |
| Within 10% band | 9.5% | — |
| Within 20% band | 19.0% | — |

### Gate status: **FAIL** (42.9% < 70%)

Coverage rate does not meet the 70% MVP target. This is documented transparently. The bands were **not** artificially widened; the 42.9% coverage uses principled min/max envelope across significant years.

### Per-point breakdown

| Marks | Actual rank range | Predicted range | Covered | Error |
|-------|-------------------|-----------------|---------|-------|
| 686 | 1–1 | 72–12,751 | MISS | — |
| 682 | 2–2 | 85–14,682 | MISS | — |
| 681 | 3–3 | 88–15,165 | MISS | — |
| 678 | 8–8 | 97–16,613 | MISS | — |
| 650 | 77–77 | 2,637–35,906 | MISS | — |
| 632 | 170–250 | 4,423–52,410 | MISS | — |
| 615 | 412–845 | 8,639–61,546 | MISS | — |
| 604 | 981–1,302 | 11,394–78,081 | MISS | — |
| 583 | 2,341–4,000 | 16,652–109,877 | MISS | — |
| 567 | 5,123–7,296 | 19,720–134,158 | MISS | — |
| 559 | 5,603–12,860 | 20,721–146,298 | MISS | — |
| 534 | 17,370–25,541 | 23,851–184,237 | OK | — |
| 520 | 27,698–36,843 | 36,963–205,184 | MISS | — |
| 498 | 36,843–76,510 | 56,038–237,259 | OK | — |
| 468 | 80,336–107,944 | 89,683–280,996 | OK | — |
| 418 | 146,846–206,050 | 145,880–375,149 | OK | — |
| 350 | 213,371–436,777 | 229,561–573,976 | OK | — |
| 242 | 577,330–684,232 | 420,473–965,525 | OK | — |
| 153 | 937,041–1,152,192 | 673,194–1,166,263 | OK | — |
| 86 | 1,391,647–1,717,603 | 1,020,420–1,883,383 | OK | — |
| 52 | 1,717,603–2,035,851 | 1,243,365–2,209,318 | OK | — |

**Pattern:** All 9 covered points are at marks ≤ 534. All 12 misses are at marks ≥ 520 where the 2025 paper-difficulty anomaly dominates.

---

## 5. Example Predictions

### `python rank_cli_demo.py --marks 620`

```
Marks:           620
Best-case AIR:   7,034
Median AIR:      35,126
Conservative AIR:61,546
Confidence:      high
Training years:  [2020, 2022, 2023, 2024]
Target year:     2025 (2,209,318 candidates)
```

### `python rank_cli_demo.py --marks 140 --category General`

```
Marks:           140
Best-case AIR:   721,459
Median AIR:      1,054,807
Conservative AIR:1,209,632
Confidence:      medium
WARNING: Marks 140 is below the General qualifying cutoff in year(s): [2020, 2024, 2025].
```

### `python rank_cli_demo.py --validate`

See Section 4 above.

---

## 6. Limitations

### 6.1. Paper difficulty variation (primary cause of low coverage)

The estimator assumes similar paper difficulty across years. In 2025, the highest score was 686/720 — a dramatic drop from previous years (715–720). This means:
- For marks ≥ 550: the same numerical marks corresponds to a **much better rank** in 2025 than in 2020–2024.
- The model systematically overestimates rank (predicts worse rank) for high marks in 2025.
- This is a **fundamental limitation** of any marks-based prediction without paper-difficulty knowledge.

### 6.2. Sparse anchor data

- 2020: Only 3 anchor points (113, 147, 720). Contributes minimally due to proximity weighting.
- 2021: Zero anchor points. Entirely excluded.
- Even the densest years (2023, 2024) have only 15 points spanning 0–720 marks.

### 6.3. Known source-quality issues

- Some marks_rank_points have `confidence: medium` (extracted from PDFs or approximate ranges).
- Data for 2022 has `max_marks=715` (not 720), suggesting possible exam variant differences.

### 6.4. Tie-breaking unpredictability

- Tie-breaking rules changed in 2025 (Physics first, not Biology first).
- Exact rank within a marks tier depends on subject-wise scores, which we cannot predict.

---

## 7. Test Coverage

**47 tests across 12 test classes, all passing.**

| # | Test class | Tests | What it covers |
|---|-----------|-------|---------------|
| 1 | TestMarksValidation | 5 | Input range [0, 720], negatives, floats |
| 2 | TestPercentileConversion | 3 | High/low marks → expected AIR direction |
| 3 | TestMonotonicity | 5 | `_enforce_decreasing`, curve monotonicity, sweep |
| 4 | TestInterpolation | 4 | Exact hits, midpoints, extrapolation clamping |
| 5 | TestWeightRenormalization | 4 | 2021 excluded, ≥3 years present, weights sum |
| 6 | TestPredictionSchema | 8 | All fields present, ordering, method string |
| 7 | TestConfidence | 3 | Valid labels, near-anchor → high, extremes → low |
| 8 | TestBelowCutoff | 5 | Warning present/absent by marks and category |
| 9 | TestValidation | 3 | `run_validation()` runs and returns valid metrics |
| 10 | TestNoValidationLeak | 3 | 2025 excluded from training, includable for testing |
| 11 | TestNoCategoryInfluence | 2 | Category does not change AIR numbers |
| 12 | TestNoExactRankClaim | 2 | Explanation disclaims exactness, best ≠ conservative |

### Full suite

```
173 passed in 12.90s
```

(65 Phase 1A + 61 Phase 1B-A + 47 Phase 1B-B)

---

## 8. What Would Improve Coverage

1. **Paper-difficulty normalization:** If we could estimate relative paper difficulty (e.g., using topper score as a proxy), we could scale marks before interpolation. This would likely bring coverage above 70%.

2. **More anchor data:** Denser marks→rank mappings (especially in the 500–700 range) would tighten bands.

3. **Percentile-rank tables:** NTA publishes full percentile→rank tables some years. Incorporating these would dramatically improve density.

4. **Score distribution modeling:** Fitting a parametric distribution (e.g., beta or mixture model) to the sparse anchors could smooth predictions.

These improvements are candidates for future phases.

---

## 9. Architecture Notes

- `RankEstimator` is stateless after `__init__`. It can be instantiated once and called many times.
- `run_validation()` creates a separate estimator with `use_validation_data=False` (correct) and tests against 2025 points.
- The estimator does NOT import or depend on the Phase 1B-A college predictor. Integration is deferred to Phase 1C.
- All data paths are derived from `config.py` constants.
