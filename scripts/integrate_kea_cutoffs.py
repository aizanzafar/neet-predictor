"""Integrate parsed KEA cutoff data into curated closing_ranks.csv.

Maps KEA college codes (M001, D661, etc.) to college_id using name matching
against the college_aliases table, then outputs in the curated schema.

Usage:
    python scripts/integrate_kea_cutoffs.py --year 2020
    python scripts/integrate_kea_cutoffs.py --year 2021
    python scripts/integrate_kea_cutoffs.py --year 2020 --year 2021 --commit
"""

import argparse
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from neet_predictor.config import CURATED_DIR
from neet_predictor.dataio.normalizer import normalize_college_name


def build_kea_code_to_college_id(kea_df: pd.DataFrame, aliases_df: pd.DataFrame) -> dict[str, int]:
    """Build mapping from KEA code (M001) to curated college_id.
    
    Strategy: 
    1. Normalize KEA college_name from cutoff data
    2. Normalize alias_name from college_aliases (authority=KEA)
    3. Match by normalized name similarity
    """
    kea_aliases = aliases_df[aliases_df["authority"] == "KEA"].copy()
    kea_aliases["name_norm"] = kea_aliases["alias_name"].apply(
        lambda x: normalize_college_name(str(x)) if pd.notna(x) else ""
    )
    
    # Get unique colleges from the KEA cutoff data
    colleges = kea_df[["college_code", "college_name"]].drop_duplicates()
    colleges["name_norm"] = colleges["college_name"].apply(normalize_college_name)
    
    mapping = {}
    unmatched = []
    
    for _, row in colleges.iterrows():
        code = row["college_code"]
        name_norm = row["name_norm"]
        
        # Try exact normalized match
        exact = kea_aliases[kea_aliases["name_norm"] == name_norm]
        if not exact.empty:
            mapping[code] = int(exact.iloc[0]["college_id"])
            continue
        
        # Try substring match (KEA names are often truncated)
        # Check if any alias starts with the same first 20 chars
        prefix = name_norm[:20] if len(name_norm) > 20 else name_norm
        partial = kea_aliases[kea_aliases["name_norm"].str.startswith(prefix)]
        if not partial.empty:
            mapping[code] = int(partial.iloc[0]["college_id"])
            continue
        
        # Try matching first significant word
        words = name_norm.split()
        if len(words) >= 2:
            key_word = words[0] if len(words[0]) > 3 else words[1] if len(words) > 1 else words[0]
            city_from_cutoff = row["college_name"].split(",")[-1].strip().lower() if "," in row["college_name"] else ""
            word_match = kea_aliases[
                kea_aliases["name_norm"].str.contains(key_word, na=False) &
                (kea_aliases["alias_name"].str.lower().str.contains(city_from_cutoff, na=False) if city_from_cutoff else True)
            ]
            if len(word_match) == 1:
                mapping[code] = int(word_match.iloc[0]["college_id"])
                continue
        
        unmatched.append((code, row["college_name"]))
    
    return mapping, unmatched


def convert_to_curated_schema(
    kea_df: pd.DataFrame, 
    mapping: dict[str, int], 
    year: int,
    source_ids: dict[str, int]
) -> pd.DataFrame:
    """Convert parsed KEA data to curated closing_ranks schema."""
    
    rows = []
    for _, r in kea_df.iterrows():
        college_id = mapping.get(r["college_code"])
        if college_id is None:
            continue  # Skip unmapped colleges
        
        # Determine source_id based on round and seat_type
        key = f"{r['round']}_{r['seat_type']}"
        src_id = source_ids.get(key, source_ids.get("default", 0))
        
        rows.append({
            "year": year,
            "round": r["round"],
            "authority": "KEA",
            "counselling_scope": "STATE_KA",
            "college_id": college_id,
            "course": r["course"],
            "category": r["category"],
            "quota": None,
            "seat_type": r.get("seat_type", None),
            "opening_rank": None,
            "closing_rank": int(r["closing_rank"]),
            "seats_filled": None,
            "derivation_method": "official_published",
            "statuses_included": None,
            "source_id": src_id,
            "seats_total": None,
            "notes": f"KEA cutoff PDF {year}",
        })
    
    return pd.DataFrame(rows)


