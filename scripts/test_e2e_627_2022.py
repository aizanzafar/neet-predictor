"""End-to-end pipeline test: 627 marks in 2022.

Query 1: "I got 627 marks in 2022, predict my rank and colleges via AIR (MCC)"
Query 2: "I have Karnataka domicile, which colleges can I get?"
"""

import sys
from pathlib import Path

_PROJECT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_PROJECT / "src"))

from neet_predictor.rank.calibration import NormalizationMode
from neet_predictor.rank.estimator import RankEstimator
from neet_predictor.integrated.pipeline import UnifiedInput, run_prediction
from neet_predictor.college.predictor import CollegePrediction


def print_header(text: str) -> None:
    print(f"\n{'='*70}")
    print(f"  {text}")
    print(f"{'='*70}")


def print_predictions(predictions: list, label: str, top_n: int = 15) -> None:
    """Print top predictions grouped by chance level."""
    # Group by chance
    safe = [p for p in predictions if p.chance == "Safe"]
    likely = [p for p in predictions if p.chance == "Likely"]
    borderline = [p for p in predictions if p.chance == "Borderline"]

    print(f"\n  {label}:")
    print(f"  Total predictions: {len(predictions)}")
    print(f"  Safe: {len(safe)} | Likely: {len(likely)} | Borderline: {len(borderline)}")

    # Show Safe colleges
    if safe:
        print(f"\n  --- SAFE ({len(safe)}) - Top {min(top_n, len(safe))} ---")
        for p in safe[:top_n]:
            college_name = p.college_name.split(",")[0]  # Just the short name
            print(f"    {college_name}")
            print(f"      State: {p.state} | Quota: {p.quota} | Margin: {p.weighted_margin:+.0%}")
            r1_str = ", ".join(f"{y}: {r:,}" for y, r in sorted(p.r1_closing_ranks.items()))
            print(f"      R1 Closing: {r1_str}")

    # Show Likely colleges
    if likely:
        print(f"\n  --- LIKELY ({len(likely)}) - Top {min(top_n, len(likely))} ---")
        for p in likely[:top_n]:
            college_name = p.college_name.split(",")[0]
            print(f"    {college_name}")
            print(f"      State: {p.state} | Quota: {p.quota} | Margin: {p.weighted_margin:+.0%}")
            r1_str = ", ".join(f"{y}: {r:,}" for y, r in sorted(p.r1_closing_ranks.items()))
            print(f"      R1 Closing: {r1_str}")

    # Show top Borderline colleges
    if borderline:
        # Sort by margin descending (closest to getting in)
        borderline_sorted = sorted(borderline, key=lambda p: p.weighted_margin, reverse=True)
        print(f"\n  --- BORDERLINE (top {min(5, len(borderline))} of {len(borderline)}) ---")
        for p in borderline_sorted[:5]:
            college_name = p.college_name.split(",")[0]
            print(f"    {college_name}")
            print(f"      State: {p.state} | Quota: {p.quota} | Margin: {p.weighted_margin:+.0%}")
            r1_str = ", ".join(f"{y}: {r:,}" for y, r in sorted(p.r1_closing_ranks.items()))
            print(f"      R1 Closing: {r1_str}")


def filter_govt_colleges(predictions: list) -> list:
    """Filter to only government/AIQ quota colleges (not deemed/paid)."""
    return [p for p in predictions if "Deemed" not in p.quota and "Paid" not in p.quota]


# ===========================================================================
# QUERY 1: "I got 627 marks in 2022, predict rank and colleges via AIR"
# ===========================================================================

print_header("QUERY 1: 627 marks in 2022 -> Rank + MCC AIR Colleges")

# Step 1: Rank Estimation
print("\n  STEP 1: Marks → Rank Estimation")
print("  " + "-" * 50)

estimator = RankEstimator(normalization=NormalizationMode.AFFINE_TWO_POINT)
rank_result = estimator.estimate(627, target_year=2022)

print(f"  Marks: 627 | Target Year: 2022")
print(f"  Best-case AIR:    {rank_result.best_case_air:>8,}")
print(f"  Median AIR:       {rank_result.median_air:>8,}")
print(f"  Conservative AIR: {rank_result.conservative_air:>8,}")
print(f"  Confidence: {rank_result.confidence}")
print(f"\n  Nearest anchors:")
for anchor in rank_result.nearest_anchors[:4]:
    print(f"    {anchor}")

# Step 2: College Prediction via MCC (using median AIR for realistic prediction)
print("\n  STEP 2: College Prediction via MCC All-India Quota")
print("  " + "-" * 50)
print(f"  Using MEDIAN AIR: {rank_result.median_air:,} (most likely scenario)")

inp = UnifiedInput(
    marks=627,
    actual_air=rank_result.median_air,  # Use median for realistic test
    national_category="General",
    home_state="Karnataka",
    course_pref="MBBS",
    college_type_pref="any",
    target_year=2022,
    normalization=NormalizationMode.AFFINE_TWO_POINT,
)

result = run_prediction(inp)
mcc = result.college_predictions.mcc_predictions

# Show ALL colleges (including deemed)
print_predictions(mcc, "ALL MCC Colleges (Govt + Deemed/Private)")

# Show only Government colleges
govt_mcc = filter_govt_colleges(mcc)
print_predictions(govt_mcc, "GOVERNMENT-ONLY MCC Colleges")


# ===========================================================================
# QUERY 2: "I have Karnataka domicile" → KEA State Quota
# ===========================================================================

print_header("QUERY 2: Karnataka Domicile -> KEA State Quota Colleges")

print(f"\n  Same marks (627), same rank (AIR {rank_result.median_air:,})")
print(f"  Adding: Karnataka domicile + GM category (General Merit)")

inp_kea = UnifiedInput(
    marks=627,
    actual_air=rank_result.median_air,
    national_category="General",
    home_state="Karnataka",
    karnataka_interest=True,
    karnataka_domicile=True,
    karnataka_category="GM",
    course_pref="MBBS",
    college_type_pref="any",
    target_year=2022,
    normalization=NormalizationMode.AFFINE_TWO_POINT,
)

result_kea = run_prediction(inp_kea)
kea = result_kea.college_predictions.kea_predictions

print_predictions(kea, "KEA Karnataka State Quota (GM category)")

# Also show combined summary
print("\n" + "=" * 70)
print("  COMBINED SUMMARY")
print("=" * 70)
mcc_actionable = [p for p in mcc if p.chance in ("Safe", "Likely", "Borderline")]
kea_actionable = [p for p in kea if p.chance in ("Safe", "Likely", "Borderline")]
print(f"\n  Marks: 627 | Year: 2022 | AIR (median): {rank_result.median_air:,}")
print(f"  MCC actionable colleges: {len(mcc_actionable)} (Safe: {len([p for p in mcc if p.chance=='Safe'])}, Likely: {len([p for p in mcc if p.chance=='Likely'])}, Borderline: {len([p for p in mcc if p.chance=='Borderline'])})")
print(f"  KEA actionable colleges: {len(kea_actionable)} (Safe: {len([p for p in kea if p.chance=='Safe'])}, Likely: {len([p for p in kea if p.chance=='Likely'])}, Borderline: {len([p for p in kea if p.chance=='Borderline'])})")
print()
