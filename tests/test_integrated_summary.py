"""Tests for Phase 1D: Student-Facing Result Contract."""

import pytest
from datetime import datetime

from neet_predictor.integrated.pipeline import UnifiedInput, run_prediction
from neet_predictor.integrated.summary import (
    StudentResult,
    build_student_result,
    InputSummary,
    RankSummary,
    RankUsedSummary,
    CollegeEntry,
    AuthoritySummary,
    ChanceBucket,
    CourseSplit,
    Metadata,
    CHANCE_ORDER,
    DEFAULT_TOP_N,
    ENGINE_VERSION,
    _LIMITATIONS,
)
from neet_predictor.rank.calibration import NormalizationMode


# ═══════════════════════════════════════════════════════
#  Fixtures
# ═══════════════════════════════════════════════════════


@pytest.fixture
def result_marks_only():
    inp = UnifiedInput(marks=600, national_category="General", home_state="Delhi")
    return run_prediction(inp)


@pytest.fixture
def result_air_only():
    inp = UnifiedInput(actual_air=15000, national_category="OBC", home_state="UP")
    return run_prediction(inp)


@pytest.fixture
def result_both():
    inp = UnifiedInput(
        marks=620, actual_air=25000,
        national_category="General", home_state="Delhi",
    )
    return run_prediction(inp)


@pytest.fixture
def result_karnataka():
    inp = UnifiedInput(
        actual_air=10000,
        national_category="OBC",
        home_state="Karnataka",
        karnataka_interest=True,
        karnataka_domicile=True,
        karnataka_category="2A",
    )
    return run_prediction(inp)


@pytest.fixture
def student_marks(result_marks_only):
    return build_student_result(result_marks_only)


@pytest.fixture
def student_air(result_air_only):
    return build_student_result(result_air_only)


@pytest.fixture
def student_both(result_both):
    return build_student_result(result_both)


@pytest.fixture
def student_karnataka(result_karnataka):
    return build_student_result(result_karnataka)


# ═══════════════════════════════════════════════════════
#  InputSummary
# ═══════════════════════════════════════════════════════


class TestInputSummary:

    def test_marks_only_input(self, student_marks):
        s = student_marks.input_summary
        assert s.marks == 600
        assert s.actual_air is None
        assert s.national_category == "General"
        assert s.home_state == "Delhi"

    def test_air_only_input(self, student_air):
        s = student_air.input_summary
        assert s.marks is None
        assert s.actual_air == 15000

    def test_both_input(self, student_both):
        s = student_both.input_summary
        assert s.marks == 620
        assert s.actual_air == 25000

    def test_normalization_is_string(self, student_marks):
        assert isinstance(student_marks.input_summary.normalization, str)
        assert student_marks.input_summary.normalization == "affine_two_point"

    def test_karnataka_fields(self, student_karnataka):
        s = student_karnataka.input_summary
        assert s.karnataka_interest is True
        assert s.karnataka_domicile is True
        assert s.karnataka_category == "2A"


# ═══════════════════════════════════════════════════════
#  RankSummary
# ═══════════════════════════════════════════════════════


class TestRankSummary:

    def test_marks_flow_has_estimate(self, student_marks):
        r = student_marks.rank_summary
        assert r.has_estimate is True
        assert r.best_case_air is not None
        assert r.median_air is not None
        assert r.conservative_air is not None
        assert r.confidence is not None
        assert r.method is not None

    def test_air_flow_has_no_estimate(self, student_air):
        r = student_air.rank_summary
        assert r.has_estimate is False
        assert r.best_case_air is None
        assert r.median_air is None
        assert r.conservative_air is None

    def test_rank_order(self, student_marks):
        r = student_marks.rank_summary
        assert r.best_case_air <= r.median_air <= r.conservative_air

    def test_both_flow_has_estimate(self, student_both):
        """Marks-based estimate is computed even when actual AIR is provided."""
        assert student_both.rank_summary.has_estimate is True


# ═══════════════════════════════════════════════════════
#  RankUsed
# ═══════════════════════════════════════════════════════


class TestRankUsed:

    def test_marks_flow_uses_median(self, student_marks):
        ru = student_marks.rank_used
        assert ru.source == "estimated_median"
        assert ru.air == student_marks.rank_summary.median_air

    def test_air_flow_uses_actual(self, student_air):
        ru = student_air.rank_used
        assert ru.source == "actual"
        assert ru.air == 15000

    def test_both_flow_uses_actual(self, student_both):
        ru = student_both.rank_used
        assert ru.source == "actual"
        assert ru.air == 25000

    def test_explanation_not_empty(self, student_marks):
        assert len(student_marks.rank_used.explanation) > 0


# ═══════════════════════════════════════════════════════
#  Shortlist
# ═══════════════════════════════════════════════════════


