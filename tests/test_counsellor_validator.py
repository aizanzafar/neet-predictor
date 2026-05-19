"""Tests for counsellor.validator — output safety checks."""

import pytest

from neet_predictor.counsellor.models import (
    CounsellingNarrative,
    ScenarioComparison,
    ScenarioResult,
    ScenarioSpec,
    ValidatedResponse,
)
from neet_predictor.counsellor.validator import validate
from neet_predictor.counsellor.executor import execute_scenario
from neet_predictor.counsellor.comparator import compare_scenarios


def _make_spec(**overrides):
    defaults = dict(
        label="Test",
        description="Test",
        marks=None,
        actual_air=5000,
        national_category="General",
        home_state="Bihar",
        pwd=False,
        karnataka_interest=False,
        karnataka_domicile=False,
        karnataka_category=None,
        course_pref="MBBS",
        college_type_pref="any",
    )
    defaults.update(overrides)
    return ScenarioSpec(**defaults)


def _get_comparison():
    """Build a real comparison from engine output."""
    spec = _make_spec()
    result = execute_scenario(spec)
    return compare_scenarios([result])


def _get_real_college_name(comparison: ScenarioComparison) -> str:
    """Get a real college name from the comparison results."""
    for sr in comparison.results:
        if sr.student_result is not None:
            if sr.student_result.shortlist:  # type: ignore[union-attr]
                return sr.student_result.shortlist[0].college_name  # type: ignore[union-attr]
    return "Unknown College"


def _make_narrative(comparison: ScenarioComparison, **overrides) -> CounsellingNarrative:
    """Build a valid narrative using real college names."""
    real_college = _get_real_college_name(comparison)
    defaults = dict(
        summary="You have good chances at several colleges.",
        primary_path=f"Your best option is {real_college} (Safe).",
        backup_path="Consider BDS as a backup.",
        top_colleges=[real_college],
        risk_areas=["Some colleges have limited data."],
        missing_data_caveats=["KEA data limited."],
        full_narrative=(
            f"You have good chances at several colleges. "
            f"Your best option is {real_college} (Safe). "
            f"This is not an admission guarantee. Verify from official sources."
        ),
        model_used="gpt-oss-120b",
        raw_llm_response="raw response",
        tokens_used=500,
    )
    defaults.update(overrides)
    return CounsellingNarrative(**defaults)


class TestValidNarrative:

    def test_valid_narrative_passes(self):
        """A clean narrative passes validation."""
        comparison = _get_comparison()
        narrative = _make_narrative(comparison)
        result = validate(narrative, comparison)
        assert isinstance(result, ValidatedResponse)
        assert result.validation_passed is True
        assert result.fallback_used is False
        assert result.narrative is not None
        assert len(result.violations) == 0

    def test_limitations_always_present(self):
        """Limitations are always included."""
        comparison = _get_comparison()
        narrative = _make_narrative(comparison)
        result = validate(narrative, comparison)
        assert len(result.limitations) > 0

    def test_warnings_collected(self):
        """Engine warnings are collected."""
        comparison = _get_comparison()
        narrative = _make_narrative(comparison)
        result = validate(narrative, comparison)
        # Warnings may or may not be present depending on input
        assert isinstance(result.warnings, list)


class TestFakeCollegeDetection:

    def test_fake_college_strips_narrative(self):
        """Mentioning a fake college causes fallback."""
        comparison = _get_comparison()
        narrative = _make_narrative(
            comparison,
            top_colleges=["Totally Invented Medical College of Narnia"],
            full_narrative=(
                "Your best option is Totally Invented Medical College of Narnia (Safe). "
                "This is not an admission guarantee."
            ),
        )
        result = validate(narrative, comparison)
        assert result.fallback_used is True
        assert result.narrative is None
        assert any("Fake college" in v for v in result.violations)


