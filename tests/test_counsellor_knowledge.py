"""Tests for counsellor.knowledge — domain context injection."""

import pytest

from neet_predictor.counsellor.models import (
    ScenarioComparison,
    ScenarioResult,
    ScenarioSpec,
    StudentIntent,
)
from neet_predictor.counsellor.knowledge import build_knowledge_context
from neet_predictor.counsellor.executor import execute_scenario
from neet_predictor.counsellor.comparator import compare_scenarios


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
        raw_query="test",
    )
    defaults.update(overrides)
    return StudentIntent(**defaults)


def _make_comparison(air=5000):
    spec = ScenarioSpec(
        label="Test",
        description="Test",
        marks=None,
        actual_air=air,
        national_category="General",
        home_state="Bihar",
        pwd=False,
        karnataka_interest=False,
        karnataka_domicile=False,
        karnataka_category=None,
        course_pref="MBBS",
        college_type_pref="any",
    )
    result = execute_scenario(spec)
    return compare_scenarios([result])


class TestKnowledgeContext:

    def test_returns_string(self):
        """build_knowledge_context returns a non-empty string."""
        intent = _make_intent()
        comparison = _make_comparison()
        ctx = build_knowledge_context(intent, comparison)
        assert isinstance(ctx, str)
        assert len(ctx) > 50

    def test_category_info_included(self):
        """Category-specific info is included."""
        intent = _make_intent(national_category="OBC")
        comparison = _make_comparison()
        ctx = build_knowledge_context(intent, comparison)
        assert "OBC" in ctx

    def test_sc_category_info(self):
        """SC category info differs from OBC."""
        intent = _make_intent(national_category="SC")
        comparison = _make_comparison()
        ctx = build_knowledge_context(intent, comparison)
        assert "SC" in ctx
        assert "3-6x" in ctx

    def test_marks_based_adds_experimental(self):
        """Marks-based input adds experimental warning."""
        intent = _make_intent(marks=550, actual_air=None)
        comparison = _make_comparison()
        ctx = build_knowledge_context(intent, comparison)
        assert "EXPERIMENTAL" in ctx

    def test_air_based_no_experimental(self):
        """AIR-based input does NOT add experimental warning."""
        intent = _make_intent(marks=None, actual_air=5000)
        comparison = _make_comparison()
        ctx = build_knowledge_context(intent, comparison)
        assert "EXPERIMENTAL" not in ctx

    def test_karnataka_includes_kea_caveat(self):
        """Karnataka interest adds KEA caveat."""
        intent = _make_intent(karnataka_interest=True)
        comparison = _make_comparison()
        ctx = build_knowledge_context(intent, comparison)
        assert "KEA" in ctx
        assert "R2 cutoffs" in ctx

    def test_no_karnataka_no_kea(self):
        """No Karnataka interest omits KEA caveat."""
        intent = _make_intent(karnataka_interest=False)
        comparison = _make_comparison()
        ctx = build_knowledge_context(intent, comparison)
        assert "R2 cutoffs" not in ctx

    def test_tier_context_included(self):
        """Tier context included based on rank."""
        intent = _make_intent(marks=None, actual_air=5000)
        comparison = _make_comparison(air=5000)
        ctx = build_knowledge_context(intent, comparison)
        assert "Tier" in ctx

    def test_competition_and_round_info(self):
        """Competition and round dynamics always present."""
        intent = _make_intent()
        comparison = _make_comparison()
        ctx = build_knowledge_context(intent, comparison)
        assert "competition" in ctx.lower() or "46:1" in ctx
        assert "R2" in ctx or "round" in ctx.lower()
