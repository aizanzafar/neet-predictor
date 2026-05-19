"""Tests for counsellor.models — dataclass contracts."""

import pytest

from neet_predictor.counsellor.models import (
    VALID_NATIONAL_CATEGORIES,
    VALID_KEA_CATEGORIES,
    VALID_COURSE_PREFS,
    VALID_COLLEGE_TYPE_PREFS,
    StudentIntent,
    ClarificationNeeded,
    ScenarioSpec,
    ScenarioResult,
    ComparisonRow,
    ScenarioComparison,
    CounsellingNarrative,
    ValidatedResponse,
)


class TestStudentIntent:

    def _make_intent(self, **overrides):
        defaults = dict(
            marks=550,
            actual_air=None,
            national_category="OBC",
            home_state="Bihar",
            pwd=False,
            karnataka_interest=False,
            karnataka_domicile=None,
            karnataka_category=None,
            course_pref="MBBS",
            college_type_pref="any",
            bds_backup=False,
            target_year=None,
            missing_slots=(),
            uncertain_slots=(),
            ambiguity_notes=(),
            raw_query="test query",
        )
        defaults.update(overrides)
        return StudentIntent(**defaults)

    def test_basic_creation(self):
        intent = self._make_intent()
        assert intent.marks == 550
        assert intent.national_category == "OBC"
        assert intent.home_state == "Bihar"

    def test_frozen(self):
        intent = self._make_intent()
        with pytest.raises(AttributeError):
            intent.marks = 600  # type: ignore[misc]

    def test_with_karnataka(self):
        intent = self._make_intent(
            karnataka_interest=True,
            karnataka_domicile=True,
            karnataka_category="2A",
        )
        assert intent.karnataka_interest is True
        assert intent.karnataka_category == "2A"


class TestClarificationNeeded:

    def test_creation(self):
        cn = ClarificationNeeded(
            questions=("What is your category?",),
            partial_intent=None,
        )
        assert len(cn.questions) == 1


class TestScenarioSpec:

    def test_creation(self):
        spec = ScenarioSpec(
            label="MBBS, MCC AIQ (OBC)",
            description="Primary prediction",
            marks=550,
            actual_air=None,
            national_category="OBC",
            home_state="Bihar",
            pwd=False,
            karnataka_interest=False,
            karnataka_domicile=False,
            karnataka_category=None,
            course_pref="MBBS",
            college_type_pref="any",
        )
        assert spec.label == "MBBS, MCC AIQ (OBC)"
        assert spec.marks == 550


class TestConstants:

    def test_valid_categories(self):
        assert "General" in VALID_NATIONAL_CATEGORIES
        assert "OBC" in VALID_NATIONAL_CATEGORIES
        assert "SC" in VALID_NATIONAL_CATEGORIES
        assert "ST" in VALID_NATIONAL_CATEGORIES
        assert "EWS" in VALID_NATIONAL_CATEGORIES

    def test_valid_kea_categories(self):
        assert "GM" in VALID_KEA_CATEGORIES
        assert "2A" in VALID_KEA_CATEGORIES

    def test_valid_course_prefs(self):
        assert "MBBS" in VALID_COURSE_PREFS
        assert "BDS" in VALID_COURSE_PREFS
        assert "MBBS+BDS" in VALID_COURSE_PREFS
