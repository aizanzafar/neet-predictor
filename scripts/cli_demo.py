"""CLI demo for NEET AIR-Based College Predictor (Phase 1B-A)."""

import argparse
import sys
from pathlib import Path

# Ensure src/ is on the path when running from project root.
_PROJECT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_PROJECT / "src"))

from neet_predictor.college.eligibility import CandidateProfile
from neet_predictor.college.predictor import predict
from neet_predictor.college.explainer import format_results


def main() -> None:
    parser = argparse.ArgumentParser(
        description="NEET AIR-Based College Predictor (Phase 1B-A)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""\
Examples:
  python cli_demo.py --air 5000 --category General --state Delhi
  python cli_demo.py --air 15000 --category OBC --state Bihar --course MBBS
  python cli_demo.py --air 10000 --category General --state Karnataka \\
      --karnataka-interest --karnataka-domicile --karnataka-category GM
""",
    )
    parser.add_argument(
        "--air", type=int, required=True, help="All India Rank",
    )
    parser.add_argument(
        "--category", required=True,
        choices=["General", "OBC", "SC", "ST", "EWS"],
        help="National category",
    )
    parser.add_argument("--state", required=True, help="Home state")
    parser.add_argument("--pwd", action="store_true", help="Person with Disability")
    parser.add_argument(
        "--course", default="MBBS", choices=["MBBS", "BDS"],
        help="Course preference (default: MBBS)",
    )
    parser.add_argument(
        "--college-type", default="any",
        choices=["any", "government", "deemed", "central", "AIIMS"],
        help="College type preference (default: any)",
    )
    parser.add_argument(
        "--karnataka-interest", action="store_true",
        help="Interested in Karnataka state counselling",
    )
    parser.add_argument(
        "--karnataka-domicile", action="store_true",
        help="Karnataka domicile",
    )
    parser.add_argument(
        "--karnataka-category", default=None,
        help="KEA category (e.g. GM, 2A, 3B, SC, ST)",
    )

    args = parser.parse_args()

    profile = CandidateProfile(
        air=args.air,
        national_category=args.category,
        home_state=args.state,
        pwd=args.pwd,
        course_pref=args.course,
        college_type_pref=args.college_type,
        karnataka_interest=args.karnataka_interest,
        karnataka_domicile=args.karnataka_domicile,
        karnataka_category=args.karnataka_category,
    )

    result = predict(profile)
    print(format_results(result))


if __name__ == "__main__":
    main()
