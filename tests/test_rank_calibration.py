"""Tests for Phase 1B-C: Rank Estimator Calibration / Paper-Difficulty Normalization."""

import pytest

from neet_predictor.rank.calibration import (
    NormalizationMode,
    YearNormParams,
    normalize_marks,
    normalize_marks_topper,
    normalize_marks_affine,
    normalize_marks_piecewise_affine,
)
from neet_predictor.rank.estimator import (
    RankEstimator,
    RankEstimate,
    run_validation,
    compare_normalization_strategies,
)
from neet_predictor.config import VALIDATION_YEAR, MAX_MARKS


# ═══════════════════════════════════════════════════════
#  Normalization function unit tests
# ═══════════════════════════════════════════════════════


class TestTopperNormalization:

    def test_identity_when_same_highest(self):
        """No scaling when target and training have same highest."""
        assert normalize_marks_topper(600, 720, 720) == pytest.approx(600.0)

    def test_upscale_harder_paper(self):
        """Target highest < training highest → marks scaled UP."""
        # 600/686 ≈ 87.5% of max → should map to ~629.7 on 720 scale
        result = normalize_marks_topper(600, 686, 720)
        assert result == pytest.approx(600 * 720 / 686, abs=0.1)
        assert result > 600

    def test_downscale_easier_paper(self):
        """Target highest > training highest → marks scaled DOWN."""
        result = normalize_marks_topper(600, 720, 686)
        assert result < 600

    def test_top_score_maps_to_top(self):
        """Target topper score maps exactly to training topper score."""
        result = normalize_marks_topper(686, 686, 720)
        assert result == pytest.approx(720.0, abs=0.1)

    def test_zero_maps_to_zero(self):
        result = normalize_marks_topper(0, 686, 720)
        assert result == pytest.approx(0.0)

    def test_clamp_upper(self):
        """Cannot exceed MAX_MARKS even if ratio would push above."""
        result = normalize_marks_topper(700, 686, 720)
        assert result <= MAX_MARKS

    def test_clamp_lower(self):
        result = normalize_marks_topper(0, 720, 720)
        assert result >= 0

    def test_monotonic(self):
        """Higher input marks → higher normalized marks."""
        prev = 0.0
        for m in range(0, 690, 10):
            n = normalize_marks_topper(m, 686, 720)
            assert n >= prev, f"Non-monotonic at marks={m}"
            prev = n

    def test_degenerate_zero_highest(self):
        """Zero highest returns marks unchanged."""
        assert normalize_marks_topper(500, 0, 720) == 500.0
        assert normalize_marks_topper(500, 720, 0) == 500.0


class TestAffineNormalization:

    def test_identity_when_same_params(self):
        """No shift when target and training have identical params."""
        result = normalize_marks_affine(500, 720, 147, 720, 147)
        assert result == pytest.approx(500.0)

    def test_top_score_maps_to_top(self):
        """Target topper maps to training topper."""
        result = normalize_marks_affine(686, 686, 144, 720, 164)
        assert result == pytest.approx(720.0, abs=0.1)

    def test_cutoff_maps_to_cutoff(self):
        """Target cutoff maps to training cutoff."""
        result = normalize_marks_affine(144, 686, 144, 720, 164)
        assert result == pytest.approx(164.0, abs=0.1)

    def test_upscale_harder_paper(self):
        """Harder target paper → marks scaled up."""
        result = normalize_marks_affine(600, 686, 144, 720, 164)
        assert result > 600

    def test_clamp_upper(self):
        result = normalize_marks_affine(700, 686, 144, 720, 164)
        assert result <= MAX_MARKS

    def test_clamp_lower(self):
        """Below-cutoff marks can still map to non-negative."""
        result = normalize_marks_affine(0, 686, 144, 720, 164)
        assert result >= 0

    def test_monotonic(self):
        """Higher input → higher output."""
        prev = -1.0
        for m in range(0, 690, 10):
            n = normalize_marks_affine(m, 686, 144, 720, 164)
            assert n >= prev, f"Non-monotonic at marks={m}"
            prev = n

    def test_degenerate_zero_range(self):
        """Zero range returns marks unchanged."""
        result = normalize_marks_affine(500, 686, 686, 720, 164)
        assert result == 500.0

    def test_2022_lower_highest(self):
        """2022 had highest_marks=715 (not 720)."""
        result = normalize_marks_affine(600, 686, 144, 715, 117)
        expected = 117 + (600 - 144) * (715 - 117) / (686 - 144)
        assert result == pytest.approx(expected, abs=0.1)


