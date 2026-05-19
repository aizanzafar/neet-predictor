# Phase 1B-C Report: Rank Estimator Calibration / Paper-Difficulty Normalization

**Date:** 2025-07-14  
**Status:** COMPLETE — coverage improved 42.9% → 66.7%, all tests pass, no validation leakage

---

## 1. Summary

Phase 1B-B's estimator achieved 42.9% coverage on 2025 held-out data. All failures were at high marks (≥520), caused by the 2025 paper-difficulty anomaly (max score 686 vs historical 715–720).

Phase 1B-C adds **paper-difficulty normalization** — mapping query marks from the target year's scale to each training year's scale before curve interpolation. This improved coverage to **66.7%** without using any 2025 anchor data for training, without artificially widening bands, and while maintaining all existing guarantees (monotonicity, ordering, no category influence on AIR).

---

## 2. Before / After Validation Table

| Metric | NONE (baseline) | TOPPER_SCORE | AFFINE_TWO_POINT |
|--------|:-:|:-:|:-:|
| **Coverage rate** | **42.9%** (9/21) | **66.7%** (14/21) | **66.7%** (14/21) |
| High-marks coverage (≥550) | 0.0% (0/11) | 36.4% (4/11) | 36.4% (4/11) |
| Low/mid-marks coverage (<550) | 90.0% (9/10) | 100.0% (10/10) | 100.0% (10/10) |
| Median absolute error | 53,058 | 45,762 | 45,092 |
| Mean absolute error | 66,193 | 56,395 | 50,966 |
| Within 10% band | 9.5% | 4.8% | 9.5% |
| Within 20% band | 19.0% | 23.8% | 23.8% |
| Gate (≥70%) | FAIL | FAIL | FAIL |

**Key improvements:**
- +5 newly covered points (686, 682, 681, 678, 520)
- High-marks coverage: 0% → 36.4%
- Low/mid-marks coverage: 90% → 100%
- Mean absolute error reduced ~23% (affine)

---

## 3. Per-Point Comparison

| Marks | Actual rank | Baseline | Topper | Affine | Delta |
|------:|------------:|:--------:|:------:|:------:|:-----:|
| 686 | 1 | MISS | **OK** | **OK** | FIXED |
| 682 | 2 | MISS | **OK** | **OK** | FIXED |
| 681 | 3 | MISS | **OK** | **OK** | FIXED |
| 678 | 8 | MISS | **OK** | **OK** | FIXED |
| 650 | 77 | MISS | MISS | MISS | — |
| 632 | 170–250 | MISS | MISS | MISS | — |
| 615 | 412–845 | MISS | MISS | MISS | — |
| 604 | 981–1,302 | MISS | MISS | MISS | — |
| 583 | 2,341–4,000 | MISS | MISS | MISS | — |
| 567 | 5,123–7,296 | MISS | MISS | MISS | — |
| 559 | 5,603–12,860 | MISS | MISS | MISS | — |
| 534 | 17,370–25,541 | OK | OK | OK | — |
| 520 | 27,698–36,843 | MISS | **OK** | **OK** | FIXED |
| 498 | 36,843–76,510 | OK | OK | OK | — |
| 468 | 80,336–107,944 | OK | OK | OK | — |
| 418 | 146,846–206,050 | OK | OK | OK | — |
| 350 | 213,371–436,777 | OK | OK | OK | — |
| 242 | 577,330–684,232 | OK | OK | OK | — |
| 153 | 937,041–1,152,192 | OK | OK | OK | — |
| 86 | 1,391,647–1,717,603 | OK | OK | OK | — |
| 52 | 1,717,603–2,035,851 | OK | OK | OK | — |

---

## 4. Normalization Strategies

### 4.1. Topper-Score Normalization (`TOPPER_SCORE`)

Single-point linear scaling using the highest achieved score:

```
normalized = marks × (training_highest / target_highest)
```

For 2025 (highest=686) → 2024 (highest=720):
- marks=686 → 720 (exact topper match)
- marks=650 → 682.2
- marks=350 → 367.1
- marks=0 → 0

**Strengths:** Simple, interpretable. Perfectly aligns topper scores. Zero marks stays zero.

**Weakness:** Only one anchor point. Assumes linear scaling across entire range.

### 4.2. Affine Two-Point Normalization (`AFFINE_TWO_POINT`)

Uses both the topper score and the UR qualifying cutoff:

```
normalized = train_cutoff + (marks − target_cutoff) × (train_highest − train_cutoff) / (target_highest − target_cutoff)
```

For 2025 (highest=686, cutoff_ur=144) → 2024 (highest=720, cutoff_ur=164):
- marks=686 → 720.0 (topper aligned)
- marks=144 → 164.0 (cutoff aligned)
- marks=650 → 683.1
- marks=350 → 375.3
- marks=0 → 16.3

**Strengths:** Anchors both ends of the "meaningful" marks range. Better tracks years where cutoff shifted substantially.

**Weakness:** Below-cutoff marks can map to unexpected values (0 → 16.3). Slightly more complex.

### 4.3. Strategy Comparison

Both strategies produce **identical coverage** (14/21) because they give very similar normalized values in the critical high-marks range. The affine strategy has a small edge in error metrics (mean abs error 50,966 vs 56,395; within-10% 9.5% vs 4.8%) because it better handles the mid-range where cutoff differences matter.

**Recommendation:** Use `AFFINE_TWO_POINT` for the best overall error metrics, or `TOPPER_SCORE` for simplicity.

---