class TestShortlist:

    def test_shortlist_is_list(self, student_marks):
        assert isinstance(student_marks.shortlist, list)

    def test_shortlist_entries_are_college_entry(self, student_marks):
        for entry in student_marks.shortlist:
            assert isinstance(entry, CollegeEntry)

    def test_shortlist_respects_top_n(self, result_marks_only):
        sr = build_student_result(result_marks_only, top_n=5)
        assert len(sr.shortlist) <= 5

    def test_shortlist_default_top_n(self, student_marks):
        assert len(student_marks.shortlist) <= DEFAULT_TOP_N

    def test_shortlist_ordered_by_chance(self, student_marks):
        """Safe before Likely before Borderline before Unlikely."""
        indices = []
        for entry in student_marks.shortlist:
            if entry.chance in CHANCE_ORDER:
                indices.append(CHANCE_ORDER.index(entry.chance))
        # Should be non-decreasing
        for i in range(1, len(indices)):
            assert indices[i] >= indices[i - 1], (
                f"Shortlist not ordered: {student_marks.shortlist[i-1].chance} "
                f"before {student_marks.shortlist[i].chance}"
            )

    def test_shortlist_entries_have_required_fields(self, student_marks):
        if student_marks.shortlist:
            e = student_marks.shortlist[0]
            assert isinstance(e.college_name, str)
            assert isinstance(e.college_id, int)
            assert e.authority in ("MCC", "KEA")
            assert e.chance in CHANCE_ORDER

    def test_shortlist_prefers_usable_over_insufficient(self, result_marks_only):
        """Insufficient data should only appear if there aren't enough usable."""
        sr = build_student_result(result_marks_only, top_n=10)
        chances = [e.chance for e in sr.shortlist]
        # If there are usable entries, they come first
        usable = [c for c in chances if c != "Insufficient data"]
        insuf = [c for c in chances if c == "Insufficient data"]
        if usable and insuf:
            # All usable entries should be before all insufficient entries
            last_usable = len(chances) - 1 - chances[::-1].index(usable[-1])
            first_insuf = chances.index("Insufficient data")
            assert last_usable < first_insuf


# ═══════════════════════════════════════════════════════
#  Authority summaries
# ═══════════════════════════════════════════════════════


class TestAuthoritySummary:

    def test_mcc_summary_present(self, student_marks):
        s = student_marks.mcc_summary
        assert s.authority == "MCC"
        assert s.total >= 0
        assert isinstance(s.by_chance, list)

    def test_kea_summary_present(self, student_marks):
        s = student_marks.kea_summary
        assert s.authority == "KEA"

    def test_kea_exploratory_flag(self):
        inp = UnifiedInput(
            actual_air=10000,
            national_category="OBC",
            home_state="Karnataka",
            karnataka_interest=True,
            karnataka_domicile=True,
            # no karnataka_category → exploratory
        )
        result = run_prediction(inp)
        sr = build_student_result(result)
        assert sr.kea_summary.exploratory is True

    def test_chance_buckets_use_correct_labels(self, student_marks):
        for bucket in student_marks.mcc_summary.by_chance:
            assert bucket.label in CHANCE_ORDER
            assert bucket.count > 0

    def test_bucket_counts_sum_to_total(self, student_marks):
        s = student_marks.mcc_summary
        assert sum(b.count for b in s.by_chance) == s.total

    def test_karnataka_kea_total(self, student_karnataka):
        assert student_karnataka.kea_summary.total > 0


# ═══════════════════════════════════════════════════════
#  Course split
# ═══════════════════════════════════════════════════════


class TestCourseSplit:

    def test_course_split_is_list(self, student_marks):
        assert isinstance(student_marks.course_split, list)

    def test_course_split_entries(self, student_marks):
        for cs in student_marks.course_split:
            assert isinstance(cs, CourseSplit)
            assert cs.course in ("MBBS", "BDS")
            assert cs.count > 0

    def test_course_split_sums_to_shortlist(self, student_marks):
        total = sum(cs.count for cs in student_marks.course_split)
        assert total == len(student_marks.shortlist)


# ═══════════════════════════════════════════════════════
#  Warnings & Limitations
# ═══════════════════════════════════════════════════════


class TestWarningsAndLimitations:

    def test_warnings_from_pipeline(self, student_marks):
        assert len(student_marks.warnings) >= 3

    def test_limitations_always_present(self, student_marks):
        assert student_marks.limitations == _LIMITATIONS

    def test_limitations_include_kea_sparse(self, student_marks):
        kea_lim = [l for l in student_marks.limitations if "KEA" in l]
        assert len(kea_lim) >= 1

    def test_limitations_no_guarantee(self, student_marks):
        guarantee = [l for l in student_marks.limitations if "guarantee" in l.lower()]
        assert len(guarantee) >= 1

    def test_warnings_are_strings(self, student_marks):
        for w in student_marks.warnings:
            assert isinstance(w, str)
            assert len(w) > 0


# ═══════════════════════════════════════════════════════
#  Metadata
# ═══════════════════════════════════════════════════════


class TestMetadata:

    def test_generated_at_is_iso(self, student_marks):
        ts = student_marks.metadata.generated_at
        # Should parse without error
        datetime.fromisoformat(ts)

    def test_engine_version(self, student_marks):
        assert student_marks.metadata.engine_version == ENGINE_VERSION

    def test_top_n_recorded(self, student_marks):
        assert student_marks.metadata.top_n == DEFAULT_TOP_N

    def test_custom_top_n(self, result_marks_only):
        sr = build_student_result(result_marks_only, top_n=7)
        assert sr.metadata.top_n == 7

    def test_totals_match_pipeline(self, result_marks_only):
        sr = build_student_result(result_marks_only)
        cp = result_marks_only.college_predictions
        assert sr.metadata.total_mcc_predictions == len(cp.mcc_predictions)
        assert sr.metadata.total_kea_predictions == len(cp.kea_predictions)


# ═══════════════════════════════════════════════════════
#  Frozen / serialisable
# ═══════════════════════════════════════════════════════


class TestFrozenContract:

    def test_student_result_is_frozen(self, student_marks):
        with pytest.raises(AttributeError):
            student_marks.input_summary = None  # type: ignore[misc]

    def test_input_summary_is_frozen(self, student_marks):
        with pytest.raises(AttributeError):
            student_marks.input_summary.marks = 999  # type: ignore[misc]

    def test_rank_summary_is_frozen(self, student_marks):
        with pytest.raises(AttributeError):
            student_marks.rank_summary.best_case_air = 999  # type: ignore[misc]