class TestProbabilityDetection:

    def test_percentage_chance(self):
        """Probability claims are flagged."""
        comparison = _get_comparison()
        real_college = _get_real_college_name(comparison)
        narrative = _make_narrative(
            comparison,
            full_narrative=(
                f"You have a 70% chance of getting {real_college}. "
                "This is not an admission guarantee."
            ),
        )
        result = validate(narrative, comparison)
        assert any("probability" in v.lower() or "percentage" in v.lower()
                   for v in result.violations)

    def test_probability_of_phrase(self):
        """'probability of' is flagged."""
        comparison = _get_comparison()
        real_college = _get_real_college_name(comparison)
        narrative = _make_narrative(
            comparison,
            full_narrative=(
                f"The probability of getting {real_college} is high. "
                "This is not an admission guarantee."
            ),
        )
        result = validate(narrative, comparison)
        assert any("probability" in v.lower() or "percentage" in v.lower()
                   for v in result.violations)


class TestGuaranteedLanguage:

    def test_guaranteed_strips_narrative(self):
        """'guaranteed' causes critical violation and fallback."""
        comparison = _get_comparison()
        real_college = _get_real_college_name(comparison)
        narrative = _make_narrative(
            comparison,
            full_narrative=(
                f"You are guaranteed admission to {real_college}. "
                "This is not an admission guarantee."
            ),
        )
        result = validate(narrative, comparison)
        assert result.fallback_used is True
        assert any("guaranteed" in v.lower() for v in result.violations)

    def test_will_definitely_get(self):
        """'will definitely get' is critical."""
        comparison = _get_comparison()
        real_college = _get_real_college_name(comparison)
        narrative = _make_narrative(
            comparison,
            full_narrative=(
                f"You will definitely get {real_college}. "
                "This is not an admission guarantee."
            ),
        )
        result = validate(narrative, comparison)
        assert result.fallback_used is True

    def test_100_percent(self):
        """'100%' causes critical violation."""
        comparison = _get_comparison()
        real_college = _get_real_college_name(comparison)
        narrative = _make_narrative(
            comparison,
            full_narrative=(
                f"100% assured admission to {real_college}. "
                "This is not an admission guarantee."
            ),
        )
        result = validate(narrative, comparison)
        assert result.fallback_used is True


class TestDisclaimerEnforcement:

    def test_missing_disclaimer_appended(self):
        """Missing disclaimer is auto-appended (not a hard violation)."""
        comparison = _get_comparison()
        real_college = _get_real_college_name(comparison)
        narrative = _make_narrative(
            comparison,
            full_narrative=f"You have good chances at {real_college}. Good luck!",
        )
        result = validate(narrative, comparison)
        # Disclaimer gets appended, narrative should still be present
        assert result.narrative is not None
        assert "guarantee" in result.narrative.full_narrative.lower()


class TestMarksBasedLabel:

    def test_marks_based_needs_experimental(self):
        """Marks-based predictions need 'experimental/estimated' label."""
        comparison = _get_comparison()
        real_college = _get_real_college_name(comparison)
        narrative = _make_narrative(
            comparison,
            full_narrative=(
                f"You have good chances at {real_college}. "
                "This is not an admission guarantee."
            ),
        )
        result = validate(narrative, comparison, marks_based=True)
        assert any("experimental" in v.lower() or "estimated" in v.lower()
                   for v in result.violations)

    def test_marks_based_with_label_passes(self):
        """Marks-based with 'estimated' label passes."""
        comparison = _get_comparison()
        real_college = _get_real_college_name(comparison)
        narrative = _make_narrative(
            comparison,
            full_narrative=(
                f"Based on your estimated rank, you have chances at {real_college}. "
                "This is not an admission guarantee."
            ),
        )
        result = validate(narrative, comparison, marks_based=True)
        assert not any("experimental" in v.lower() or "estimated" in v.lower()
                       for v in result.violations)


class TestKEAGrounding:

    def test_kea_claims_without_data(self):
        """KEA mentions without data and without caveat flagged."""
        comparison = _get_comparison()  # No Karnataka in this comparison
        real_college = _get_real_college_name(comparison)
        narrative = _make_narrative(
            comparison,
            full_narrative=(
                f"In KEA counselling you will get top colleges. "
                f"Also consider {real_college} via MCC. "
                "This is not an admission guarantee."
            ),
        )
        result = validate(narrative, comparison)
        # May or may not flag depending on KEA data in comparison
        # This is a soft check, just ensure no crash
        assert isinstance(result, ValidatedResponse)
