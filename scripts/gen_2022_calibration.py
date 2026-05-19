"""Generate calibration points from KEA 2022 RTI allotment data."""
import pandas as pd
from pathlib import Path

df = pd.read_csv("data/parsed/kea_allotments/kea_2022_rti_allotments.csv")
print(f"Loaded {len(df)} candidates for 2022")
print(f"  Marks range: {df['neet_marks'].min()} - {df['neet_marks'].max()}")
print(f"  Rank range: {df['neet_rank'].min()} - {df['neet_rank'].max()}")

SAMPLE_SCORES = [
    700, 690, 680, 670, 660, 650, 640, 630, 620, 610,
    600, 590, 580, 570, 560, 550, 540, 530, 520, 510,
    500, 480, 460, 440, 420, 400, 380, 360, 340, 320,
    300, 280, 260, 240, 220, 200, 180, 160, 140, 120,
]
BAND_WIDTH = 2

points = []
for center in SAMPLE_SCORES:
    lo, hi = center - BAND_WIDTH, center + BAND_WIDTH
    band = df[(df["neet_marks"] >= lo) & (df["neet_marks"] <= hi)]
    if len(band) < 2:
        continue
    points.append({
        "year": 2022,
        "marks_min": lo,
        "marks_max": hi,
        "rank_min": int(band["neet_rank"].min()),
        "rank_max": int(band["neet_rank"].max()),
        "rank_median": int(band["neet_rank"].median()),
        "candidate_count": len(band),
        "percentile": None,
        "data_granularity": "range",
        "extraction_method": "kea_rti_allotment",
        "source_id": 71,
        "confidence": "high",
        "notes": f"From KEA UGNEET 2022 RTI allotment list; {len(band)} candidates in band {lo}-{hi}",
    })

points_df = pd.DataFrame(points)
print(f"\nGenerated {len(points_df)} calibration points")
print(f"  Marks coverage: {points_df['marks_min'].min()} to {points_df['marks_max'].max()}")
print(f"  Rank coverage: {points_df['rank_min'].min()} to {points_df['rank_max'].max()}")

# Append to curated marks_rank_points.csv
curated_path = Path("data/curated/marks_rank_points.csv")
existing = pd.read_csv(curated_path)
print(f"\nExisting curated points: {len(existing)}")

# Remove any existing 2022 kea-sourced points
mask = ~((existing["year"] == 2022) & (existing["extraction_method"].str.contains("kea", na=False)))
existing = existing[mask]

# Assign point_ids
max_id = int(existing["point_id"].max())
points_df["point_id"] = range(max_id + 1, max_id + 1 + len(points_df))

combined = pd.concat([existing, points_df], ignore_index=True)
combined.to_csv(curated_path, index=False)
print(f"Appended {len(points_df)} points. Total: {len(combined)} (was {len(existing)})")

# Summary
yr_2022 = combined[combined["year"] == 2022]
print(f"\n2022 points total: {len(yr_2022)}")
for method in yr_2022["extraction_method"].unique():
    c = yr_2022[yr_2022["extraction_method"] == method]
    print(f"  {method}: {len(c)} points")
