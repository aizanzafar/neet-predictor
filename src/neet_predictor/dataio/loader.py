"""Load curated CSV files into pandas DataFrames or SQLite."""

from pathlib import Path
from typing import Optional

import pandas as pd

from neet_predictor.config import CURATED_DIR, SOURCES_DIR


# ── CSV file definitions ──
CURATED_FILES = {
    "exam_years": CURATED_DIR / "exam_years.csv",
    "marks_rank_points": CURATED_DIR / "marks_rank_points.csv",
    "colleges": CURATED_DIR / "colleges.csv",
    "allotments": CURATED_DIR / "allotments.csv",
    "closing_ranks": CURATED_DIR / "closing_ranks.csv",
    "seat_matrix": CURATED_DIR / "seat_matrix.csv",
    "college_aliases": CURATED_DIR / "college_aliases.csv",
}

SOURCE_FILE = SOURCES_DIR / "data_sources.csv"


class DataNotFoundError(Exception):
    """Raised when a required data file does not exist."""
    pass


class InsufficientDataError(Exception):
    """Raised when data exists but doesn't meet minimum thresholds."""
    pass


def load_csv(path: Path, required: bool = True) -> Optional[pd.DataFrame]:
    """Load a CSV file into a DataFrame.

    Args:
        path: Path to the CSV file.
        required: If True, raise DataNotFoundError when file is missing.

    Returns:
        DataFrame or None if not required and missing.
    """
    if not path.exists():
        if required:
            raise DataNotFoundError(
                f"Required data file not found: {path}\n"
                f"This file must be populated before prediction can run."
            )
        return None
    df = pd.read_csv(path)
    if df.empty:
        if required:
            raise DataNotFoundError(
                f"Data file exists but is empty: {path}\n"
                f"Populate this file with real data."
            )
        return None
    return df


def load_data_sources() -> Optional[pd.DataFrame]:
    """Load the data sources provenance registry."""
    return load_csv(SOURCE_FILE, required=False)


def load_exam_years() -> Optional[pd.DataFrame]:
    """Load exam year statistics."""
    return load_csv(CURATED_FILES["exam_years"], required=False)


def load_marks_rank_points() -> Optional[pd.DataFrame]:
    """Load marks-to-rank anchor points."""
    return load_csv(CURATED_FILES["marks_rank_points"], required=False)


def load_colleges() -> Optional[pd.DataFrame]:
    """Load college master table."""
    return load_csv(CURATED_FILES["colleges"], required=False)


def load_allotments() -> Optional[pd.DataFrame]:
    """Load allotment records."""
    return load_csv(CURATED_FILES["allotments"], required=False)


def load_closing_ranks() -> Optional[pd.DataFrame]:
    """Load closing rank records."""
    path = CURATED_FILES["closing_ranks"]
    if not path.exists():
        return None
    df = pd.read_csv(path, dtype={"quota": str, "statuses_included": str})
    return df if not df.empty else None


def check_data_availability() -> dict:
    """Check which data files exist and their row counts.

    Returns:
        Dict of {table_name: {"exists": bool, "rows": int|None, "path": str}}
    """
    report = {}
    all_files = {**CURATED_FILES, "data_sources": SOURCE_FILE}

    for name, path in all_files.items():
        entry = {"path": str(path), "exists": path.exists(), "rows": None}
        if entry["exists"]:
            try:
                df = pd.read_csv(path)
                entry["rows"] = len(df)
            except Exception:
                entry["rows"] = 0
        report[name] = entry
    return report