class TestNormalizeModeDispatch:

    _target = YearNormParams(2025, 686, 144)
    _train = YearNormParams(2024, 720, 164)

    def test_none_returns_unchanged(self):
        result = normalize_marks(600, NormalizationMode.NONE, self._target, self._train)
        assert result == pytest.approx(600.0)

    def test_topper_dispatches(self):
        result = normalize_marks(
            600, NormalizationMode.TOPPER_SCORE, self._target, self._train
        )
        expected = normalize_marks_topper(600, 686, 720)
        assert result == pytest.approx(expected)

    def test_affine_dispatches(self):
        result = normalize_marks(
            600, NormalizationMode.AFFINE_TWO_POINT, self._target, self._train
        )
        expected = normalize_marks_affine(600, 686, 144, 720, 164)
        assert result == pytest.approx(expected)


# ═══════════════════════════════════════════════════════
#  Estimator integration tests (with normalization)
# ═══════════════════════════════════════════════════════


@pytest.fixture(scope="module")
def est_topper():
    return RankEstimator(normalization=NormalizationMode.TOPPER_SCORE)


@pytest.fixture(scope="module")
def est_affine():
    return RankEstimator(normalization=NormalizationMode.AFFINE_TWO_POINT)


@pytest.fixture(scope="module")
def est_none():
    return RankEstimator(normalization=NormalizationMode.NONE)


class TestEstimatorWithNormalization:

    def test_topper_returns_valid_result(self, est_topper):
        r = est_topper.estimate(600, target_year=2025)
        assert isinstance(r, RankEstimate)
        assert r.best_case_air <= r.median_air <= r.conservative_air

    def test_affine_returns_valid_result(self, est_affine):
        r = est_affine.estimate(600, target_year=2025)
        assert isinstance(r, RankEstimate)
        assert r.best_case_air <= r.median_air <= r.conservative_air

    def test_method_contains_strategy_name(self, est_topper, est_affine, est_none):
        r_t = est_topper.estimate(500)
        r_a = est_affine.estimate(500)
        r_n = est_none.estimate(500)

        assert "topper_score" in r_t.method
        assert "affine_two_point" in r_a.method
        assert r_n.method == "weighted_percentile_interpolation"

    def test_explanation_mentions_adjustment(self, est_topper):
        r = est_topper.estimate(600, target_year=2025)
        assert "paper-difficulty" in r.explanation.lower()

    def test_explanation_no_adjustment_for_none(self, est_none):
        r = est_none.estimate(600, target_year=2025)
        assert "paper-difficulty" not in r.explanation.lower()


class TestMonotonicityWithNormalization:

    def test_topper_monotonic(self, est_topper):
        """Higher marks → lower (better) median AIR even with normalization."""
        prev = None
        for m in range(100, 690, 50):
            r = est_topper.estimate(m, target_year=2025)
            if prev is not None:
                assert r.median_air <= prev, (
                    f"Marks {m}: median {r.median_air} > previous {prev}"
                )
            prev = r.median_air

    def test_affine_monotonic(self, est_affine):
        prev = None
        for m in range(100, 690, 50):
            r = est_affine.estimate(m, target_year=2025)
            if prev is not None:
                assert r.median_air <= prev, (
                    f"Marks {m}: median {r.median_air} > previous {prev}"
                )
            prev = r.median_air


class TestNoValidationLeakageWithNormalization:

    def test_topper_excludes_2025_from_curves(self, est_topper):
        assert VALIDATION_YEAR not in est_topper._curves

    def test_affine_excludes_2025_from_curves(self, est_affine):
        assert VALIDATION_YEAR not in est_affine._curves

    def test_topper_result_excludes_2025_training(self, est_topper):
        r = est_topper.estimate(500)
        assert VALIDATION_YEAR not in r.training_years

    def test_normalization_uses_target_metadata_not_anchors(self, est_topper):
        """Using target-year highest_marks and cutoff is NOT training leakage.

        These are publicly available exam metadata, not marks-to-rank anchors.
        """
        r = est_topper.estimate(600, target_year=2025)
        assert r.target_year == 2025
        # The normalization uses highest_marks=686, which is exam metadata
        assert "paper-difficulty" in r.explanation.lower()


