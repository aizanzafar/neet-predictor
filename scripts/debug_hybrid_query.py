"""Full hybrid prediction log for: 658 marks, 2026, General, Karnataka."""
import sys
import os
import logging

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, "src")
logging.basicConfig(
    level=logging.WARNING,  # suppress httpx noise
    format="%(name)s | %(levelname)s | %(message)s",
)
# Enable DEBUG only for our modules
logging.getLogger("neet_predictor").setLevel(logging.DEBUG)
logger = logging.getLogger("FULL_LOG")

print("=" * 80)
print("FULL HYBRID PREDICTION LOG")
print("Query: 658 marks in 2026, General category, Karnataka state")
print("=" * 80)

# ============================================================
# STEP 1: Dataset Prediction
# ============================================================
print("\n" + "=" * 80)
print("STEP 1: DATASET PREDICTION (Our verified 6-year data)")
print("=" * 80)

from neet_predictor.rank.estimator import RankEstimator

est = RankEstimator(use_validation_data=True)

try:
    r = est.estimate(658, target_year=2026)
    print(f"  Target year requested: 2026")
    print(f"  Actual target year used: {r.target_year}")
    print(f"  Target appeared: {r.target_appeared:,}")
    print(f"  Method: {r.method}")
    print(f"  Confidence: {r.confidence}")
    print(f"  Median AIR: {r.median_air:,}")
    print(f"  Best case AIR: {r.best_case_air:,}")
    print(f"  Conservative AIR: {r.conservative_air:,}")
    print(f"  Training years used: {r.training_years}")
    print(f"  Nearest anchors:")
    for a in r.nearest_anchors:
        print(
            f"    Year {a['year']}: marks {a['marks_min']}-{a['marks_max']} "
            f"-> rank {a['rank_min']:,}-{a['rank_max']:,} ({a['confidence']})"
        )
    print(f"\n  Explanation: {r.explanation[:300]}")
except Exception as e:
    print(f"  ERROR: {e}")
    import traceback

    traceback.print_exc()

# ============================================================
# STEP 2: Web Search Query Construction + SERP Call
# ============================================================
print("\n" + "=" * 80)
print("STEP 2: WEB SEARCH (SerpAPI / DuckDuckGo / Built-in tables)")
print("=" * 80)

from neet_predictor.integrated.web_search import (
    build_search_query,
    search_neet_rank,
)

query = build_search_query(658, 2026, "General")
print(f"  Search query built: '{query}'")
print(f"  Calling search_neet_rank(658, 2026, 'General')...")

import os

print(f"  SERP_API_KEY set: {bool(os.getenv('SERP_API_KEY', ''))}")

web_result = search_neet_rank(658, 2026, "General")

print(f"\n  --- Web Search Results ---")
print(f"  Query used: {web_result.query_used}")
print(f"  Number of results: {len(web_result.results)}")
print(f"  Error: {web_result.error}")
print(f"  Raw snippets ({len(web_result.raw_snippets)}):")
for i, s in enumerate(web_result.raw_snippets[:5]):
    print(f"    [{i}] {s[:150]}")

print(f"\n  --- Parsed Rank Data ---")
for i, wr in enumerate(web_result.results):
    print(
        f"    [{i}] Source: {wr.source} | "
        f"Rank: {wr.rank_min:,}-{wr.rank_max:,} | "
        f"Estimate: {wr.rank_estimate:,} | "
        f"Year: {wr.year}"
    )
    print(f"         Context: {wr.context[:120]}")

print(f"\n  --- Consensus ---")
print(f"  Consensus rank min: {web_result.consensus_rank_min}")
print(f"  Consensus rank max: {web_result.consensus_rank_max}")
print(f"  Consensus rank mid: {web_result.consensus_rank_mid}")
print(f"  Source count: {web_result.source_count}")

# ============================================================
# STEP 3: Hybrid Agent Merge
# ============================================================
print("\n" + "=" * 80)
print("STEP 3: HYBRID AGENT (Merge dataset + web)")
print("=" * 80)

from neet_predictor.integrated.hybrid_agent import run_hybrid_prediction

hybrid = run_hybrid_prediction(658, 2026, "General", estimator=est)

print(f"  Final rank min: {hybrid.final_rank_min:,}")
print(f"  Final rank mid: {hybrid.final_rank_mid:,}")
print(f"  Final rank max: {hybrid.final_rank_max:,}")
print(f"  Agreement: {hybrid.agreement}")
print(f"  Divergence: {hybrid.divergence_pct:.1f}%")
print(f"  Primary source: {hybrid.primary_source}")
print(f"\n  Percentile context: {hybrid.percentile_context}")
print(f"  Counselling context: {hybrid.counselling_context}")
print(f"  Tie-breaking notes: {hybrid.tie_breaking_notes}")
print(f"\n  Explanation: {hybrid.explanation}")

