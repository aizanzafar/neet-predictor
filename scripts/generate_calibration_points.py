"""Generate calibration anchor points from KEA eligible list data.

Converts the parsed eligible list (score ↔ rank pairs for thousands of candidates)
into curated marks_rank_points entries for the rank estimator.

Strategy: Sample at key score intervals to build a dense calibration curve.
Each point represents the median rank observed in a narrow score band.

Usage:
    python scripts/generate_calibration_points.py --year 2020
    python scripts/generate_calibration_points.py --year 2021
"""

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd


# Score bands to sample at (center of each band, ±2 marks)
SAMPLE_SCORES = [
    700, 690, 680, 670, 660, 650, 640, 630, 620, 610,
    600, 590, 580, 570, 560, 550, 540, 530, 520, 510,
    500, 480, 460, 440, 420, 400, 380, 360, 340, 320,
    300, 280, 260, 240, 220, 200, 180, 160, 140, 120,
]

BAND_WIDTH = 2  # ±2 marks from center


def generate_points(df: pd.DataFrame, year: int) -> pd.DataFrame:
    """Generate calibration anchor points from eligible list data."""
    points = []

    for center in SAMPLE_SCORES:
        lo = center - BAND_WIDTH
        hi = center + BAND_WIDTH
        band = df[(df["neet_score"] >= lo) & (df["neet_score"] <= hi)]

        if len(band) < 2:
            continue

        rank_min = int(band["neet_ai_rank"].min())
        rank_max = int(band["neet_ai_rank"].max())
        rank_median = int(band["neet_ai_rank"].median())
        candidate_count = len(band)

        points.append({
            "year": year,
            "marks_min": lo,
            "marks_max": hi,
            "rank_min": rank_min,
            "rank_max": rank_max,
            "rank_median": rank_median,
            "candidate_count": candidate_count,
            "percentile": None,
            "data_granularity": "range",
            "extraction_method": "kea_eligible_list",
            "source_id": 53 if year == 2020 else 68,
            "confidence": "high",
            "notes": f"From KEA UGNEET {year} verified eligible list; {candidate_count} candidates in band {lo}-{hi}",
        })

    return pd.DataFrame(points)


def main():
    parser = argparse.ArgumentParser(description="Generate rank calibration points from eligible lists")
    parser.add_argument("--year", type=int, required=True, choices=[2020, 2021])
    parser.add_argument("--output", "-o", type=Path, default=None)
    parser.add_argument("--append-to-curated", action="store_true",
                        help="Append new points directly to data/curated/marks_rank_points.csv")
    args = parser.parse_args()

    # Load eligible list
    eligible_path = Path(f"data/parsed/rank_calibration/kea_{args.year}_eligible_full.csv")
    if not eligible_path.exists():
        print(f"ERROR: {eligible_path} not found. Parse the eligible list first.")
        sys.exit(1)

    df = pd.read_csv(eligible_path)
    print(f"Loaded {len(df)} candidates for {args.year}")
    print(f"  Score range: {df['neet_score'].min()} - {df['neet_score'].max()}")
    print(f"  Rank range: {df['neet_ai_rank'].min()} - {df['neet_ai_rank'].max()}")

    # Generate calibration points
    points = generate_points(df, args.year)
    print(f"\nGenerated {len(points)} calibration anchor points")

    if not points.empty:
        print(f"  Marks coverage: {points['marks_min'].min()} - {points['marks_max'].max()}")
        print(f"  Rank coverage: {points['rank_min'].min()} - {points['rank_max'].max()}")
        print("\n  Sample points:")
        for _, p in points.head(10).iterrows():
            print(f"    Marks {p['marks_min']}-{p['marks_max']}: Rank {p['rank_min']:,}-{p['rank_max']:,} (median {p['rank_median']:,}, n={p['candidate_count']})")

    # Output
    if args.append_to_curated:
        curated_path = Path("data/curated/marks_rank_points.csv")
        existing = pd.read_csv(curated_path)

        # Remove any existing kea_eligible_list points for this year
        mask = ~((existing["year"] == args.year) & (existing["extraction_method"] == "kea_eligible_list"))
        existing = existing[mask]

        # Assign point_ids
        max_id = existing["point_id"].max()
        points["point_id"] = range(max_id + 1, max_id + 1 + len(points))

        # Append
        combined = pd.concat([existing, points], ignore_index=True)
        combined.to_csv(curated_path, index=False)
        print(f"\nAppended {len(points)} points to {curated_path}")
        print(f"Total points now: {len(combined)} (was {len(existing)})")
    else:
        out_path = args.output or Path(f"data/analysis/calibration_points_{args.year}.csv")
        out_path.parent.mkdir(parents=True, exist_ok=True)
        points.to_csv(out_path, index=False)
        print(f"\nSaved to {out_path}")
        print("Use --append-to-curated to add directly to marks_rank_points.csv")


if __name__ == "__main__":
    main()