def main():
    parser = argparse.ArgumentParser(description="Integrate KEA cutoffs into curated closing_ranks")
    parser.add_argument("--year", type=int, action="append", required=True)
    parser.add_argument("--commit", action="store_true", help="Actually write to curated file")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be added")
    args = parser.parse_args()
    
    aliases_df = pd.read_csv(CURATED_DIR / "college_aliases.csv")
    
    all_new_rows = []
    
    for year in args.year:
        cutoff_path = Path(f"data/parsed/kea_cutoffs/kea_{year}_closing_ranks.csv")
        if not cutoff_path.exists():
            print(f"ERROR: {cutoff_path} not found")
            continue
        
        kea_df = pd.read_csv(cutoff_path)
        print(f"\n{'='*60}")
        print(f"Year {year}: {len(kea_df)} entries, {kea_df.college_code.nunique()} colleges")
        
        # Build mapping
        mapping, unmatched = build_kea_code_to_college_id(kea_df, aliases_df)
        print(f"  Mapped: {len(mapping)} colleges")
        print(f"  Unmatched: {len(unmatched)} colleges")
        
        if unmatched:
            print("  Unmatched colleges:")
            for code, name in unmatched[:10]:
                print(f"    {code}: {name}")
        
        # Source IDs for 2020 and 2021
        source_map = {
            2020: {"R1_GOVT": 54, "R1_HK": 55, "R1_PRIV": 56, "R2_GOVT": 57, "R2_HK": 58, "R2_PRIV": 59, "default": 54},
            2021: {"R1_GOVT": 61, "R1_HK": 62, "R1_PRIV": 63, "R2_GOVT": 64, "R2_HK": 65, "R2_PRIV": 66, "default": 61},
        }
        # Simplified: use default source_id
        source_ids = source_map.get(year, {"default": 61})
        
        # Convert
        curated_rows = convert_to_curated_schema(kea_df, mapping, year, source_ids)
        print(f"  Converted: {len(curated_rows)} rows (from {len(kea_df)} source rows)")
        
        mapped_pct = len(curated_rows) / len(kea_df) * 100 if len(kea_df) > 0 else 0
        print(f"  Coverage: {mapped_pct:.1f}%")
        
        all_new_rows.append(curated_rows)
    
    if not all_new_rows:
        print("\nNo data to integrate.")
        return
    
    combined_new = pd.concat(all_new_rows, ignore_index=True)
    print(f"\n{'='*60}")
    print(f"Total new rows: {len(combined_new)}")
    
    if args.commit:
        curated_path = CURATED_DIR / "closing_ranks.csv"
        existing = pd.read_csv(curated_path, dtype={"quota": str, "statuses_included": str})
        
        # Remove any existing KEA official_published data for these years
        years_to_add = set(args.year)
        mask = ~(
            (existing["year"].isin(years_to_add)) & 
            (existing["authority"] == "KEA") & 
            (existing["derivation_method"] == "official_published")
        )
        existing = existing[mask]
        
        # Append
        final = pd.concat([existing, combined_new], ignore_index=True)
        final.to_csv(curated_path, index=False)
        print(f"\nCommitted! {curated_path}: {len(final)} total rows (was {len(existing)})")
    else:
        print("\nDry run complete. Use --commit to write to curated/closing_ranks.csv")
        # Save preview
        preview_path = Path("data/analysis/kea_integration_preview.csv")
        preview_path.parent.mkdir(parents=True, exist_ok=True)
        combined_new.to_csv(preview_path, index=False)
        print(f"Preview saved to {preview_path}")


if __name__ == "__main__":
    main()
