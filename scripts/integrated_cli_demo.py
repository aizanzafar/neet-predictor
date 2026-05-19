"""CLI demo for the Integrated NEET Predictor (Phase 1C).

Usage examples:

  # Marks only (General, Delhi)
  python scripts/integrated_cli_demo.py --marks 620 --category General --state Delhi

  # Actual AIR only (OBC, Karnataka with KEA interest)
  python scripts/integrated_cli_demo.py --air 15000 --category OBC --state Karnataka \
      --karnataka-interest --karnataka-domicile --karnataka-category 2A

  # Both marks and AIR (actual AIR used for college prediction)
  python scripts/integrated_cli_demo.py --marks 620 --air 25000 --category General --state Delhi
"""

import argparse
import sys
from pathlib import Path

_PROJECT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_PROJECT / "src"))

from neet_predictor.rank.calibration import NormalizationMode
from neet_predictor.integrated.pipeline import UnifiedInput, run_prediction
from neet_predictor.integrated.explainer import format_unified_result


def main() -> None:
    parser = argparse.ArgumentParser(
        description="NEET Integrated Predictor: Marks/AIR → College Predictions",
    )
    parser.add_argument(
        "--marks", type=int, default=None,
        help="NEET marks (0–720). Required if --air is not given.",
    )
    parser.add_argument(
        "--air", type=int, default=None,
        help="Actual All-India Rank. Required if --marks is not given.",
    )
    parser.add_argument(
        "--category", required=True,
        choices=["General", "OBC", "SC", "ST", "EWS"],
        help="National category.",
    )
    parser.add_argument(
        "--state", required=True,
        help="Home state (e.g. Delhi, Karnataka, Maharashtra).",
    )
    parser.add_argument(
        "--course", default="MBBS",
        choices=["MBBS", "BDS"],
        help="Course preference (default: MBBS).",
    )
    parser.add_argument(
        "--college-type", default="any",
        choices=["any", "government", "deemed", "central", "AIIMS"],
        help="College type preference (default: any).",
    )
    parser.add_argument(
        "--karnataka-interest", action="store_true",
        help="Interested in Karnataka KEA counselling.",
    )
    parser.add_argument(
        "--karnataka-domicile", action="store_true",
        help="Karnataka domicile status.",
    )
    parser.add_argument(
        "--karnataka-category", default=None,
        choices=["GM", "1", "2A", "2B", "3A", "3B", "SC", "ST"],
        help="KEA category (must be explicitly provided, not derived).",
    )
    parser.add_argument(
        "--target-year", type=int, default=2025,
        help="Target exam year for rank estimation (default: 2025).",
    )
    parser.add_argument(
        "--normalization", default="affine_two_point",
        choices=["none", "topper_score", "affine_two_point", "piecewise_affine"],
        help="Normalization strategy for rank estimation (default: affine_two_point).",
    )

    args = parser.parse_args()

    if args.marks is None and args.air is None:
        parser.error("At least one of --marks or --air must be provided.")

    norm_map = {
        "none": NormalizationMode.NONE,
        "topper_score": NormalizationMode.TOPPER_SCORE,
        "affine_two_point": NormalizationMode.AFFINE_TWO_POINT,
        "piecewise_affine": NormalizationMode.PIECEWISE_AFFINE,
    }

    try:
        inp = UnifiedInput(
            marks=args.marks,
            actual_air=args.air,
            national_category=args.category,
            home_state=args.state,
            pwd=False,
            course_pref=args.course,
            college_type_pref=args.college_type,
            karnataka_interest=args.karnataka_interest,
            karnataka_domicile=args.karnataka_domicile,
            karnataka_category=args.karnataka_category,
            target_year=args.target_year,
            normalization=norm_map[args.normalization],
        )
    except ValueError as e:
        parser.error(str(e))

    result = run_prediction(inp)
    print(format_unified_result(result))


if __name__ == "__main__":
    main()
