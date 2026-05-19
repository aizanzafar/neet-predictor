"""CLI demo for NEET Marks-to-AIR Rank Estimator (Phase 1B-B/C)."""

import argparse
import sys
from pathlib import Path

_PROJECT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_PROJECT / "src"))

from neet_predictor.rank.calibration import NormalizationMode
from neet_predictor.rank.estimator import (
    RankEstimator,
    run_validation,
    compare_normalization_strategies,
)


def _format_result(r) -> str:
    lines = []
    lines.append("=" * 64)
    lines.append("NEET Marks-to-AIR Rank Estimator  —  Result")
    lines.append("=" * 64)
    lines.append(f"Marks:           {r.marks}")
    lines.append(f"Best-case AIR:   {r.best_case_air:,}")
    lines.append(f"Median AIR:      {r.median_air:,}")
    lines.append(f"Conservative AIR:{r.conservative_air:,}")
    lines.append(f"Confidence:      {r.confidence}")
    lines.append(f"Method:          {r.method}")
    lines.append(f"Training years:  {r.training_years}")
    lines.append(f"Target year:     {r.target_year} ({r.target_appeared:,} candidates)")
    lines.append("")

    if r.below_cutoff_warning:
        lines.append(f"WARNING: {r.below_cutoff_warning}")
        lines.append("")

    lines.append("-- Nearest historical anchors --")
    for a in r.nearest_anchors:
        lines.append(
            f"  {a['year']}: marks {a['marks_min']}-{a['marks_max']} "
            f"→ rank {a['rank_min']:,}-{a['rank_max']:,} ({a['confidence']})"
        )
    lines.append("")
    lines.append("-- Explanation --")
    lines.append(r.explanation)
    lines.append("")
    lines.append("-- Disclaimer --")
    lines.append(
        "This is an estimate based on historical data. "
        "Actual AIR depends on paper difficulty and tie-breaking rules. "
        "Exact rank cannot be predicted."
    )
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="NEET Marks-to-AIR Rank Estimator (Phase 1B-B/C)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""\
Examples:
  python rank_cli_demo.py --marks 620
  python rank_cli_demo.py --marks 620 --normalization topper_score
  python rank_cli_demo.py --marks 620 --target-year 2025
  python rank_cli_demo.py --marks 140 --category General
  python rank_cli_demo.py --validate
  python rank_cli_demo.py --validate --normalization affine_two_point
  python rank_cli_demo.py --compare
""",
    )
    parser.add_argument(
        "--marks", type=int, help="NEET marks (0-720)",
    )
    parser.add_argument(
        "--target-year", type=int, default=None,
        help="Target year for appeared-candidates scaling",
    )
    parser.add_argument(
        "--category", default=None,
        choices=["General", "OBC", "SC", "ST", "EWS"],
        help="Category (only for cutoff warning, not for AIR)",
    )
    parser.add_argument(
        "--normalization", default="none",
        choices=["none", "topper_score", "affine_two_point", "piecewise_affine"],
        help="Paper-difficulty normalization strategy (default: none)",
    )
    parser.add_argument(
        "--validate", action="store_true",
        help="Run 2025 held-out validation",
    )
    parser.add_argument(
        "--compare", action="store_true",
        help="Compare all normalization strategies on 2025 data",
    )

    args = parser.parse_args()
    norm_mode = NormalizationMode(args.normalization)

    if args.compare:
        print("Comparing normalization strategies on 2025 held-out data...")
        print()
        comp = compare_normalization_strategies()
        header = f"{'Strategy':<20} {'Coverage':>10} {'High(>=550)':>12} {'Low(<550)':>12} {'MedAbsErr':>12} {'MeanAbsErr':>12} {'W/in10%':>8} {'W/in20%':>8}"
        print(header)
        print("-" * len(header))
        for mode_name in ["none", "topper_score", "affine_two_point"]:
            r = comp[mode_name]
            n_cov = sum(1 for x in r["results"] if x["covered"])
            n_tot = r["n_validation_points"]
            print(
                f"{mode_name:<20} "
                f"{r['coverage_rate']:>8.1%} ({n_cov}/{n_tot})"
                f"{r['high_marks_coverage']:>9.1%}   "
                f"{r['low_mid_marks_coverage']:>9.1%}   "
                f"{r['median_absolute_error']:>12,.0f}"
                f"{r['mean_absolute_error']:>12,.0f}"
                f"{r['within_10_percent_band']:>8.1%}"
                f"{r['within_20_percent_band']:>8.1%}"
            )
        return

    if args.validate:
        print(f"Running 2025 held-out validation (normalization={args.normalization})...")
        print()
        results = run_validation(normalization=norm_mode)

        print("=" * 64)
        print("2025 Held-Out Validation Results")
        print("=" * 64)
        print(f"Validation points:       {results['n_validation_points']}")
        print(f"Coverage rate:           {results['coverage_rate']:.1%}")
        print(f"Median absolute error:   {results['median_absolute_error']:,.0f}")
        print(f"Mean absolute error:     {results['mean_absolute_error']:,.0f}")
        print(f"Within 10% band:         {results['within_10_percent_band']:.1%}")
        print(f"Within 20% band:         {results['within_20_percent_band']:.1%}")
        print(f"Target (>=70%):          {'PASS' if results['pass'] else 'FAIL'}")
        print()

        print("Per-point results:")
        for r in results["results"]:
            status = "OK " if r["covered"] else "MISS"
            print(
                f"  [{status}] marks={r['marks']:>3d}  "
                f"actual=[{r['actual_rank_min']:>8,}-{r['actual_rank_max']:>8,}]  "
                f"pred=[{r['predicted_best']:>8,}-{r['predicted_conservative']:>8,}]  "
                f"err={r['pct_error']:>6.1%}  {r['confidence']}"
            )
        return

    if args.marks is None:
        parser.error("--marks is required (or use --validate / --compare)")

    est = RankEstimator(normalization=norm_mode)
    result = est.estimate(
        marks=args.marks,
        target_year=args.target_year,
        category=args.category,
    )
    print(_format_result(result))


if __name__ == "__main__":
    main()
