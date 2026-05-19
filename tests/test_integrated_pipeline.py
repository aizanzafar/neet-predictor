"""Tests for Phase 1C: Integrated Marks/AIR → College Prediction Pipeline."""

import pytest

from neet_predictor.integrated.pipeline import (
    UnifiedInput,
    UnifiedResult,
    RankUsed,
    run_prediction,
    _WARN_HISTORICAL,
    _WARN_MARKS_EXPERIMENTAL,
    _WARN_ESTIMATED_AIR_USED,
    _WARN_ACTUAL_AIR_USED,
    _WARN_MCC_KEA_VERIFY,
    _WARN_KEA_SPARSE,
)
from neet_predictor.integrated.explainer import format_unified_result
from neet_predictor.rank.calibration import NormalizationMode
from neet_predictor.config import VALIDATION_YEAR


# ═══════════════════════════════════════════════════════
#  Input validation
# ═══════════════════════════════════════════════════════


class TestInputValidation:

    def test_missing_marks_and_air_raises(self):
        """Must provide at least one of marks or actual_air."""
        with pytest.raises(ValueError, match="At least one"):
            UnifiedInput(national_category="General", home_state="Delhi")

    def test_invalid_marks_too_high(self):
        with pytest.raises(ValueError, match="marks must be"):
            UnifiedInput(marks=800, national_category="General", home_state="Delhi")

    def test_invalid_marks_negative(self):
        with pytest.raises(ValueError, match="marks must be"):
            UnifiedInput(marks=-10, national_category="General", home_state="Delhi")

    def test_invalid_air_zero(self):
        with pytest.raises(ValueError, match="actual_air must be"):
            UnifiedInput(actual_air=0, national_category="General", home_state="Delhi")

    def test_invalid_air_negative(self):
        with pytest.raises(ValueError, match="actual_air must be"):
            UnifiedInput(actual_air=-5, national_category="General", home_state="Delhi")

    def test_invalid_category(self):
        with pytest.raises(ValueError, match="national_category"):
            UnifiedInput(marks=600, national_category="Invalid", home_state="Delhi")

    def test_invalid_karnataka_category(self):
        with pytest.raises(ValueError, match="karnataka_category"):
            UnifiedInput(
                marks=600, national_category="General", home_state="Karnataka",
                karnataka_interest=True, karnataka_domicile=True,
                karnataka_category="INVALID",
            )

    def test_valid_marks_only(self):
        inp = UnifiedInput(marks=600, national_category="General", home_state="Delhi")
        assert inp.marks == 600
        assert inp.actual_air is None

    def test_valid_air_only(self):
        inp = UnifiedInput(actual_air=5000, national_category="OBC", home_state="UP")
        assert inp.actual_air == 5000
        assert inp.marks is None

    def test_valid_both(self):
        inp = UnifiedInput(
            marks=620, actual_air=25000,
            national_category="General", home_state="Delhi",
        )
        assert inp.marks == 620
        assert inp.actual_air == 25000

    def test_marks_zero_is_valid(self):
        inp = UnifiedInput(marks=0, national_category="General", home_state="Delhi")
        assert inp.marks == 0

    def test_marks_720_is_valid(self):
        inp = UnifiedInput(marks=720, national_category="General", home_state="Delhi")
        assert inp.marks == 720


# ═══════════════════════════════════════════════════════
#  Defaults
# ═══════════════════════════════════════════════════════


class TestDefaults:

    def test_default_normalization_is_affine(self):
        inp = UnifiedInput(marks=600, national_category="General", home_state="Delhi")
        assert inp.normalization == NormalizationMode.AFFINE_TWO_POINT

    def test_default_target_year(self):
        inp = UnifiedInput(marks=600, national_category="General", home_state="Delhi")
        assert inp.target_year == VALIDATION_YEAR

    def test_default_course(self):
        inp = UnifiedInput(marks=600, national_category="General", home_state="Delhi")
        assert inp.course_pref == "MBBS"