## 5. Why 7 Points Still Miss

The 7 remaining misses are all marks 559–650, corresponding to ranks 77–12,860 in 2025.

**Root cause: non-linear score distribution compression.** When a paper is harder, not only do all scores drop, but the top of the distribution compresses disproportionately. Marks 650 in 2025 (94.8% of max) corresponds to rank 77, but the equivalent marks in training years (682 after normalization) corresponds to rank ~84–4406 depending on year.

Linear normalization correctly handles the first-order effect (overall score shift) but cannot capture the second-order effect (shape change in the top percentile). This would require either:

1. **Score-distribution modeling** — fitting a parametric distribution (e.g., beta mixture) to each year's anchors and warping between distributions
2. **Denser top-of-range anchor data** — finer granularity in the 650–720 marks range for training years
3. **Percentile-quantile matching** — if full percentile tables become available

The closest miss is marks=650: predicted best=84, actual=77 — a gap of just 7 ranks (8.3%). This single point separates 66.7% from 71.4%.

---

## 6. Files Created / Modified

### New files

| File | Purpose |
|------|---------|
| `src/neet_predictor/rank/calibration.py` | `NormalizationMode` enum, `normalize_marks_topper()`, `normalize_marks_affine()`, `normalize_marks()` dispatcher |
| `tests/test_rank_calibration.py` | 39 tests: unit tests for normalization functions + integration + coverage improvement verification |
| `PHASE1B_C_RANK_CALIBRATION_REPORT.md` | This report |

### Modified files

| File | Changes |
|------|---------|
| `src/neet_predictor/rank/estimator.py` | Added `normalization` param to `RankEstimator.__init__`; per-year marks normalization in `estimate()` loop; proximity distance computed on normalized marks; updated explanation text; updated method string; `run_validation()` accepts normalization param; added `compare_normalization_strategies()` |
| `src/neet_predictor/rank/__init__.py` | Exports `NormalizationMode`, `YearNormParams`, `compare_normalization_strategies` |

### NOT modified

- College predictor (Phase 1B-A) — unchanged
- Config — unchanged
- Curated data files — unchanged
- Phase 1B-B tests — unchanged, all still pass

---

## 7. Test Coverage

**39 new tests across 9 test classes, all passing.**

| # | Test class | Tests | What it covers |
|---|-----------|-------|---------------|
| 1 | TestTopperNormalization | 9 | Identity, scaling, clamping, monotonicity, degenerate cases |
| 2 | TestAffineNormalization | 9 | Identity, top/cutoff mapping, scaling, clamping, monotonicity, 2022 variant |
| 3 | TestNormalizeModeDispatch | 3 | NONE/TOPPER/AFFINE dispatch correctness |
| 4 | TestEstimatorWithNormalization | 5 | Valid results, method string, explanation text |
| 5 | TestMonotonicityWithNormalization | 2 | Higher marks → lower AIR for both strategies |
| 6 | TestNoValidationLeakageWithNormalization | 4 | 2025 excluded from curves, metadata usage is not leakage |
| 7 | TestNormalizationImprovesCoverage | 3 | Coverage > baseline for both strategies; high-marks improvement |
| 8 | TestCategoryUnaffectedByNormalization | 2 | Category does not change AIR with normalization |
| 9 | TestCompareStrategies | 2 | Comparison function returns all modes and expected metrics |

### Full suite

```
212 passed in 13.50s
```

(65 Phase 1A + 61 Phase 1B-A + 47 Phase 1B-B + 39 Phase 1B-C)

---

## 8. No Validation Leakage

The normalization uses only **exam metadata** from the target year:
- `highest_marks` (686 for 2025) — published by NTA with results
- `cutoff_ur` (144 for 2025) — published by NTA with results

These are NOT marks-to-rank anchor data. They do not reveal individual student ranks. They are available to any student at result time. The 2025 marks_rank_points are never used for training.

---

## 9. Acceptance Gate Assessment

| Criterion | Status |
|-----------|--------|
| Coverage should improve toward ≥70% | 42.9% → 66.7% (+23.8pp) — significant improvement but below 70% |
| High-mark misses should reduce | 11/11 → 7/11 — 4 high-marks points fixed |
| No validation leakage | ✓ 2025 excluded from training; only exam metadata used |
| All tests pass | ✓ 212/212 |
| Explanations mention paper-difficulty adjustment | ✓ When normalization is active |
| Monotonicity preserved | ✓ Tested for both strategies |
| No artificial band widening | ✓ Same envelope algorithm; bands actually tightened for some points |

**Coverage gate (≥70%): NOT MET.** The gap is 1 point (15/21 = 71.4% would pass). marks=650 misses by just 7 ranks (predicted best=84, actual=77). Closing this gap requires either denser training data or distribution-shape modeling, not further normalization.

---

## 10. Usage

```python
from neet_predictor.rank import RankEstimator, NormalizationMode

# With paper-difficulty normalization
est = RankEstimator(normalization=NormalizationMode.TOPPER_SCORE)
result = est.estimate(620, target_year=2025)

# Or affine two-point
est = RankEstimator(normalization=NormalizationMode.AFFINE_TWO_POINT)
result = est.estimate(620, target_year=2025)

# Compare all strategies
from neet_predictor.rank import compare_normalization_strategies
comparison = compare_normalization_strategies()
```

CLI:
```bash
python rank_cli_demo.py --marks 620 --target-year 2025 --normalization topper_score
python rank_cli_demo.py --validate --normalization affine_two_point
python rank_cli_demo.py --compare
```
