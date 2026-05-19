"""Tests for data validation (BLUEPRINT Part C5 rules)."""

import pandas as pd
import pytest

from neet_predictor.dataio.validator import (
    ValidationResult,
    validate_allotments,
    validate_closing_ranks,
    validate_colleges,
    validate_data_sources,
    validate_exam_years,
    validate_marks_rank_points,
)


# ═══════════════════════════════════════════════════════════════
# Sample valid data (marked as SAMPLE — not real NEET data)
# ═══════════════════════════════════════════════════════════════

def _sample_sources():
    """SAMPLE data for testing only — not real."""
    return pd.DataFrame({
        "source_id": [1, 2],
        "source_type": ["OFFICIAL_NTA", "SECONDARY_PORTAL"],
        "source_name": ["NTA 2024 Result Notice", "Careers360 Table"],
        "confidence": ["high", "medium"],
    })


def _sample_marks_rank_valid():
    """SAMPLE: valid monotonic marks-rank data."""
    return pd.DataFrame({
        "year": [2024, 2024, 2024, 2024],
        "marks_min": [700, 650, 600, 550],
        "marks_max": [700, 650, 600, 550],
        "rank_min": [50, 2000, 10000, 30000],
        "rank_max": [100, 3000, 15000, 45000],
        "source_id": [1, 1, 1, 1],
        "confidence": ["high", "high", "high", "high"],
    })


def _sample_marks_rank_bad_monotonicity():
    """SAMPLE: marks go up but rank also goes up (violation)."""
    return pd.DataFrame({
        "year": [2024, 2024],
        "marks_min": [700, 650],
        "marks_max": [700, 650],
        "rank_min": [5000, 2000],  # 700 marks has WORSE rank than 650 — violation!
        "rank_max": [6000, 3000],
        "source_id": [1, 1],
        "confidence": ["high", "high"],
    })


# ═══════════════════════════════════════════════════════════════
# Tests: data_sources
# ═══════════════════════════════════════════════════════════════

class TestDataSourcesValidation:

    def test_valid_sources(self):
        result = validate_data_sources(_sample_sources())
        assert result.is_valid

    def test_invalid_source_type(self):
        df = pd.DataFrame({
            "source_id": [1],
            "source_type": ["INVALID_TYPE"],
            "source_name": ["test"],
            "confidence": ["high"],
        })
        result = validate_data_sources(df)
        assert not result.is_valid
        assert "Invalid source_type" in result.errors[0]

    def test_invalid_confidence(self):
        df = pd.DataFrame({
            "source_id": [1],
            "source_type": ["OFFICIAL_NTA"],
            "source_name": ["test"],
            "confidence": ["very_high"],
        })
        result = validate_data_sources(df)
        assert not result.is_valid


# ═══════════════════════════════════════════════════════════════
# Tests: marks_rank_points
# ═══════════════════════════════════════════════════════════════

class TestMarksRankValidation:

    def test_valid_data_passes(self):
        result = validate_marks_rank_points(_sample_marks_rank_valid(), _sample_sources())
        assert result.is_valid

    def test_marks_below_zero(self):
        df = _sample_marks_rank_valid().copy()
        df.loc[0, "marks_min"] = -5
        result = validate_marks_rank_points(df)
        assert not result.is_valid
        assert any("marks_min < 0" in e for e in result.errors)

    def test_marks_above_720(self):
        df = _sample_marks_rank_valid().copy()
        df.loc[0, "marks_max"] = 750
        result = validate_marks_rank_points(df)
        assert not result.is_valid
        assert any("marks_max > 720" in e for e in result.errors)

    def test_marks_min_greater_than_max(self):
        df = _sample_marks_rank_valid().copy()
        df.loc[0, "marks_min"] = 710
        df.loc[0, "marks_max"] = 700
        result = validate_marks_rank_points(df)
        assert not result.is_valid
        assert any("marks_min > marks_max" in e for e in result.errors)

    def test_rank_below_one(self):
        df = _sample_marks_rank_valid().copy()
        df.loc[0, "rank_min"] = 0
        result = validate_marks_rank_points(df)
        assert not result.is_valid
        assert any("rank_min < 1" in e for e in result.errors)

    def test_rank_min_greater_than_max(self):
        df = _sample_marks_rank_valid().copy()
        df.loc[0, "rank_min"] = 200
        df.loc[0, "rank_max"] = 100
        result = validate_marks_rank_points(df)
        assert not result.is_valid
        assert any("rank_min > rank_max" in e for e in result.errors)

    def test_null_source_id(self):
        df = _sample_marks_rank_valid().copy()
        df.loc[0, "source_id"] = None
        result = validate_marks_rank_points(df)
        assert not result.is_valid
        assert any("NULL source_id" in e for e in result.errors)

    def test_monotonicity_violation(self):
        df = _sample_marks_rank_bad_monotonicity()
        result = validate_marks_rank_points(df, _sample_sources())
        assert not result.is_valid
        assert any("monotonicity" in e.lower() for e in result.errors)

    def test_orphan_source_id(self):
        df = _sample_marks_rank_valid().copy()
        df["source_id"] = 999  # Doesn't exist in sources
        result = validate_marks_rank_points(df, _sample_sources())
        assert not result.is_valid
        assert any("not found in data_sources" in e for e in result.errors)


# ═══════════════════════════════════════════════════════════════
# Tests: allotments
# ═══════════════════════════════════════════════════════════════

