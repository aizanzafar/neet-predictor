"""Build all curated CSVs from parsed allotment data.

Steps:
1. Merge all parsed CSVs → allotments.csv
2. Build college master → colleges.csv + college_aliases.csv
3. Map college_raw → college_id in allotments (update allotments.csv)
4. Derive closing_ranks.csv from allotments

Usage:
    python -m pipelines.build_curated
"""

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from neet_predictor.config import CURATED_DIR, PARSED_MCC_DIR, PARSED_KEA_DIR
from pipelines.build_college_master import build_college_master
from pipelines.build_closing_ranks import build_closing_ranks


def merge_parsed_csvs() -> pd.DataFrame:
    """Merge all parsed MCC + KEA CSVs into a single allotments DataFrame."""
    mcc_files = sorted(PARSED_MCC_DIR.glob("mcc_*.csv"))
    kea_files = sorted(PARSED_KEA_DIR.glob("kea_*.csv"))
    all_files = mcc_files + kea_files

    if not all_files:
        print("ERROR: No parsed CSV files found.")
        return pd.DataFrame()

    print(f"Merging {len(mcc_files)} MCC + {len(kea_files)} KEA parsed files...")

    dfs = []
    for f in all_files:
        df = pd.read_csv(f)
        # Skip summary/metadata files
        if df.empty or "air" not in df.columns:
            continue
        dfs.append(df)
        print(f"  {f.name}: {len(df)} rows")

    if not dfs:
        return pd.DataFrame()

    merged = pd.concat(dfs, ignore_index=True)

    # Add allotment_id
    merged.insert(0, "allotment_id", range(1, len(merged) + 1))

    # Ensure schema columns exist (add missing ones as empty)
    schema_cols = [
        "allotment_id", "year", "round", "authority", "counselling_scope",
        "rank_raw", "air", "rank_type", "allotted_quota", "college_id",
        "college_raw", "course", "seat_category", "candidate_category",
        "seat_type", "fee", "status", "source_id", "notes",
    ]
    for col in schema_cols:
        if col not in merged.columns:
            merged[col] = None

    # Reorder to schema
    merged = merged[[c for c in schema_cols if c in merged.columns]]

    print(f"Total merged: {len(merged)} rows")
    return merged


def main():
    CURATED_DIR.mkdir(parents=True, exist_ok=True)

    # Step 1: Merge parsed CSVs
    print("=" * 60)
    print("STEP 1: Merge parsed CSVs → allotments.csv")
    print("=" * 60)
    allotments = merge_parsed_csvs()
    if allotments.empty:
        print("FATAL: No data to work with.")
        sys.exit(1)

    # Step 2: Build college master
    print("\n" + "=" * 60)
    print("STEP 2: Build college master → colleges.csv + college_aliases.csv")
    print("=" * 60)
    colleges, aliases = build_college_master(allotments)

    if not colleges.empty:
        colleges.to_csv(CURATED_DIR / "colleges.csv", index=False)
        print(f"Saved colleges.csv ({len(colleges)} rows)")

    if not aliases.empty:
        aliases.to_csv(CURATED_DIR / "college_aliases.csv", index=False)
        print(f"Saved college_aliases.csv ({len(aliases)} rows)")

    # Step 3: Map college_raw → college_id in allotments
    print("\n" + "=" * 60)
    print("STEP 3: Resolve college_id in allotments")
    print("=" * 60)
    if not aliases.empty:
        from neet_predictor.dataio.normalizer import normalize_college_name
        # Build lookup: normalized name → college_id
        norm_to_id = dict(zip(aliases["alias_normalized"], aliases["college_id"]))
        allotments["_norm"] = allotments["college_raw"].apply(normalize_college_name)
        allotments["college_id"] = allotments["_norm"].map(norm_to_id)
        allotments.drop(columns=["_norm"], inplace=True)

        resolved = allotments["college_id"].notna().sum()
        unresolved = allotments["college_id"].isna().sum()
        print(f"Resolved: {resolved}, Unresolved: {unresolved}")
    else:
        print("WARNING: No college aliases — college_id will be NULL.")

    # Save allotments
    allotments.to_csv(CURATED_DIR / "allotments.csv", index=False)
    print(f"Saved allotments.csv ({len(allotments)} rows)")

    # Step 4: Derive closing ranks
    print("\n" + "=" * 60)
    print("STEP 4: Derive closing_ranks.csv")
    print("=" * 60)
    closing = build_closing_ranks(allotments)
    if not closing.empty:
        closing.to_csv(CURATED_DIR / "closing_ranks.csv", index=False)
        print(f"Saved closing_ranks.csv ({len(closing)} rows)")
    else:
        print("WARNING: No closing ranks derived.")

    # Summary
    print("\n" + "=" * 60)
    print("CURATED DATA SUMMARY")
    print("=" * 60)
    for name in ["allotments", "colleges", "college_aliases", "closing_ranks"]:
        path = CURATED_DIR / f"{name}.csv"
        if path.exists():
            df = pd.read_csv(path)
            print(f"  {name}.csv: {len(df)} rows")
        else:
            print(f"  {name}.csv: NOT FOUND")


if __name__ == "__main__":
    main()
