"""Data validation implementing all hard rules from BLUEPRINT.md Part C5.

All data must pass these checks at load time. Fail loudly, never silently accept bad data.
"""

from dataclasses import dataclass, field
from typing import Optional

import pandas as pd

from neet_predictor.config import (
    KEA_CATEGORIES,
    MAX_MARKS,
    MAX_YEAR,
    MCC_CATEGORIES,
    MIN_MARKS,
    MIN_YEAR,
    VALID_AUTHORITIES,
    VALID_CONFIDENCE,
    VALID_COURSES,
    VALID_DERIVATION_METHODS,
    VALID_OWNERSHIP,
    VALID_ROUNDS,
    VALID_SOURCE_TYPES,
)


@dataclass
class ValidationResult:
    """Result of a validation run."""

    table_name: str
    total_rows: int = 0
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def is_valid(self) -> bool:
        return len(self.errors) == 0

    def summary(self) -> str:
        status = "PASS" if self.is_valid else "FAIL"
        lines = [f"[{status}] {self.table_name}: {self.total_rows} rows"]
        for e in self.errors:
            lines.append(f"  ERROR: {e}")
        for w in self.warnings:
            lines.append(f"  WARN:  {w}")
        return "\n".join(lines)


# ═══════════════════════════════════════════════════════════════
# Data Sources validation
# ═══════════════════════════════════════════════════════════════

def validate_data_sources(df: pd.DataFrame) -> ValidationResult:
    """Validate the data_sources table."""
    result = ValidationResult(table_name="data_sources", total_rows=len(df))

    # Required columns
    required_cols = {"source_id", "source_type", "source_name", "confidence"}
    missing = required_cols - set(df.columns)
    if missing:
        result.errors.append(f"Missing required columns: {missing}")
        return result

    # source_type enum
    invalid_types = df[~df["source_type"].isin(VALID_SOURCE_TYPES)]
    if len(invalid_types) > 0:
        bad = invalid_types["source_type"].unique().tolist()
        result.errors.append(f"Invalid source_type values: {bad}")

    # confidence enum
    invalid_conf = df[~df["confidence"].isin(VALID_CONFIDENCE)]
    if len(invalid_conf) > 0:
        bad = invalid_conf["confidence"].unique().tolist()
        result.errors.append(f"Invalid confidence values: {bad}")

    return result


# ═══════════════════════════════════════════════════════════════
# Marks-to-Rank validation
# ═══════════════════════════════════════════════════════════════

