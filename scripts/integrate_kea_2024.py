"""One-shot script to integrate all KEA 2024 data into curated closing_ranks.csv.

Combines:
- R1+R2 official cutoffs (from cutoff PDFs) -> derivation_method = 'official_published'
- MOPUP/Stray closing ranks (derived from allotment lists) -> 'derived_from_allotments'

Replaces ALL existing KEA 2024 data.
"""

import sys
from pathlib import Path

_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_root / "src"))
sys.path.insert(0, str(_root))

import pandas as pd

from neet_predictor.config import CURATED_DIR
from scripts.integrate_kea_cutoffs import build_kea_code_to_college_id, convert_to_curated_schema


def main():
    aliases_df = pd.read_csv(CURATED_DIR / "college_aliases.csv")
    source_ids = {"default": 61}

    # ===== R1 + R2 OFFICIAL CUTOFFS =====
    official_df = pd.read_csv("data/parsed/kea_cutoffs/kea_2024_closing_ranks.csv")
    mapping, unmatched = build_kea_code_to_college_id(official_df, aliases_df)
    print(f"R1+R2 Official: {len(official_df)} entries, {len(mapping)} colleges mapped")
    if unmatched:
        print(f"  Unmatched ({len(unmatched)}):")
        for code, name in unmatched[:10]:
            print(f"    {code}: {name}")

    official_curated = convert_to_curated_schema(official_df, mapping, 2024, source_ids)
    print(f"  -> {len(official_curated)} curated rows")

    # ===== MOPUP/STRAY DERIVED FROM ALLOTMENTS =====
    derived_df = pd.read_csv("data/parsed/kea_cutoffs/kea_2024_derived_closing_ranks.csv")
    # Only keep MOPUP and STRAY (R2 dental already covered by official cutoffs)
    derived_df = derived_df[derived_df["round"].isin(["MOPUP", "STRAY"])].copy()
    print(f"MOPUP/Stray derived: {len(derived_df)} entries")

    # Derived entries don't have college_name, so build mapping from official data
    mapping2, unmatched2 = build_kea_code_to_college_id(derived_df, aliases_df)
    # For derived entries without names, use mapping from official
    combined_mapping = {**mapping2, **mapping}

    derived_curated = convert_to_curated_schema(derived_df, combined_mapping, 2024, source_ids)
    derived_curated["derivation_method"] = "derived_from_allotments"
    derived_curated["notes"] = "KEA allotment list 2024"
    print(f"  -> {len(derived_curated)} curated rows")

    # ===== COMBINE =====
    combined_new = pd.concat([official_curated, derived_curated], ignore_index=True)
    print(f"\nTotal new: {len(combined_new)} rows")
    print(f"  R1+R2 official_published: {len(official_curated)}")
    print(f"  MOPUP/Stray derived: {len(derived_curated)}")
    rounds = combined_new["round"].value_counts().to_dict()
    print(f"  By round: {rounds}")

    # ===== LOAD EXISTING AND REPLACE =====
    curated_path = CURATED_DIR / "closing_ranks.csv"
    existing = pd.read_csv(curated_path, dtype={"quota": str, "statuses_included": str})
    print(f"\nExisting total: {len(existing)}")

    # Remove ALL KEA 2024
    mask = ~((existing["year"] == 2024) & (existing["authority"] == "KEA"))
    cleaned = existing[mask].copy()
    removed = len(existing) - len(cleaned)
    print(f"Removed {removed} existing KEA 2024 rows")

    # Append new
    final = pd.concat([cleaned, combined_new], ignore_index=True)
    final.to_csv(curated_path, index=False)
    print(f"Final: {len(final)} rows (was {len(existing)})")
    print(f"Net change: {len(final) - len(existing):+d} rows")

    # Summary stats
    kea_2024 = final[(final["year"] == 2024) & (final["authority"] == "KEA")]
    print(f"\nKEA 2024 summary:")
    print(f"  Total rows: {len(kea_2024)}")
    print(f"  Colleges: {kea_2024['college_id'].nunique()}")
    print(f"  Rounds: {sorted(kea_2024['round'].unique())}")
    print(f"  Methods: {kea_2024['derivation_method'].value_counts().to_dict()}")


if __name__ == "__main__":
    main()