# ============================================================
# STEP 4: Full Pipeline (College Predictions)
# ============================================================
print("\n" + "=" * 80)
print("STEP 4: FULL PIPELINE — College Predictions for Karnataka")
print("=" * 80)

from neet_predictor.integrated.pipeline import UnifiedInput, run_prediction
from neet_predictor.integrated.summary import build_student_result

inp = UnifiedInput(
    marks=658,
    national_category="General",
    home_state="Karnataka",
    karnataka_interest=True,
    karnataka_domicile=True,
    karnataka_category="GM",
    course_pref="MBBS",
    college_type_pref="any",
    target_year=2026,
)

result = run_prediction(inp)
sr = build_student_result(result)

print(f"  AIR used for college matching: {result.rank_used.air:,} ({result.rank_used.source})")
print(f"  Total shortlisted colleges: {len(sr.shortlist)}")

safe = [e for e in sr.shortlist if e.chance == "Safe"]
likely = [e for e in sr.shortlist if e.chance == "Likely"]
borderline = [e for e in sr.shortlist if e.chance == "Borderline"]
unlikely = [e for e in sr.shortlist if e.chance == "Unlikely"]

print(f"  Safe: {len(safe)} | Likely: {len(likely)} | Borderline: {len(borderline)} | Unlikely: {len(unlikely)}")

print(f"\n  --- TOP SAFE COLLEGES ---")
for i, e in enumerate(safe[:10]):
    r1 = max(e.r1_closing_ranks.items(), key=lambda x: x[0]) if e.r1_closing_ranks else (None, None)
    closing = f"R1 closing: {r1[1]:,} ({r1[0]})" if r1[0] else "no data"
    print(f"    [{i+1}] {e.college_name.split(',')[0][:55]}")
    print(f"         State: {e.state} | Authority: {e.authority} | Category: {e.category}")
    print(f"         {closing} | Margin: {e.weighted_margin:+.0%}" if e.weighted_margin else f"         {closing}")

print(f"\n  --- TOP LIKELY COLLEGES ---")
for i, e in enumerate(likely[:8]):
    r1 = max(e.r1_closing_ranks.items(), key=lambda x: x[0]) if e.r1_closing_ranks else (None, None)
    closing = f"R1 closing: {r1[1]:,} ({r1[0]})" if r1[0] else "no data"
    print(f"    [{i+1}] {e.college_name.split(',')[0][:55]}")
    print(f"         State: {e.state} | Authority: {e.authority} | {closing}")

print(f"\n  --- TOP BORDERLINE COLLEGES ---")
for i, e in enumerate(borderline[:5]):
    r1 = max(e.r1_closing_ranks.items(), key=lambda x: x[0]) if e.r1_closing_ranks else (None, None)
    closing = f"R1 closing: {r1[1]:,} ({r1[0]})" if r1[0] else "no data"
    print(f"    [{i+1}] {e.college_name.split(',')[0][:55]}")
    print(f"         State: {e.state} | Authority: {e.authority} | {closing}")

# KEA specifically
kea_colleges = [e for e in sr.shortlist if e.authority == "KEA"]
print(f"\n  --- KEA KARNATAKA COLLEGES ({len(kea_colleges)} total) ---")
for i, e in enumerate(kea_colleges[:12]):
    r1 = max(e.r1_closing_ranks.items(), key=lambda x: x[0]) if e.r1_closing_ranks else (None, None)
    closing = f"R1 closing: {r1[1]:,} ({r1[0]})" if r1[0] else "no data"
    print(f"    [{i+1}] {e.college_name.split(',')[0][:55]}")
    print(f"         Chance: {e.chance} | Cat: {e.category} | {closing}")

# ============================================================
# STEP 5: Full Reasoning (with hybrid augmentation)
# ============================================================
print("\n" + "=" * 80)
print("STEP 5: REASONING OUTPUT (Rule-based + Hybrid Web Cross-check)")
print("=" * 80)

from neet_predictor.integrated.reasoning import generate_reasoning

reasoning = generate_reasoning(658, 2026, result, sr)
print(f"  Source: {reasoning.source}")
print(f"  Hybrid agreement: {reasoning.hybrid_agreement}")
print(f"\n{'─'*60}")
print(reasoning.full_text)
print(f"{'─'*60}")

# Warnings
if result.warnings:
    print(f"\n  --- Warnings ---")
    for w in result.warnings:
        print(f"    • {w}")

print("\n" + "=" * 80)
print("END OF LOG")
print("=" * 80)