# ═══════════════════════════════════════════════════════
#  Flow A: Actual AIR only
# ═══════════════════════════════════════════════════════


class TestFlowActualAIR:

    @pytest.fixture
    def result_air_only(self):
        inp = UnifiedInput(
            actual_air=15000,
            national_category="OBC",
            home_state="Karnataka",
            karnataka_interest=True,
            karnataka_domicile=True,
            karnataka_category="2A",
        )
        return run_prediction(inp)

    def test_rank_used_is_actual(self, result_air_only):
        assert result_air_only.rank_used.source == "actual"
        assert result_air_only.rank_used.air == 15000

    def test_no_rank_estimate(self, result_air_only):
        assert result_air_only.rank_estimate is None

    def test_college_predictions_present(self, result_air_only):
        cp = result_air_only.college_predictions
        assert cp is not None
        assert cp.profile.air == 15000

    def test_result_has_warnings(self, result_air_only):
        assert len(result_air_only.warnings) > 0
        assert _WARN_HISTORICAL in result_air_only.warnings

    def test_no_estimated_air_warning(self, result_air_only):
        assert _WARN_ESTIMATED_AIR_USED not in result_air_only.warnings

    def test_kea_predictions_present(self, result_air_only):
        """Karnataka interest → KEA predictions should be generated."""
        cp = result_air_only.college_predictions
        assert isinstance(cp.kea_predictions, list)


# ═══════════════════════════════════════════════════════
#  Flow B: Marks only
# ═══════════════════════════════════════════════════════


class TestFlowMarksOnly:

    @pytest.fixture
    def result_marks_only(self):
        inp = UnifiedInput(
            marks=620,
            national_category="General",
            home_state="Delhi",
        )
        return run_prediction(inp)

    def test_rank_estimate_present(self, result_marks_only):
        assert result_marks_only.rank_estimate is not None
        assert result_marks_only.rank_estimate.marks == 620

    def test_median_air_used(self, result_marks_only):
        ru = result_marks_only.rank_used
        assert ru.source == "estimated_median"
        re = result_marks_only.rank_estimate
        assert ru.air == re.median_air

    def test_college_predictions_use_median(self, result_marks_only):
        cp = result_marks_only.college_predictions
        re = result_marks_only.rank_estimate
        assert cp.profile.air == re.median_air

    def test_estimated_air_warning_present(self, result_marks_only):
        assert _WARN_ESTIMATED_AIR_USED in result_marks_only.warnings

    def test_marks_experimental_warning(self, result_marks_only):
        assert _WARN_MARKS_EXPERIMENTAL in result_marks_only.warnings

    def test_rank_estimate_has_all_fields(self, result_marks_only):
        re = result_marks_only.rank_estimate
        assert re.best_case_air > 0
        assert re.median_air > 0
        assert re.conservative_air > 0
        assert re.best_case_air <= re.median_air <= re.conservative_air

    def test_mcc_kea_verify_warning(self, result_marks_only):
        assert _WARN_MCC_KEA_VERIFY in result_marks_only.warnings


# ═══════════════════════════════════════════════════════
#  Flow C: Marks + actual AIR
# ═══════════════════════════════════════════════════════


class TestFlowMarksAndAIR:

    @pytest.fixture
    def result_both(self):
        inp = UnifiedInput(
            marks=620,
            actual_air=25000,
            national_category="General",
            home_state="Delhi",
        )
        return run_prediction(inp)

    def test_actual_air_used_for_college(self, result_both):
        assert result_both.rank_used.source == "actual"
        assert result_both.rank_used.air == 25000

    def test_rank_estimate_still_computed(self, result_both):
        """Marks-based estimate is shown for comparison."""
        assert result_both.rank_estimate is not None
        assert result_both.rank_estimate.marks == 620

    def test_college_uses_actual_not_estimated(self, result_both):
        assert result_both.college_predictions.profile.air == 25000

    def test_actual_air_warning_present(self, result_both):
        assert _WARN_ACTUAL_AIR_USED in result_both.warnings