def validate_marks_rank_points(df: pd.DataFrame, sources_df: Optional[pd.DataFrame] = None) -> ValidationResult:
    """Validate marks_rank_points against all C5 rules."""
    result = ValidationResult(table_name="marks_rank_points", total_rows=len(df))

    required_cols = {"year", "marks_min", "marks_max", "rank_min", "rank_max", "source_id", "confidence"}
    missing = required_cols - set(df.columns)
    if missing:
        result.errors.append(f"Missing required columns: {missing}")
        return result

    # marks_min >= 0 AND marks_max <= 720
    bad_marks_low = df[df["marks_min"] < MIN_MARKS]
    if len(bad_marks_low) > 0:
        result.errors.append(f"{len(bad_marks_low)} rows have marks_min < {MIN_MARKS}")

    bad_marks_high = df[df["marks_max"] > MAX_MARKS]
    if len(bad_marks_high) > 0:
        result.errors.append(f"{len(bad_marks_high)} rows have marks_max > {MAX_MARKS}")

    # marks_min <= marks_max
    bad_order = df[df["marks_min"] > df["marks_max"]]
    if len(bad_order) > 0:
        result.errors.append(f"{len(bad_order)} rows have marks_min > marks_max")

    # rank_min >= 1
    bad_rank = df[df["rank_min"] < 1]
    if len(bad_rank) > 0:
        result.errors.append(f"{len(bad_rank)} rows have rank_min < 1")

    # rank_min <= rank_max
    bad_rank_order = df[df["rank_min"] > df["rank_max"]]
    if len(bad_rank_order) > 0:
        result.errors.append(f"{len(bad_rank_order)} rows have rank_min > rank_max")

    # source_id IS NOT NULL
    null_source = df[df["source_id"].isna()]
    if len(null_source) > 0:
        result.errors.append(f"{len(null_source)} rows have NULL source_id (no provenance)")

    # confidence enum
    if "confidence" in df.columns:
        invalid_conf = df[~df["confidence"].isin(VALID_CONFIDENCE)]
        if len(invalid_conf) > 0:
            result.errors.append(f"{len(invalid_conf)} rows have invalid confidence values")

    # Monotonicity check per year:
    # If row A has marks_min > row B's marks_max, then A's rank_max must be <= B's rank_min
    for year, group in df.groupby("year"):
        sorted_group = group.sort_values("marks_min", ascending=False).reset_index(drop=True)
        violations = []
        for i in range(len(sorted_group) - 1):
            row_a = sorted_group.iloc[i]
            row_b = sorted_group.iloc[i + 1]
            if row_a["marks_min"] > row_b["marks_max"]:
                if row_a["rank_max"] > row_b["rank_min"]:
                    violations.append(
                        f"marks {row_a['marks_min']}–{row_a['marks_max']} → rank {row_a['rank_min']}–{row_a['rank_max']} "
                        f"vs marks {row_b['marks_min']}–{row_b['marks_max']} → rank {row_b['rank_min']}–{row_b['rank_max']}"
                    )
        if violations:
            result.errors.append(
                f"Year {year}: {len(violations)} monotonicity violation(s). "
                f"Higher marks must imply better (lower) rank. First: {violations[0]}"
            )

    # Cross-table: source_id must exist in data_sources
    if sources_df is not None and "source_id" in df.columns:
        valid_ids = set(sources_df["source_id"].dropna().astype(int))
        used_ids = set(df["source_id"].dropna().astype(int))
        orphans = used_ids - valid_ids
        if orphans:
            result.errors.append(f"source_id values not found in data_sources: {orphans}")

    return result


# ═══════════════════════════════════════════════════════════════
# Allotment validation
# ═══════════════════════════════════════════════════════════════

def validate_allotments(df: pd.DataFrame, colleges_df: Optional[pd.DataFrame] = None, sources_df: Optional[pd.DataFrame] = None) -> ValidationResult:
    """Validate allotment records against all C5 rules."""
    result = ValidationResult(table_name="allotments", total_rows=len(df))

    required_cols = {"year", "round", "authority", "counselling_scope", "rank_raw", "air", "course", "seat_category", "allotted_quota"}
    missing = required_cols - set(df.columns)
    if missing:
        result.errors.append(f"Missing required columns: {missing}")
        return result

    # air >= 1
    bad_air = df[df["air"] < 1]
    if len(bad_air) > 0:
        result.errors.append(f"{len(bad_air)} rows have air < 1")

    # year BETWEEN 2020 AND 2025
    bad_year = df[(df["year"] < MIN_YEAR) | (df["year"] > MAX_YEAR)]
    if len(bad_year) > 0:
        result.errors.append(f"{len(bad_year)} rows have year outside {MIN_YEAR}–{MAX_YEAR}")

    # round IN valid set
    invalid_round = df[~df["round"].isin(VALID_ROUNDS)]
    if len(invalid_round) > 0:
        bad = invalid_round["round"].unique().tolist()
        result.errors.append(f"Invalid round values: {bad}")

    # course IN valid set
    invalid_course = df[~df["course"].isin(VALID_COURSES)]
    if len(invalid_course) > 0:
        bad = invalid_course["course"].unique().tolist()
        result.errors.append(f"Invalid course values: {bad}")

    # authority IN valid set
    invalid_auth = df[~df["authority"].isin(VALID_AUTHORITIES)]
    if len(invalid_auth) > 0:
        bad = invalid_auth["authority"].unique().tolist()
        result.errors.append(f"Invalid authority values: {bad}")

    # Per (year, round, authority, allotted_quota): same air should map to at most ONE college
    # Note: same AIR can legitimately appear in different counselling pools (AIIMS/JIPMER/Central)
    if "college_id" in df.columns:
        group_cols = ["year", "round", "authority", "air"]
        if "allotted_quota" in df.columns:
            group_cols.append("allotted_quota")
        dup_check = df.dropna(subset=["college_id"]).groupby(
            group_cols
        )["college_id"].nunique()
        duplicates = dup_check[dup_check > 1]
        if len(duplicates) > 0:
            result.warnings.append(
                f"{len(duplicates)} (year, round, authority, quota, air) groups map to multiple colleges"
            )

    # Authority-category consistency
    _check_category_consistency(df, result)

    # college_id not null after normalization
    if "college_id" in df.columns:
        null_college = df[df["college_id"].isna()]
        if len(null_college) > 0:
            result.warnings.append(
                f"{len(null_college)} rows have NULL college_id (unresolved college names)"
            )

    # Cross-table checks
    if colleges_df is not None and "college_id" in df.columns:
        valid_ids = set(colleges_df["college_id"].dropna().astype(int))
        used_ids = set(df["college_id"].dropna().astype(int))
        orphans = used_ids - valid_ids
        if orphans:
            result.errors.append(f"college_id values not in colleges table: {sorted(list(orphans))[:10]}...")

    if sources_df is not None and "source_id" in df.columns:
        valid_ids = set(sources_df["source_id"].dropna().astype(int))
        used_ids = set(df["source_id"].dropna().astype(int))
        orphans = used_ids - valid_ids
        if orphans:
            result.errors.append(f"source_id values not in data_sources: {orphans}")

    return result


