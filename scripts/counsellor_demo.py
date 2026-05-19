"""CLI demo for the counsellor module.

Usage:
    python -m scripts.counsellor_demo "I scored 550 marks in NEET, OBC from Bihar"
    python -m scripts.counsellor_demo --interactive
"""

from __future__ import annotations

import argparse
import sys
import textwrap
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from neet_predictor.counsellor import (
    ClarificationNeeded,
    LLMClient,
    LLMClientError,
    ValidatedResponse,
    run_counsellor,
)


def _print_response(result: ValidatedResponse) -> None:
    """Pretty-print a validated response."""
    print("\n" + "=" * 70)
    print("COUNSELLOR RESPONSE")
    print("=" * 70)

    if result.fallback_used:
        print("\n⚠️  LLM narrative STRIPPED due to validation failures.")
        print("Violations:")
        for v in result.violations:
            print(f"  ❌ {v}")
        print("\n--- Falling back to raw engine results ---")
        for row in result.scenarios.comparison_table:
            print(f"\n  [{row.label}]")
            print(f"    Safe: {row.safe_count}, Likely: {row.likely_count}, "
                  f"Borderline: {row.borderline_count}")
            if row.best_college:
                print(f"    Best: {row.best_college} ({row.best_chance})")
    elif result.narrative:
        print(f"\n{result.narrative.full_narrative}")

    if result.violations and not result.fallback_used:
        print("\n⚠️  Minor validation issues (narrative preserved):")
        for v in result.violations:
            print(f"  - {v}")

    print("\n" + "-" * 70)
    print("WARNINGS:")
    for w in result.warnings:
        print(f"  ⚠️  {w}")

    print("\nLIMITATIONS:")
    for l in result.limitations:
        print(f"  • {l}")

    print(f"\n⏱️  Processing time: {result.processing_time_ms}ms")
    print(f"✅ Validation passed: {result.validation_passed}")
    print("=" * 70)


def _print_clarification(result: ClarificationNeeded) -> None:
    """Print clarification questions."""
    print("\n" + "=" * 70)
    print("NEED MORE INFORMATION")
    print("=" * 70)
    print("\nPlease answer the following:")
    for i, q in enumerate(result.questions, 1):
        print(f"  {i}. {q}")
    print("=" * 70)


def main() -> None:
    parser = argparse.ArgumentParser(description="NEET Counsellor Demo")
    parser.add_argument("query", nargs="?", help="Student query")
    parser.add_argument("--interactive", "-i", action="store_true",
                        help="Interactive mode")
    args = parser.parse_args()

    try:
        client = LLMClient()
    except LLMClientError as e:
        print(f"❌ Error: {e}")
        print("Make sure .env file exists with SIEMENS_API_KEY set.")
        sys.exit(1)

    if args.interactive:
        print("NEET UG Counsellor (type 'quit' to exit)")
        print("-" * 40)
        while True:
            try:
                query = input("\n📝 Your question: ").strip()
            except (EOFError, KeyboardInterrupt):
                break
            if query.lower() in ("quit", "exit", "q"):
                break
            if not query:
                continue

            try:
                result = run_counsellor(query, client=client)
                if isinstance(result, ClarificationNeeded):
                    _print_clarification(result)
                else:
                    _print_response(result)
            except LLMClientError as e:
                print(f"\n❌ LLM Error: {e}")
            except Exception as e:
                print(f"\n❌ Unexpected error: {type(e).__name__}: {e}")

    elif args.query:
        print(f"Query: {args.query}")
        try:
            result = run_counsellor(args.query, client=client)
            if isinstance(result, ClarificationNeeded):
                _print_clarification(result)
            else:
                _print_response(result)
        except LLMClientError as e:
            print(f"\n❌ LLM Error: {e}")
            sys.exit(1)
    else:
        # Example queries
        examples = [
            "I scored 550 marks in NEET 2025, OBC category from Bihar. What are my chances?",
            "AIR 12000, General category, Maharashtra. Interested in Karnataka too.",
            "Got 480 marks, SC category from UP. Should I consider BDS?",
        ]
        print("No query provided. Example usage:")
        print(f"\n  python {__file__} \"<your query>\"")
        print(f"  python {__file__} --interactive")
        print("\nExample queries:")
        for ex in examples:
            print(f"  • {ex}")


if __name__ == "__main__":
    main()
