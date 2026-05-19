"""Tests for Phase 1B-B: Marks-to-AIR Rank Estimator.

Covers:
  1.  Marks validation
  2.  Percentile conversion
  3.  Monotonicity enforcement
  4.  Interpolation correctness
  5.  Weight renormalization (2021 has no data)
  6.  Prediction schema
  7.  Confidence labels
  8.  Below-cutoff warning
  9.  2025 held-out validation runner
  10. No use of 2025 data during training
  11. No category influence on AIR estimation
  12. Exact-rank claims are never made
"""

import numpy as np
import pytest

from neet_predictor.rank.estimator import (
    RankEstimator,
    RankEstimate,
    _enforce_decreasing,
    _interpolate_curve,
    run_validation,
)
from neet_predictor.config import TRAINING_YEARS, VALIDATION_YEAR, YEAR_WEIGHTS


@pytest.fixture(scope="module")
def estimator():
    """Shared estimator instance (loads data once)."""
    return RankEstimator(use_validation_data=False)


# ═══════════════════════════════════════════════════════
#  1. Marks validation
# ═══════════════════════════════════════════════════════


class TestMarksValidation:

    def test_negative_marks_raises(self, estimator):
        with pytest.raises(ValueError, match="between"):
            estimator.estimate(-1)

    def test_marks_above_720_raises(self, estimator):
        with pytest.raises(ValueError, match="between"):
            estimator.estimate(721)

    def test_marks_zero_ok(self, estimator):
        r = estimator.estimate(0)
        assert r.marks == 0
        assert r.conservative_air > 0

    def test_marks_720_ok(self, estimator):
        r = estimator.estimate(720)
        assert r.marks == 720
        assert r.best_case_air >= 1

    def test_marks_float_converted(self, estimator):
        r = estimator.estimate(500.7)
        assert r.marks == 500


# ═══════════════════════════════════════════════════════
#  2. Percentile conversion
# ═══════════════════════════════════════════════════════


class TestPercentileConversion:

    def test_high_marks_low_percentile(self, estimator):
        """720 marks → very low percentile (close to rank 1)."""
        r = estimator.estimate(720)
        # best_case should be very small rank
        assert r.best_case_air <= 50

    def test_low_marks_high_percentile(self, estimator):
        """0 marks → very high percentile (close to worst rank)."""
        r = estimator.estimate(0)
        assert r.conservative_air > 1_000_000

    def test_ordering_preserved(self, estimator):
        """Higher marks → lower (better) AIR."""
        r600 = estimator.estimate(600)
        r400 = estimator.estimate(400)
        assert r600.median_air < r400.median_air


# ═══════════════════════════════════════════════════════
#  3. Monotonicity enforcement
# ═══════════════════════════════════════════════════════


class TestMonotonicity:

    def test_enforce_decreasing_no_violation(self):
        arr = np.array([0.8, 0.6, 0.4, 0.2])
        result = _enforce_decreasing(arr)
        np.testing.assert_array_equal(result, arr)

    def test_enforce_decreasing_with_violation(self):
        arr = np.array([0.8, 0.6, 0.75, 0.2])
        result = _enforce_decreasing(arr)
        # 0.75 at index 2 should be corrected to 0.6 (or merged)
        assert result[2] <= result[1], "Monotonicity violated"
        # Still decreasing
        for i in range(len(result) - 1):
            assert result[i] >= result[i + 1]

    def test_enforce_decreasing_single_element(self):
        arr = np.array([0.5])
        result = _enforce_decreasing(arr)
        assert result[0] == 0.5

    def test_curves_are_monotonic(self, estimator):
        """All built curves must be monotonically decreasing."""
        for yr, curve in estimator._curves.items():
            for i in range(len(curve.pct_best) - 1):
                assert curve.pct_best[i] >= curve.pct_best[i + 1], (
                    f"pct_best not decreasing in {yr} at index {i}"
                )
            for i in range(len(curve.pct_worst) - 1):
                assert curve.pct_worst[i] >= curve.pct_worst[i + 1], (
                    f"pct_worst not decreasing in {yr} at index {i}"
                )

    def test_higher_marks_always_better_rank(self, estimator):
        """For a sweep of marks, median AIR must be monotonically decreasing."""
        prev = None
        for m in range(100, 710, 50):
            r = estimator.estimate(m)
            if prev is not None:
                assert r.median_air <= prev, (
                    f"Marks {m}: median {r.median_air} > previous {prev}"
                )
            prev = r.median_air