def _check_category_consistency(df: pd.DataFrame, result: ValidationResult) -> None:
    """Check that MCC records don't use KEA categories and vice versa."""
    if "authority" not in df.columns or "seat_category" not in df.columns:
        return

    mcc_rows = df[df["authority"] == "MCC"]
    kea_rows = df[df["authority"] == "KEA"]

    # MCC records should NOT use KEA-only categories
    if len(mcc_rows) > 0:
        kea_only_in_mcc = mcc_rows[mcc_rows["seat_category"].isin(KEA_CATEGORIES - MCC_CATEGORIES)]
        if len(kea_only_in_mcc) > 0:
            bad_cats = kea_only_in_mcc["seat_category"].unique().tolist()
            result.errors.append(
                f"MCC records using KEA-only categories: {bad_cats} ({len(kea_only_in_mcc)} rows)"
            )

    # KEA records should NOT use MCC-only categories (unless mapped)
    if len(kea_rows) > 0:
        mcc_only_in_kea = kea_rows[kea_rows["seat_category"].isin(MCC_CATEGORIES - KEA_CATEGORIES)]
        if len(mcc_only_in_kea) > 0:
            bad_cats = mcc_only_in_kea["seat_category"].unique().tolist()
            result.warnings.append(
                f"KEA records using MCC-only categories (may need mapping): {bad_cats} ({len(mcc_only_in_kea)} rows)"
            )


# ═══════════════════════════════════════════════════════════════
# Closing Ranks validation
# ═══════════════════════════════════════════════════════════════

def validate_closing_ranks(df: pd.DataFrame, colleges_df: Optional[pd.DataFrame] = None) -> ValidationResult:
    """Validate closing_ranks table."""
    result = ValidationResult(table_name="closing_ranks", total_rows=len(df))

    required_cols = {"year", "round", "authority", "college_id", "course", "quota", "category", "closing_rank"}
    missing = required_cols - set(df.columns)
    if missing:
        result.errors.append(f"Missing required columns: {missing}")
        return result

    # closing_rank >= opening_rank
    if "opening_rank" in df.columns:
        has_both = df[df["opening_rank"].notna()]
        bad_order = has_both[has_both["closing_rank"] < has_both["opening_rank"]]
        if len(bad_order) > 0:
            result.errors.append(f"{len(bad_order)} rows have closing_rank < opening_rank")

    # seats_filled <= seats_total
    if "seats_filled" in df.columns and "seats_total" in df.columns:
        has_both = df[df["seats_filled"].notna() & df["seats_total"].notna()]
        bad_seats = has_both[has_both["seats_filled"] > has_both["seats_total"]]
        if len(bad_seats) > 0:
            result.errors.append(f"{len(bad_seats)} rows have seats_filled > seats_total")

    # derivation_method IS NOT NULL
    if "derivation_method" in df.columns:
        null_method = df[df["derivation_method"].isna()]
        if len(null_method) > 0:
            result.errors.append(f"{len(null_method)} rows have NULL derivation_method")
    else:
        result.errors.append("Missing derivation_method column")

    # Cross-table: college_id
    if colleges_df is not None and "college_id" in df.columns:
        valid_ids = set(colleges_df["college_id"].dropna().astype(int))
        used_ids = set(df["college_id"].dropna().astype(int))
        orphans = used_ids - valid_ids
        if orphans:
            result.errors.append(f"college_id values not in colleges table: {sorted(list(orphans))[:10]}")

    return result