class TestNormalizationImprovesCoverage:
    """Compare baseline vs. normalized validation to verify improvement."""

    def test_topper_coverage_improves(self):
        base = run_validation(normalization=NormalizationMode.NONE)
        topper = run_validation(normalization=NormalizationMode.TOPPER_SCORE)
        assert topper["coverage_rate"] >= base["coverage_rate"], (
            f"Topper ({topper['coverage_rate']:.1%}) should be at least as good as "
            f"baseline ({base['coverage_rate']:.1%})"
        )

    def test_affine_coverage_improves(self):
        base = run_validation(normalization=NormalizationMode.NONE)
        affine = run_validation(normalization=NormalizationMode.AFFINE_TWO_POINT)
        assert affine["coverage_rate"] >= base["coverage_rate"], (
            f"Affine ({affine['coverage_rate']:.1%}) should be at least as good as "
            f"baseline ({base['coverage_rate']:.1%})"
        )

    def test_topper_high_marks_coverage_improves(self):
        """High marks (≥550) should see at least as good coverage."""
        base = run_validation(normalization=NormalizationMode.NONE)
        topper = run_validation(normalization=NormalizationMode.TOPPER_SCORE)
        base_high = [r for r in base["results"] if r["marks"] >= 550]
        topper_high = [r for r in topper["results"] if r["marks"] >= 550]
        b_cov = sum(1 for r in base_high if r["covered"]) / len(base_high)
        t_cov = sum(1 for r in topper_high if r["covered"]) / len(topper_high)
        assert t_cov >= b_cov


class TestCategoryUnaffectedByNormalization:

    def test_category_does_not_change_air_with_topper(self, est_topper):
        r_none = est_topper.estimate(500, category=None)
        r_obc = est_topper.estimate(500, category="OBC")
        assert r_none.median_air == r_obc.median_air

    def test_category_does_not_change_air_with_affine(self, est_affine):
        r_none = est_affine.estimate(500, category=None)
        r_sc = est_affine.estimate(500, category="SC")
        assert r_none.median_air == r_sc.median_air


class TestCompareStrategies:

    def test_compare_returns_all_modes(self):
        comp = compare_normalization_strategies()
        assert "none" in comp
        assert "topper_score" in comp
        assert "affine_two_point" in comp

    def test_compare_has_expected_metrics(self):
        comp = compare_normalization_strategies()
        for mode, result in comp.items():
            assert "coverage_rate" in result
            assert "high_marks_coverage" in result
            assert "low_mid_marks_coverage" in result
            assert "n_validation_points" in result


# ═══════════════════════════════════════════════════════
#  Phase 1B-D: Piecewise Affine & Acceptance Tests
# ═══════════════════════════════════════════════════════