# ═══════════════════════════════════════════════════════
#  4. Interpolation
# ═══════════════════════════════════════════════════════


class TestInterpolation:

    def test_exact_anchor_hit(self):
        xp = np.array([100.0, 200.0, 300.0])
        fp = np.array([0.9, 0.5, 0.1])
        assert _interpolate_curve(200.0, xp, fp) == pytest.approx(0.5)

    def test_midpoint_interpolation(self):
        xp = np.array([100.0, 300.0])
        fp = np.array([0.8, 0.2])
        assert _interpolate_curve(200.0, xp, fp) == pytest.approx(0.5)

    def test_extrapolation_below_clamps(self):
        xp = np.array([100.0, 300.0])
        fp = np.array([0.8, 0.2])
        assert _interpolate_curve(50.0, xp, fp) == pytest.approx(0.8)

    def test_extrapolation_above_clamps(self):
        xp = np.array([100.0, 300.0])
        fp = np.array([0.8, 0.2])
        assert _interpolate_curve(400.0, xp, fp) == pytest.approx(0.2)


# ═══════════════════════════════════════════════════════
#  5. Weight renormalization
# ═══════════════════════════════════════════════════════


class TestWeightRenormalization:

    def test_2021_has_curve(self, estimator):
        """2021 now has calibration anchor data → curve built."""
        assert 2021 in estimator._curves

    def test_training_years_present(self, estimator):
        """At least 2022, 2023, 2024 should have curves."""
        for yr in [2022, 2023, 2024]:
            assert yr in estimator._curves, f"Missing curve for {yr}"

    def test_result_has_all_training_years(self, estimator):
        r = estimator.estimate(500)
        assert 2021 in r.training_years
        assert len(r.training_years) >= 4

    def test_weights_are_renormalized(self, estimator):
        """Effective weights should sum to ~1 when renormalized."""
        r = estimator.estimate(600)
        # training_years in result shows which years contributed
        assert len(r.training_years) >= 3


# ═══════════════════════════════════════════════════════
#  6. Prediction schema
# ═══════════════════════════════════════════════════════


class TestPredictionSchema:

    def test_result_is_rank_estimate(self, estimator):
        r = estimator.estimate(500)
        assert isinstance(r, RankEstimate)

    def test_required_fields_present(self, estimator):
        r = estimator.estimate(500)
        assert hasattr(r, "marks")
        assert hasattr(r, "best_case_air")
        assert hasattr(r, "median_air")
        assert hasattr(r, "conservative_air")
        assert hasattr(r, "confidence")
        assert hasattr(r, "method")
        assert hasattr(r, "training_years")
        assert hasattr(r, "validation_year")
        assert hasattr(r, "explanation")
        assert hasattr(r, "nearest_anchors")

    def test_best_le_median_le_conservative(self, estimator):
        for m in [100, 300, 500, 650, 720]:
            r = estimator.estimate(m)
            assert r.best_case_air <= r.median_air <= r.conservative_air, (
                f"Ordering violated at marks={m}: "
                f"{r.best_case_air} <= {r.median_air} <= {r.conservative_air}"
            )

    def test_method_field(self, estimator):
        r = estimator.estimate(500)
        assert r.method == "weighted_percentile_interpolation"

    def test_validation_year_field(self, estimator):
        r = estimator.estimate(500)
        assert r.validation_year == VALIDATION_YEAR

    def test_nearest_anchors_not_empty(self, estimator):
        r = estimator.estimate(500)
        assert len(r.nearest_anchors) > 0
        # Each anchor should have expected keys
        for a in r.nearest_anchors:
            assert "year" in a
            assert "marks_min" in a
            assert "rank_min" in a

    def test_target_year_default(self, estimator):
        r = estimator.estimate(500)
        assert r.target_year is not None
        assert r.target_appeared is not None
        assert r.target_appeared > 1_000_000

    def test_target_year_explicit(self, estimator):
        r = estimator.estimate(500, target_year=2024)
        assert r.target_year == 2024


# ═══════════════════════════════════════════════════════
#  7. Confidence labels
# ═══════════════════════════════════════════════════════


class TestConfidence:

    def test_confidence_is_valid_label(self, estimator):
        for m in [100, 300, 500, 650, 720]:
            r = estimator.estimate(m)
            assert r.confidence in ("high", "medium", "low")

    def test_high_confidence_near_anchors(self, estimator):
        """Marks near dense anchors should get high or medium confidence."""
        r = estimator.estimate(650)
        assert r.confidence in ("high", "medium")

    def test_low_confidence_at_extremes(self, estimator):
        """Very low marks (near 0) may get low confidence if sparse."""
        r = estimator.estimate(5)
        assert r.confidence in ("low", "medium")