# ═══════════════════════════════════════════════════════════════
# Colleges validation
# ═══════════════════════════════════════════════════════════════

def validate_colleges(df: pd.DataFrame) -> ValidationResult:
    """Validate colleges master table."""
    result = ValidationResult(table_name="colleges", total_rows=len(df))

    required_cols = {"college_id", "college_name", "name_normalized", "state", "ownership", "counselling"}
    missing = required_cols - set(df.columns)
    if missing:
        result.errors.append(f"Missing required columns: {missing}")
        return result

    # college_name IS NOT NULL
    null_name = df[df["college_name"].isna() | (df["college_name"].str.strip() == "")]
    if len(null_name) > 0:
        result.errors.append(f"{len(null_name)} rows have NULL/empty college_name")

    # name_normalized IS NOT NULL
    null_norm = df[df["name_normalized"].isna() | (df["name_normalized"].str.strip() == "")]
    if len(null_norm) > 0:
        result.errors.append(f"{len(null_norm)} rows have NULL/empty name_normalized")

    # state IS NOT NULL
    null_state = df[df["state"].isna()]
    if len(null_state) > 0:
        result.errors.append(f"{len(null_state)} rows have NULL state")

    # ownership enum
    invalid_ownership = df[~df["ownership"].isin(VALID_OWNERSHIP)]
    if len(invalid_ownership) > 0:
        bad = invalid_ownership["ownership"].unique().tolist()
        result.errors.append(f"Invalid ownership values: {bad}")

    return result


# ═══════════════════════════════════════════════════════════════
# Exam Years validation
# ═══════════════════════════════════════════════════════════════

def validate_exam_years(df: pd.DataFrame) -> ValidationResult:
    """Validate exam_years table."""
    result = ValidationResult(table_name="exam_years", total_rows=len(df))

    required_cols = {"year", "appeared_candidates"}
    missing = required_cols - set(df.columns)
    if missing:
        result.errors.append(f"Missing required columns: {missing}")
        return result

    # year range
    bad_year = df[(df["year"] < MIN_YEAR) | (df["year"] > MAX_YEAR)]
    if len(bad_year) > 0:
        result.errors.append(f"Years outside {MIN_YEAR}–{MAX_YEAR}: {bad_year['year'].tolist()}")

    # appeared_candidates > 0
    bad_count = df[df["appeared_candidates"] <= 0]
    if len(bad_count) > 0:
        result.errors.append(f"{len(bad_count)} rows have appeared_candidates <= 0")

    return result


# ═══════════════════════════════════════════════════════════════
# Run all validations
# ═══════════════════════════════════════════════════════════════

def validate_all(data: dict[str, pd.DataFrame]) -> list[ValidationResult]:
    """Run all validators on a dict of DataFrames.

    Args:
        data: Dict with keys like 'marks_rank_points', 'allotments', etc.

    Returns:
        List of ValidationResult objects.
    """
    results = []
    sources_df = data.get("data_sources")
    colleges_df = data.get("colleges")

    if "data_sources" in data and data["data_sources"] is not None:
        results.append(validate_data_sources(data["data_sources"]))

    if "exam_years" in data and data["exam_years"] is not None:
        results.append(validate_exam_years(data["exam_years"]))

    if "marks_rank_points" in data and data["marks_rank_points"] is not None:
        results.append(validate_marks_rank_points(data["marks_rank_points"], sources_df))

    if "colleges" in data and data["colleges"] is not None:
        results.append(validate_colleges(data["colleges"]))

    if "allotments" in data and data["allotments"] is not None:
        results.append(validate_allotments(data["allotments"], colleges_df, sources_df))

    if "closing_ranks" in data and data["closing_ranks"] is not None:
        results.append(validate_closing_ranks(data["closing_ranks"], colleges_df))

    return results
