"""Derive closing ranks from parsed allotment data.

Usage:
    python -m pipelines.build_closing_ranks

Rules from BLUEPRINT.md:
- Closing rank = MAX(air) among VALID allotments per group
- INCLUDE: status = 'Allotted' (regardless of later reporting)
- EXCLUDE: 'Cancelled', 'Resigned', 'Seat Surrendered'
- 'Upgraded' counts for BOTH old and new college
- Round-specific: NEVER merge R1 and Mop-up closing ranks
"""

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from neet_predictor.config import CURATED_DIR

# Statuses to include for closing rank computation
INCLUDE_STATUSES = {"Allotted", "Upgraded"}
EXCLUDE_STATUSES = {"Cancelled", "Resigned", "Seat Surrendered", "Not Reported"}


def build_closing_ranks(allotments_df: pd.DataFrame, source_id: int = 1) -> pd.DataFrame:
    """Derive closing ranks from allotment records.

    Groups by (year, round, authority, counselling_scope, college_id, course,
    allotted_quota, seat_category, seat_type) and computes:
    - opening_rank: MIN(air) in group
    - closing_rank: MAX(air) in group
    - seats_filled: COUNT in group

    Args:
        allotments_df: DataFrame matching allotments schema.
        source_id: Source reference for derived data.

    Returns:
        DataFrame matching closing_ranks schema.
    """
    if allotments_df is None or allotments_df.empty:
        print("No allotment data available. Cannot derive closing ranks.")
        return pd.DataFrame()

    # Filter by valid statuses
    if "status" in allotments_df.columns:
        valid = allotments_df[
            allotments_df["status"].isin(INCLUDE_STATUSES)
            | allotments_df["status"].isna()  # Treat NULL status as valid (some PDFs don't have status)
        ]
        excluded_count = len(allotments_df) - len(valid)
        if excluded_count > 0:
            print(f"Excluded {excluded_count} rows with invalid statuses")
    else:
        valid = allotments_df

    if valid.empty:
        print("No valid allotment rows after status filtering.")
        return pd.DataFrame()

    # Require college_id to be resolved
    if "college_id" in valid.columns:
        unresolved = valid[valid["college_id"].isna()]
        if len(unresolved) > 0:
            print(f"WARNING: {len(unresolved)} rows with unresolved college_id — skipping these")
            valid = valid.dropna(subset=["college_id"])

    if valid.empty:
        return pd.DataFrame()

    # Group and aggregate
    # Use college_id if resolved, otherwise fall back to college_raw
    if "college_id" in valid.columns and valid["college_id"].notna().any():
        college_col = "college_id"
    elif "college_raw" in valid.columns:
        college_col = "college_raw"
    else:
        print("ERROR: No college identifier column found.")
        return pd.DataFrame()

    group_cols = ["year", "round", "authority", "counselling_scope", college_col, "course"]

    # Use seat_category as 'category' and allotted_quota as 'quota'
    if "seat_category" in valid.columns:
        group_cols.append("seat_category")
    if "allotted_quota" in valid.columns:
        group_cols.append("allotted_quota")
    if "seat_type" in valid.columns:
        group_cols.append("seat_type")

    agg = valid.groupby(group_cols, dropna=False).agg(
        opening_rank=("air", "min"),
        closing_rank=("air", "max"),
        seats_filled=("air", "count"),
    ).reset_index()

    # Rename to match closing_ranks schema
    rename_map = {}
    if "seat_category" in agg.columns:
        rename_map["seat_category"] = "category"
    if "allotted_quota" in agg.columns:
        rename_map["allotted_quota"] = "quota"
    if "college_raw" in agg.columns and "college_id" not in agg.columns:
        rename_map["college_raw"] = "college_id"  # Use raw name as ID until resolved
    agg = agg.rename(columns=rename_map)

    # Add metadata columns
    agg["derivation_method"] = "derived_from_allotments"
    agg["statuses_included"] = ",".join(sorted(INCLUDE_STATUSES))
    agg["source_id"] = source_id
    agg["seats_total"] = None
    agg["notes"] = "auto-derived from allotment records"

    print(f"Derived {len(agg)} closing rank entries")
    return agg


def main():
    allotments_path = CURATED_DIR / "allotments.csv"
    output_path = CURATED_DIR / "closing_ranks.csv"

    if not allotments_path.exists():
        print(f"ERROR: {allotments_path} not found. Parse allotment PDFs first.")
        sys.exit(1)

    df = pd.read_csv(allotments_path)
    if df.empty:
        print("ERROR: allotments.csv is empty. No data to derive closing ranks from.")
        sys.exit(1)

    closing = build_closing_ranks(df)
    if not closing.empty:
        closing.to_csv(output_path, index=False)
        print(f"Saved closing ranks to {output_path}")
    else:
        print("No closing ranks derived.")


if __name__ == "__main__":
    main()
