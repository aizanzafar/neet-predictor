"""Run all Phase 1A validators and produce a validation report.

Usage:
    python run_validators.py
"""

import sys
from pathlib import Path

_PROJECT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_PROJECT / "src"))

import pandas as pd

from neet_predictor.config import CURATED_DIR, SOURCES_DIR
from neet_predictor.dataio.validator import validate_all, ValidationResult


def load_csv_safe(path: Path) -> pd.DataFrame | None:
    """Load a CSV or return None if empty/missing."""
    if not path.exists():
        return None
    df = pd.read_csv(path)
    if df.empty or len(df) == 0:
        return None
    return df


def main():
    print("=" * 60)
    print("PHASE 1A VALIDATION REPORT")
    print("=" * 60)

    data = {}

    # Load all curated CSVs
    data["data_sources"] = load_csv_safe(SOURCES_DIR / "data_sources.csv")
    data["exam_years"] = load_csv_safe(CURATED_DIR / "exam_years.csv")
    data["marks_rank_points"] = load_csv_safe(CURATED_DIR / "marks_rank_points.csv")
    data["colleges"] = load_csv_safe(CURATED_DIR / "colleges.csv")
    data["allotments"] = load_csv_safe(CURATED_DIR / "allotments.csv")
    data["closing_ranks"] = load_csv_safe(CURATED_DIR / "closing_ranks.csv")

    # Show what we loaded
    print("\nData loaded:")
    for name, df in data.items():
        if df is not None:
            print(f"  {name}: {len(df)} rows")
        else:
            print(f"  {name}: NOT AVAILABLE")

    # Run validators
    print("\n" + "-" * 60)
    results = validate_all(data)

    # Show results
    pass_count = 0
    fail_count = 0
    for r in results:
        print(f"\n{r.summary()}")
        if r.is_valid:
            pass_count += 1
        else:
            fail_count += 1

    # Tables without data
    skipped = [name for name, df in data.items() if df is None]
    if skipped:
        print(f"\nSKIPPED (no data): {', '.join(skipped)}")

    # Gate checks
    print("\n" + "=" * 60)
    print("PHASE 1A GATE CHECKS")
    print("=" * 60)

    gates = {}

    # Gate 1: exam_years >= 5 years
    if data["exam_years"] is not None:
        years = len(data["exam_years"])
        gates["exam_years >= 5 years"] = years >= 5
        print(f"  exam_years >= 5 years: {'PASS' if years >= 5 else 'FAIL'} ({years} years)")
    else:
        gates["exam_years >= 5 years"] = False
        print(f"  exam_years >= 5 years: FAIL (no data)")

    # Gate 2: marks_rank_points >= 15 anchors/year for >= 3 years
    if data["marks_rank_points"] is not None:
        year_counts = data["marks_rank_points"].groupby("year").size()
        years_with_enough = (year_counts >= 15).sum()
        gates["marks_rank >= 15 anchors/yr for >= 3 yrs"] = years_with_enough >= 3
        print(f"  marks_rank >= 15 anchors/yr for >= 3 yrs: "
              f"{'PASS' if years_with_enough >= 3 else 'FAIL'} ({years_with_enough} years)")
    else:
        gates["marks_rank >= 15 anchors/yr for >= 3 yrs"] = False
        print(f"  marks_rank >= 15 anchors/yr for >= 3 yrs: FAIL (no data)")

    # Gate 3: closing_ranks >= 500 rows
    if data["closing_ranks"] is not None:
        cr_rows = len(data["closing_ranks"])
        gates["closing_ranks >= 500 rows"] = cr_rows >= 500
        print(f"  closing_ranks >= 500 rows: {'PASS' if cr_rows >= 500 else 'FAIL'} ({cr_rows} rows)")
    else:
        gates["closing_ranks >= 500 rows"] = False
        print(f"  closing_ranks >= 500 rows: FAIL (no data)")

    # Gate 4: zero unresolved colleges
    if data["allotments"] is not None and "college_id" in data["allotments"].columns:
        unresolved = data["allotments"]["college_id"].isna().sum()
        gates["zero unresolved colleges"] = unresolved == 0
        print(f"  zero unresolved colleges: {'PASS' if unresolved == 0 else 'FAIL'} ({unresolved} unresolved)")
    else:
        gates["zero unresolved colleges"] = False
        print(f"  zero unresolved colleges: FAIL (no allotment data)")

    # Gate 5: all source_id FKs resolve
    if data["data_sources"] is not None:
        valid_ids = set(data["data_sources"]["source_id"])
        fk_ok = True
        for name in ["allotments", "marks_rank_points", "closing_ranks"]:
            if data.get(name) is not None and "source_id" in data[name].columns:
                used = set(data[name]["source_id"].dropna().astype(int))
                orphans = used - valid_ids
                if orphans:
                    fk_ok = False
                    print(f"  source_id FK ({name}): FAIL — orphan IDs: {orphans}")
        gates["all source_id FKs resolve"] = fk_ok
        if fk_ok:
            print(f"  all source_id FKs resolve: PASS")
    else:
        gates["all source_id FKs resolve"] = False
        print(f"  all source_id FKs resolve: FAIL (no data_sources)")

    # Gate 6: all tests pass
    gates["all tests pass"] = pass_count > 0 and fail_count == 0
    print(f"  all validation tests pass: {'PASS' if gates['all tests pass'] else 'FAIL'} "
          f"({pass_count} pass, {fail_count} fail)")

    # Overall
    all_gates_pass = all(gates.values())
    print(f"\n{'=' * 60}")
    print(f"OVERALL GATE STATUS: {'ALL GATES PASS' if all_gates_pass else 'GATES NOT MET'}")
    print(f"{'=' * 60}")

    return results, gates


if __name__ == "__main__":
    main()
