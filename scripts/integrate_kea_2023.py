"""One-shot script to integrate all KEA 2023 data into curated closing_ranks.csv.

Combines:
- R1 official cutoffs (from cutoff PDFs) -> derivation_method = 'official_published'
- R2/Mopup/Stray closing ranks (derived from allotment lists) -> 'derived_from_allotments'

Replaces ALL existing KEA 2023 data.
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

    # ===== R1 OFFICIAL CUTOFFS =====
    r1_df = pd.read_csv("data/parsed/kea_cutoffs/kea_2023_closing_ranks.csv")
    mapping, unmatched = build_kea_code_to_college_id(r1_df, aliases_df)
    print(f"R1 Official: {len(r1_df)} entries, {len(mapping)} colleges mapped")

    r1_curated = convert_to_curated_schema(r1_df, mapping, 2023, source_ids)
    print(f"  -> {len(r1_curated)} curated rows")

    # ===== R2/MOPUP/STRAY DERIVED FROM ALLOTMENTS =====
    r2_df = pd.read_csv("data/parsed/kea_cutoffs/kea_2023_derived_closing_ranks.csv")
    mapping2, unmatched2 = build_kea_code_to_college_id(r2_df, aliases_df)
    print(f"R2/Mopup derived: {len(r2_df)} entries, {len(mapping2)} mapped, {len(unmatched2)} unmatched")
    if unmatched2:
        for code, name in unmatched2[:5]:
            print(f"    UNMATCHED: {code} - {name}")

    r2_curated = convert_to_curated_schema(r2_df, mapping2, 2023, source_ids)
    r2_curated["derivation_method"] = "derived_from_allotments"
    r2_curated["notes"] = "KEA allotment list 2023"
    print(f"  -> {len(r2_curated)} curated rows")

    # ===== COMBINE =====
    combined_new = pd.concat([r1_curated, r2_curated], ignore_index=True)
    print(f"\nTotal new: {len(combined_new)} rows")
    print(f"  R1 official_published: {len(r1_curated)}")
    print(f"  R2/Mopup/Stray derived: {len(r2_curated)}")
    rounds = combined_new["round"].value_counts().to_dict()
    print(f"  By round: {rounds}")

    # ===== LOAD EXISTING AND REPLACE =====
    curated_path = CURATED_DIR / "closing_ranks.csv"
    existing = pd.read_csv(curated_path, dtype={"quota": str, "statuses_included": str})
    print(f"\nExisting total: {len(existing)}")

    # Remove ALL KEA 2023
    mask = ~((existing["year"] == 2023) & (existing["authority"] == "KEA"))
    cleaned = existing[mask].copy()
    removed = len(existing) - len(cleaned)
    print(f"Removed {removed} existing KEA 2023 rows")

    # Append new
    final = pd.concat([cleaned, combined_new], ignore_index=True)
    final.to_csv(curated_path, index=False)
    print(f"Final: {len(final)} rows (was {len(existing)})")
    print(f"Net change: {len(final) - len(existing):+d} rows")


if __name__ == "__main__":
    main()