class TestAllotmentsValidation:

    def _sample_allotments(self):
        return pd.DataFrame({
            "year": [2024, 2024],
            "round": ["R1", "R1"],
            "authority": ["MCC", "MCC"],
            "counselling_scope": ["AIQ", "AIQ"],
            "rank_raw": ["1.0", "2.0"],
            "air": [1, 2],
            "allotted_quota": ["Open Seat Quota", "Open Seat Quota"],
            "college_id": [1, 1],
            "college_raw": ["AIIMS New Delhi", "AIIMS New Delhi"],
            "course": ["MBBS", "MBBS"],
            "seat_category": ["Open", "Open"],
            "candidate_category": ["General", "OBC"],
            "source_id": [1, 1],
        })

    def test_valid_allotments(self):
        result = validate_allotments(self._sample_allotments())
        assert result.is_valid

    def test_air_below_one(self):
        df = self._sample_allotments()
        df.loc[0, "air"] = 0
        result = validate_allotments(df)
        assert not result.is_valid

    def test_invalid_year(self):
        df = self._sample_allotments()
        df.loc[0, "year"] = 2019
        result = validate_allotments(df)
        assert not result.is_valid

    def test_invalid_round(self):
        df = self._sample_allotments()
        df.loc[0, "round"] = "ROUND1"
        result = validate_allotments(df)
        assert not result.is_valid

    def test_invalid_course(self):
        df = self._sample_allotments()
        df.loc[0, "course"] = "AYUSH"
        result = validate_allotments(df)
        assert not result.is_valid

    def test_mcc_with_kea_category(self):
        """MCC records must NOT use KEA-only categories."""
        df = self._sample_allotments()
        df.loc[0, "seat_category"] = "2A"  # KEA-only category in MCC record
        result = validate_allotments(df)
        assert not result.is_valid
        assert any("KEA-only categories" in e for e in result.errors)

    def test_duplicate_air_in_same_round(self):
        """Same AIR in same round+quota should warn about multiple colleges."""
        df = self._sample_allotments()
        df.loc[1, "air"] = 1  # Same air as row 0
        df.loc[1, "college_id"] = 2  # But different college!
        result = validate_allotments(df)
        assert result.is_valid  # Downgraded to warning (legitimate across counselling pools)
        assert any("multiple colleges" in w for w in result.warnings)


# ═══════════════════════════════════════════════════════════════
# Tests: closing_ranks
# ═══════════════════════════════════════════════════════════════

class TestClosingRanksValidation:

    def _sample_closing(self):
        return pd.DataFrame({
            "year": [2024],
            "round": ["R1"],
            "authority": ["MCC"],
            "college_id": [1],
            "course": ["MBBS"],
            "quota": ["Open"],
            "category": ["Open"],
            "opening_rank": [1],
            "closing_rank": [100],
            "seats_total": [50],
            "seats_filled": [48],
            "derivation_method": ["derived_from_allotments"],
        })

    def test_valid_closing_ranks(self):
        result = validate_closing_ranks(self._sample_closing())
        assert result.is_valid

    def test_closing_less_than_opening(self):
        df = self._sample_closing()
        df.loc[0, "closing_rank"] = 0  # Less than opening_rank=1
        result = validate_closing_ranks(df)
        assert not result.is_valid

    def test_seats_filled_exceeds_total(self):
        df = self._sample_closing()
        df.loc[0, "seats_filled"] = 60  # More than seats_total=50
        result = validate_closing_ranks(df)
        assert not result.is_valid

    def test_null_derivation_method(self):
        df = self._sample_closing()
        df.loc[0, "derivation_method"] = None
        result = validate_closing_ranks(df)
        assert not result.is_valid


# ═══════════════════════════════════════════════════════════════
# Tests: colleges
# ═══════════════════════════════════════════════════════════════

class TestCollegesValidation:

    def _sample_colleges(self):
        return pd.DataFrame({
            "college_id": [1],
            "college_name": ["AIIMS New Delhi"],
            "name_normalized": ["aiims new delhi"],
            "state": ["Delhi"],
            "ownership": ["AIIMS"],
            "counselling": ["MCC"],
        })

    def test_valid_colleges(self):
        result = validate_colleges(self._sample_colleges())
        assert result.is_valid

    def test_invalid_ownership(self):
        df = self._sample_colleges()
        df.loc[0, "ownership"] = "unknown_type"
        result = validate_colleges(df)
        assert not result.is_valid

    def test_null_name(self):
        df = self._sample_colleges()
        df.loc[0, "college_name"] = ""
        result = validate_colleges(df)
        assert not result.is_valid


# ═══════════════════════════════════════════════════════════════
# Tests: exam_years
# ═══════════════════════════════════════════════════════════════

class TestExamYearsValidation:

    def test_valid(self):
        df = pd.DataFrame({
            "year": [2024],
            "appeared_candidates": [2400000],
        })
        result = validate_exam_years(df)
        assert result.is_valid

    def test_invalid_year(self):
        df = pd.DataFrame({
            "year": [2018],
            "appeared_candidates": [1000000],
        })
        result = validate_exam_years(df)
        assert not result.is_valid

    def test_zero_candidates(self):
        df = pd.DataFrame({
            "year": [2024],
            "appeared_candidates": [0],
        })
        result = validate_exam_years(df)
        assert not result.is_valid
