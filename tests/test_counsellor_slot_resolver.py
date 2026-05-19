"""Tests for counsellor.slot_resolver — deterministic branching logic."""

import pytest

from neet_predictor.counsellor.models import (
    ClarificationNeeded,
    ScenarioSpec,
    StudentIntent,
)
from neet_predictor.counsellor.slot_resolver import resolve_slots


def _make_intent(**overrides):
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


class TestClarificationNeeded:

    def test_missing_marks_and_air(self):
        """Must ask for marks/AIR if neither provided."""
        intent = _make_intent(marks=None, actual_air=None)
        result = resolve_slots(intent)
        assert isinstance(result, ClarificationNeeded)
        assert any("marks" in q.lower() or "rank" in q.lower() for q in result.questions)

    def test_missing_category(self):
        """Must ask for category if not provided."""
        intent = _make_intent(national_category=None)
        result = resolve_slots(intent)
        assert isinstance(result, ClarificationNeeded)
        assert any("category" in q.lower() for q in result.questions)

    def test_missing_both(self):
        """Multiple questions if both missing."""
        intent = _make_intent(marks=None, actual_air=None, national_category=None)
        result = resolve_slots(intent)
        assert isinstance(result, ClarificationNeeded)
        assert len(result.questions) == 2


class TestPrimaryScenario:

    def test_basic_mbbs_scenario(self):
        """Simple case: one primary MCC scenario."""
        intent = _make_intent()
        result = resolve_slots(intent)
        assert isinstance(result, list)
        assert len(result) == 1
        spec = result[0]
        assert isinstance(spec, ScenarioSpec)
        assert "MCC" in spec.label
        assert spec.marks == 550
        assert spec.national_category == "OBC"
        assert spec.course_pref == "MBBS"

    def test_actual_air_used(self):
        """AIR passed through correctly."""
        intent = _make_intent(marks=None, actual_air=12000)
        result = resolve_slots(intent)
        assert isinstance(result, list)
        assert result[0].actual_air == 12000
        assert result[0].marks is None

    def test_home_state_defaults_to_unknown(self):
        """Missing home_state uses 'Unknown'."""
        intent = _make_intent(home_state=None)
        result = resolve_slots(intent)
        assert isinstance(result, list)
        assert result[0].home_state == "Unknown"


class TestKarnatakaScenarios:

    def test_karnataka_confirmed_domicile(self):
        """Karnataka with confirmed domicile adds one KEA scenario."""
        intent = _make_intent(
            karnataka_interest=True,
            karnataka_domicile=True,
            karnataka_category="2A",
        )
        result = resolve_slots(intent)
        assert isinstance(result, list)
        # Primary MCC + one KEA
        assert len(result) == 2
        kea = result[1]
        assert "KEA" in kea.label
        assert kea.karnataka_domicile is True
        assert kea.karnataka_category == "2A"

    def test_karnataka_unknown_domicile_branches(self):
        """Uncertain domicile creates two KEA branches."""
        intent = _make_intent(
            karnataka_interest=True,
            karnataka_domicile=None,
            karnataka_category=None,
        )
        result = resolve_slots(intent)
        assert isinstance(result, list)
        # Primary MCC + KEA with domicile + KEA without
        assert len(result) == 3
        labels = [s.label for s in result]
        assert any("domicile" in l.lower() for l in labels)
        assert any("no domicile" in l.lower() for l in labels)

    def test_karnataka_no_interest(self):
        """No Karnataka interest = no KEA scenarios."""
        intent = _make_intent(karnataka_interest=False)
        result = resolve_slots(intent)
        assert isinstance(result, list)
        assert len(result) == 1
        assert "KEA" not in result[0].label


class TestBDSBackup:

    def test_bds_backup_adds_scenario(self):
        """BDS backup adds one more scenario."""
        intent = _make_intent(bds_backup=True)
        result = resolve_slots(intent)
        assert isinstance(result, list)
        assert len(result) == 2
        bds_spec = result[1]
        assert "BDS" in bds_spec.label
        assert bds_spec.course_pref == "MBBS+BDS"

    def test_bds_without_backup_flag(self):
        """No BDS backup = only primary."""
        intent = _make_intent(bds_backup=False)
        result = resolve_slots(intent)
        assert isinstance(result, list)
        assert len(result) == 1


class TestMaxScenarios:

    def test_full_branching(self):
        """Karnataka uncertain + BDS backup = 4 scenarios max."""
        intent = _make_intent(
            karnataka_interest=True,
            karnataka_domicile=None,
            bds_backup=True,
        )
        result = resolve_slots(intent)
        assert isinstance(result, list)
        # MCC primary + KEA with + KEA without + BDS backup = 4
        assert len(result) == 4