class TestPiecewiseAffineUnit:
    """Unit tests for normalize_marks_piecewise_affine."""

    def _pw(self, marks, src, tgt):
        return normalize_marks_piecewise_affine(
            marks, src.highest_marks, src.cutoff_ur,
            tgt.highest_marks, tgt.cutoff_ur,
            target_toppers=src.toppers_at_highest,
            target_appeared=src.appeared,
            training_toppers=tgt.toppers_at_highest,
            training_appeared=tgt.appeared,
        )

    def test_identity_same_params(self):
        """No change when target and training have identical params."""
        p = YearNormParams(year=2024, highest_marks=720, cutoff_ur=164,
                           toppers_at_highest=61, appeared=2_333_297)
        result = self._pw(600, p, p)
        assert result == pytest.approx(600.0, abs=1.0)

    def test_low_marks_use_affine(self):
        """Below top band, piecewise should behave like affine."""
        src = YearNormParams(year=2025, highest_marks=686, cutoff_ur=144,
                             toppers_at_highest=1, appeared=2_209_318)
        tgt = YearNormParams(year=2024, highest_marks=720, cutoff_ur=164,
                             toppers_at_highest=61, appeared=2_333_297)
        pw = self._pw(300, src, tgt)
        aff = normalize_marks_affine(300, src.highest_marks, src.cutoff_ur,
                                     tgt.highest_marks, tgt.cutoff_ur)
        assert pw == pytest.approx(aff, abs=0.1)

    def test_top_band_compressed_vs_affine(self):
        """In the top band, piecewise result should differ from plain affine."""
        src = YearNormParams(year=2025, highest_marks=686, cutoff_ur=144,
                             toppers_at_highest=1, appeared=2_209_318)
        tgt = YearNormParams(year=2024, highest_marks=720, cutoff_ur=164,
                             toppers_at_highest=61, appeared=2_333_297)
        pw = self._pw(680, src, tgt)
        aff = normalize_marks_affine(680, src.highest_marks, src.cutoff_ur,
                                     tgt.highest_marks, tgt.cutoff_ur)
        assert pw != pytest.approx(aff, abs=0.01)

    def test_monotonic(self):
        """Higher marks → higher normalized marks."""
        src = YearNormParams(year=2025, highest_marks=686, cutoff_ur=144,
                             toppers_at_highest=1, appeared=2_209_318)
        tgt = YearNormParams(year=2024, highest_marks=720, cutoff_ur=164,
                             toppers_at_highest=61, appeared=2_333_297)
        prev = 0.0
        for m in range(100, 686, 10):
            r = self._pw(m, src, tgt)
            assert r >= prev, f"Non-monotonic at marks={m}: {r} < {prev}"
            prev = r

    def test_zero_below_cutoff_stays_low(self):
        src = YearNormParams(year=2025, highest_marks=686, cutoff_ur=144,
                             toppers_at_highest=1, appeared=2_209_318)
        tgt = YearNormParams(year=2024, highest_marks=720, cutoff_ur=164,
                             toppers_at_highest=61, appeared=2_333_297)
        # Affine anchors at cutoff, so 0 doesn't map to exactly 0
        assert self._pw(0, src, tgt) < 50

    def test_dispatch_via_normalize_marks(self):
        """normalize_marks dispatches correctly for PIECEWISE_AFFINE."""
        src = YearNormParams(year=2025, highest_marks=686, cutoff_ur=144,
                             toppers_at_highest=1, appeared=2_209_318)
        tgt = YearNormParams(year=2024, highest_marks=720, cutoff_ur=164,
                             toppers_at_highest=61, appeared=2_333_297)
        result = normalize_marks(500, NormalizationMode.PIECEWISE_AFFINE, src, tgt)
        direct = self._pw(500, src, tgt)
        assert result == pytest.approx(direct)


class TestPiecewiseAffineIntegration:
    """Integration tests: piecewise affine through the estimator."""

    @pytest.fixture
    def est_piecewise(self):
        return RankEstimator(normalization=NormalizationMode.PIECEWISE_AFFINE)

    def test_no_validation_leak(self, est_piecewise):
        assert VALIDATION_YEAR not in est_piecewise._curves

    def test_monotonic_air(self, est_piecewise):
        prev = None
        for m in range(100, 690, 50):
            r = est_piecewise.estimate(m, target_year=2025)
            if prev is not None:
                assert r.median_air <= prev, (
                    f"Marks {m}: median {r.median_air} > previous {prev}"
                )
            prev = r.median_air

    def test_coverage_not_worse_than_none(self):
        base = run_validation(normalization=NormalizationMode.NONE)
        pw = run_validation(normalization=NormalizationMode.PIECEWISE_AFFINE)
        assert pw["coverage_rate"] >= base["coverage_rate"]

    def test_no_band_widening_vs_affine(self):
        """Piecewise should not widen bands beyond affine."""
        aff = run_validation(normalization=NormalizationMode.AFFINE_TWO_POINT)
        pw = run_validation(normalization=NormalizationMode.PIECEWISE_AFFINE)
        for a, p in zip(aff["results"], pw["results"]):
            a_width = a["predicted_conservative"] - a["predicted_best"]
            p_width = p["predicted_conservative"] - p["predicted_best"]
            assert p_width <= a_width + 1, (
                f"marks={a['marks']}: piecewise band {p_width} > affine band {a_width}"
            )


class TestCompareStrategiesPhase1BD:

    def test_compare_includes_piecewise(self):
        comp = compare_normalization_strategies()
        assert "piecewise_affine" in comp

    def test_all_four_modes_present(self):
        comp = compare_normalization_strategies()
        expected = {"none", "topper_score", "affine_two_point", "piecewise_affine"}
        assert set(comp.keys()) == expected

    def test_piecewise_does_not_degrade_low_mid(self):
        comp = compare_normalization_strategies()
        assert comp["piecewise_affine"]["low_mid_marks_coverage"] >= \
               comp["affine_two_point"]["low_mid_marks_coverage"]
