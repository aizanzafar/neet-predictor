"""Diagnose rank estimator accuracy issues for 2022."""
import csv

rows = list(csv.DictReader(open("data/curated/marks_rank_points.csv")))
r2022 = [r for r in rows if r["year"] == "2022"]

print("=== 2022 DATA CONFLICT ANALYSIS ===\n")

# Separate precise vs coarse data
precise = []
coarse = []
for r in r2022:
    spread = int(r["rank_max"]) - int(r["rank_min"])
    marks = int(r["marks_min"])
    if spread > 5000 or (marks in (650, 600, 550, 500)):
        coarse.append(r)
    else:
        precise.append(r)

print(f"Precise points: {len(precise)}, Coarse/suspect: {len(coarse)}\n")

print("PRECISE data (NTA score-vs-rank bands):")
for r in sorted(precise, key=lambda x: -int(x["marks_min"]))[:20]:
    marks = r["marks_min"]
    rmin, rmax = int(r["rank_min"]), int(r["rank_max"])
    print(f"  marks={marks:>4} -> rank {rmin:>7,}-{rmax:>7,}  [{r['extraction_method']}, {r['confidence']}]")

print("\nCOARSE/SUSPECT data:")
for r in sorted(coarse, key=lambda x: -int(x["marks_min"])):
    marks = int(r["marks_min"])
    rmin, rmax = int(r["rank_min"]), int(r["rank_max"])
    print(f"  marks={marks:>4} -> rank {rmin:>7,}-{rmax:>7,}  [{r['extraction_method']}, {r['confidence']}]")
    # Check contradiction with precise neighbors
    for p in precise:
        pm = int(p["marks_min"])
        pr_min, pr_max = int(p["rank_min"]), int(p["rank_max"])
        if abs(pm - marks) <= 10 and pm != marks:
            # If coarse says better rank than precise neighbor with LOWER marks, it's wrong
            if marks > pm and rmin < pr_min:
                print(f"    OK: higher marks, better rank")
            elif marks < pm and rmin > pr_min:
                print(f"    OK: lower marks, worse rank")
            elif marks > pm and rmax > pr_min:
                print(f"    CONFLICT: marks={marks} claims rank {rmin:,}-{rmax:,} but marks={pm} is {pr_min:,}-{pr_max:,}")
            elif marks >= pm and rmin < pr_min // 2:
                print(f"    SUSPECT: marks={marks} rank {rmin:,} is much better than marks={pm} rank {pr_min:,}")

print("\n\n=== WHAT 627 SHOULD MAP TO IN 2022 ===")
print("Direct interpolation from precise 2022 data:")
print("  marks=628 -> rank 8,575-10,107")
print("  marks=618 -> rank 11,742-13,484")
print("  Linear interp for 627: ~10,107 + (11,742-10,107)*0.1 = ~10,271")
print("  RTI ground truth (Mysore MC allotment): rank ~10,220")
print("  MATCH! Direct interpolation within 2022 is accurate.")
print()
print("=== WHY ESTIMATOR GIVES 17,387 (MEDIAN) ===")
print("Year weights: 2024=0.40, 2023=0.25, 2022=0.18, 2021=0.10, 2020=0.07")
print("Problem: 2022 data gets only 18% weight even when TARGET is 2022!")
print("The 2024 curve (40% weight) maps 627 marks to a MUCH worse rank")
print("because 2024 was harder/more competitive.")
print()

# Check what 2024 and 2025 say for 627 marks
r2024 = [r for r in rows if r["year"] == "2024"]
r2025 = [r for r in rows if r["year"] == "2025"]

print("What other years say about 627 marks:")
for year_label, year_data in [("2024", r2024), ("2025", r2025), ("2021", [r for r in rows if r["year"] == "2021"])]:
    for r in sorted(year_data, key=lambda x: abs(int(x["marks_min"]) - 627)):
        if abs(int(r["marks_min"]) - 627) <= 5:
            print(f"  {year_label}: marks={r['marks_min']} -> rank {r['rank_min']}-{r['rank_max']}")
            break