# ═══════════════════════════════════════════════════════
#  Category & Karnataka
# ═══════════════════════════════════════════════════════


class TestCategoryBehavior:

    def test_category_does_not_affect_air_estimate(self):
        r_gen = run_prediction(UnifiedInput(
            marks=600, national_category="General", home_state="Delhi",
        ))
        r_obc = run_prediction(UnifiedInput(
            marks=600, national_category="OBC", home_state="Delhi",
        ))
        assert r_gen.rank_estimate.median_air == r_obc.rank_estimate.median_air

    def test_karnataka_category_not_inferred(self):
        """Karnataka category must be explicitly provided, never derived."""
        inp = UnifiedInput(
            actual_air=10000,
            national_category="OBC",
            home_state="Karnataka",
            karnataka_interest=True,
            karnataka_domicile=True,
            # karnataka_category NOT provided — should NOT default to 2A/2B
        )
        result = run_prediction(inp)
        cp = result.college_predictions
        # Without KEA category, domicile user sees GM only (exploratory)
        assert cp.kea_exploratory is True


# ═══════════════════════════════════════════════════════
#  Warnings
# ═══════════════════════════════════════════════════════


class TestWarnings:

    def test_always_has_historical_warning(self):
        result = run_prediction(UnifiedInput(
            actual_air=5000, national_category="General", home_state="Delhi",
        ))
        assert _WARN_HISTORICAL in result.warnings

    def test_always_has_mcc_kea_verify(self):
        result = run_prediction(UnifiedInput(
            actual_air=5000, national_category="General", home_state="Delhi",
        ))
        assert _WARN_MCC_KEA_VERIFY in result.warnings

    def test_always_has_kea_sparse(self):
        result = run_prediction(UnifiedInput(
            actual_air=5000, national_category="General", home_state="Delhi",
        ))
        assert _WARN_KEA_SPARSE in result.warnings


# ═══════════════════════════════════════════════════════
#  Result structure
# ═══════════════════════════════════════════════════════


class TestResultStructure:

    def test_result_has_rank_section_and_college_section(self):
        result = run_prediction(UnifiedInput(
            marks=600, national_category="General", home_state="Delhi",
        ))
        # Rank section
        assert result.rank_estimate is not None
        assert result.rank_used is not None
        # College section
        assert result.college_predictions is not None
        assert isinstance(result.college_predictions.mcc_predictions, list)
        assert isinstance(result.college_predictions.kea_predictions, list)

    def test_result_has_input(self):
        inp = UnifiedInput(marks=600, national_category="General", home_state="Delhi")
        result = run_prediction(inp)
        assert result.input is inp

    def test_result_has_warnings_list(self):
        result = run_prediction(UnifiedInput(
            marks=600, national_category="General", home_state="Delhi",
        ))
        assert isinstance(result.warnings, list)
        assert len(result.warnings) >= 3  # historical + experimental + estimated + verify + sparse


# ═══════════════════════════════════════════════════════
#  Explainer
# ═══════════════════════════════════════════════════════


class TestExplainer:

    def test_format_marks_only(self):
        result = run_prediction(UnifiedInput(
            marks=600, national_category="General", home_state="Delhi",
        ))
        text = format_unified_result(result)
        assert "Marks: 600" in text
        assert "estimated_median" in text
        assert "Warnings" in text

    def test_format_air_only(self):
        result = run_prediction(UnifiedInput(
            actual_air=10000, national_category="OBC", home_state="UP",
        ))
        text = format_unified_result(result)
        assert "Actual AIR: 10,000" in text
        assert "actual" in text
        assert "Not applicable" in text

    def test_format_both(self):
        result = run_prediction(UnifiedInput(
            marks=620, actual_air=25000,
            national_category="General", home_state="Delhi",
        ))
        text = format_unified_result(result)
        assert "Marks: 620" in text
        assert "Actual AIR: 25,000" in text
        assert "actual" in text