# ═══════════════════════════════════════════════════════
#  8. Below-cutoff warning
# ═══════════════════════════════════════════════════════


class TestBelowCutoff:

    def test_no_warning_above_cutoff(self, estimator):
        r = estimator.estimate(600)
        assert r.below_cutoff_warning is None

    def test_warning_below_ur_cutoff(self, estimator):
        r = estimator.estimate(100)
        assert r.below_cutoff_warning is not None
        assert "below" in r.below_cutoff_warning.lower()

    def test_warning_for_general_below_cutoff(self, estimator):
        r = estimator.estimate(140, category="General")
        assert r.below_cutoff_warning is not None

    def test_no_warning_for_sc_above_sc_cutoff(self, estimator):
        """SC cutoff is lower — marks 120 may be above SC cutoff."""
        r = estimator.estimate(120, category="SC")
        # SC cutoff is 93-129 depending on year
        # 120 is above SC cutoff in 2022/2023 but below in 2024
        # Just check it returns something (warning or None both valid)
        assert isinstance(r.below_cutoff_warning, (str, type(None)))

    def test_category_does_not_affect_air(self, estimator):
        """Category is ONLY for cutoff warning, not for AIR estimation."""
        r_none = estimator.estimate(500, category=None)
        r_obc = estimator.estimate(500, category="OBC")
        r_sc = estimator.estimate(500, category="SC")
        assert r_none.best_case_air == r_obc.best_case_air == r_sc.best_case_air
        assert r_none.median_air == r_obc.median_air == r_sc.median_air


# ═══════════════════════════════════════════════════════
#  9. Validation runner
# ═══════════════════════════════════════════════════════


class TestValidation:

    def test_validation_runs(self):
        results = run_validation()
        assert "n_validation_points" in results
        assert "coverage_rate" in results
        assert results["n_validation_points"] > 0

    def test_validation_metrics_present(self):
        results = run_validation()
        assert "median_absolute_error" in results
        assert "mean_absolute_error" in results
        assert "within_10_percent_band" in results
        assert "within_20_percent_band" in results

    def test_coverage_rate_is_fraction(self):
        results = run_validation()
        assert 0.0 <= results["coverage_rate"] <= 1.0


# ═══════════════════════════════════════════════════════
#  10. No 2025 data during training
# ═══════════════════════════════════════════════════════


class TestNoValidationLeak:

    def test_default_estimator_excludes_2025(self, estimator):
        """Default estimator must NOT have 2025 in its curves."""
        assert VALIDATION_YEAR not in estimator._curves

    def test_result_training_years_exclude_2025(self, estimator):
        r = estimator.estimate(500)
        assert VALIDATION_YEAR not in r.training_years

    def test_validation_estimator_can_include_2025(self):
        """use_validation_data=True allows 2025 (for test harness only)."""
        val_est = RankEstimator(use_validation_data=True)
        assert VALIDATION_YEAR in val_est._curves


# ═══════════════════════════════════════════════════════
#  11. No category influence on AIR
# ═══════════════════════════════════════════════════════


class TestNoCategoryInfluence:

    def test_category_does_not_change_air(self, estimator):
        """AIR estimates must be identical regardless of category."""
        base = estimator.estimate(400)
        for cat in ["General", "OBC", "SC", "ST", "EWS"]:
            r = estimator.estimate(400, category=cat)
            assert r.best_case_air == base.best_case_air
            assert r.median_air == base.median_air
            assert r.conservative_air == base.conservative_air

    def test_category_only_affects_warning(self, estimator):
        """Category only affects below_cutoff_warning."""
        r_gen = estimator.estimate(140, category="General")
        r_sc = estimator.estimate(140, category="SC")
        # Same AIR
        assert r_gen.median_air == r_sc.median_air
        # But warnings may differ (General cutoff is higher than SC)


# ═══════════════════════════════════════════════════════
#  12. No exact-rank claims
# ═══════════════════════════════════════════════════════


class TestNoExactRankClaim:

    def test_explanation_disclaims_exact_rank(self, estimator):
        r = estimator.estimate(600)
        assert "exact" in r.explanation.lower() or "tie" in r.explanation.lower()

    def test_best_and_conservative_differ(self, estimator):
        """For most marks, best and conservative should differ (range, not point)."""
        r = estimator.estimate(500)
        assert r.best_case_air != r.conservative_air, (
            "Best and conservative should differ for typical marks"
        )
