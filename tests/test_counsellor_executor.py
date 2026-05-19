"""Tests for counsellor.executor — deterministic engine calls."""

import pytest

from neet_predictor.counsellor.models import ScenarioResult, ScenarioSpec
from neet_predictor.counsellor.executor import execute_scenario, execute_all


def _make_spec(**overrides):
    defaults = dict(
        label="MBBS, MCC AIQ (General)",
        description="Test scenario",
        marks=550,
        actual_air=None,
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


class TestExecuteScenario:

    def test_valid_marks_returns_result(self):
        """A valid marks-based spec returns a ScenarioResult with student_result."""
        spec = _make_spec(marks=550, national_category="General")
        result = execute_scenario(spec)
        assert isinstance(result, ScenarioResult)
        assert result.error is None
        assert result.student_result is not None

    def test_valid_air_returns_result(self):
        """A valid AIR-based spec returns a ScenarioResult."""
        spec = _make_spec(marks=None, actual_air=12000, national_category="OBC")
        result = execute_scenario(spec)
        assert isinstance(result, ScenarioResult)
        assert result.error is None
        assert result.student_result is not None

    def test_result_has_shortlist(self):
        """Student result should have a non-empty shortlist for mid-range ranks."""
        spec = _make_spec(marks=None, actual_air=5000, national_category="General")
        result = execute_scenario(spec)
        assert result.student_result is not None
        assert len(result.student_result.shortlist) > 0  # type: ignore[union-attr]

    def test_obc_category_works(self):
        """OBC category produces results."""
        spec = _make_spec(marks=520, national_category="OBC")
        result = execute_scenario(spec)
        assert result.error is None
        assert result.student_result is not None

    def test_sc_category_works(self):
        """SC category produces results."""
        spec = _make_spec(marks=450, national_category="SC")
        result = execute_scenario(spec)
        assert result.error is None

    def test_karnataka_interest(self):
        """Karnataka interest flag passes through."""
        spec = _make_spec(
            marks=550,
            national_category="General",
            karnataka_interest=True,
            karnataka_domicile=True,
            karnataka_category="GM",
        )
        result = execute_scenario(spec)
        assert result.error is None

    def test_invalid_spec_returns_error(self):
        """Invalid input (no marks or AIR) captured as error, not exception."""
        spec = _make_spec(marks=None, actual_air=None)
        result = execute_scenario(spec)
        assert result.error is not None
        assert result.student_result is None


class TestExecuteAll:

    def test_multiple_scenarios(self):
        """execute_all processes all specs and returns same-length list."""
        specs = [
            _make_spec(marks=550, label="Scenario A"),
            _make_spec(marks=500, label="Scenario B"),
            _make_spec(marks=None, actual_air=20000, label="Scenario C"),
        ]
        results = execute_all(specs)
        assert len(results) == 3
        assert all(isinstance(r, ScenarioResult) for r in results)
        assert all(r.error is None for r in results)

    def test_order_preserved(self):
        """Results preserve the order of input specs."""
        specs = [
            _make_spec(marks=600, label="First"),
            _make_spec(marks=400, label="Second"),
        ]
        results = execute_all(specs)
        assert results[0].spec.label == "First"
        assert results[1].spec.label == "Second"

    def test_error_does_not_stop_others(self):
        """One failing spec doesn't block other scenarios."""
        specs = [
            _make_spec(marks=None, actual_air=None, label="Bad"),
            _make_spec(marks=550, label="Good"),
        ]
        results = execute_all(specs)
        assert results[0].error is not None
        assert results[1].error is None
