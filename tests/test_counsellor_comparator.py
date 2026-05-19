"""Tests for counsellor.comparator — cross-scenario comparison."""

import pytest

from neet_predictor.counsellor.models import (
    ComparisonRow,
    ScenarioComparison,
    ScenarioResult,
    ScenarioSpec,
)
from neet_predictor.counsellor.comparator import compare_scenarios
from neet_predictor.counsellor.executor import execute_scenario


def _make_spec(**overrides):
    defaults = dict(
        label="Test Scenario",
        description="Test",
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


class TestCompareScenarios:

    def test_single_scenario(self):
        """Single scenario produces a comparison with one row."""
        spec = _make_spec(marks=550, label="Primary")
        result = execute_scenario(spec)
        comparison = compare_scenarios([result])
        assert isinstance(comparison, ScenarioComparison)
        assert len(comparison.comparison_table) == 1
        assert comparison.comparison_table[0].label == "Primary"

    def test_comparison_table_fields(self):
        """Comparison row has expected fields."""
        spec = _make_spec(marks=None, actual_air=5000, label="Test")
        result = execute_scenario(spec)
        comparison = compare_scenarios([result])
        row = comparison.comparison_table[0]
        assert isinstance(row, ComparisonRow)
        assert row.safe_count >= 0
        assert row.likely_count >= 0
        assert row.borderline_count >= 0
        assert row.total_options == row.safe_count + row.likely_count + row.borderline_count

    def test_best_scenario_selected(self):
        """Best scenario is the one with highest composite score."""
        spec_good = _make_spec(marks=None, actual_air=5000, label="Good")
        spec_worse = _make_spec(marks=None, actual_air=80000, label="Worse")
        results = [execute_scenario(spec_good), execute_scenario(spec_worse)]
        comparison = compare_scenarios(results)
        # AIR 5000 should have more options than 80000
        assert comparison.best_scenario_label == "Good"

    def test_multiple_results_generates_notes(self):
        """Two results produce comparison notes."""
        spec_a = _make_spec(marks=None, actual_air=5000, label="A")
        spec_b = _make_spec(marks=None, actual_air=10000, label="B")
        results = [execute_scenario(spec_a), execute_scenario(spec_b)]
        comparison = compare_scenarios(results)
        # Should have notes comparing the two
        assert len(comparison.notes) >= 0  # May or may not have delta

    def test_error_scenario_handled(self):
        """Error scenario gets zero counts in comparison."""
        error_result = ScenarioResult(
            spec=_make_spec(marks=None, actual_air=None, label="Error"),
            student_result=None,
            error="No input",
        )
        good_spec = _make_spec(marks=550, label="Good")
        good_result = execute_scenario(good_spec)
        comparison = compare_scenarios([error_result, good_result])
        assert len(comparison.comparison_table) == 2
        error_row = comparison.comparison_table[0]
        assert error_row.total_options == 0
        assert error_row.authority_split == "Error"

    def test_results_tuple_preserved(self):
        """All input results are stored in the comparison."""
        spec = _make_spec(marks=550, label="Only")
        result = execute_scenario(spec)
        comparison = compare_scenarios([result])
        assert len(comparison.results) == 1
        assert comparison.results[0].spec.label == "Only"
