"""Layer 4: Scenario Comparator — compares results across branches.

Pure deterministic. No LLM involved.
"""

from __future__ import annotations

from neet_predictor.counsellor.models import (
    ComparisonRow,
    ScenarioComparison,
    ScenarioResult,
)
from neet_predictor.integrated.summary import StudentResult


def _count_by_chance(student_result: StudentResult) -> dict[str, int]:
    """Count colleges per chance label in shortlist."""
    counts: dict[str, int] = {
        "Safe": 0, "Likely": 0, "Borderline": 0, "Unlikely": 0,
        "Insufficient data": 0,
    }
    for entry in student_result.shortlist:
        if entry.chance in counts:
            counts[entry.chance] += 1
    return counts


def _best_college_from(student_result: StudentResult) -> tuple[str | None, str | None]:
    """Return (best_college_name, best_chance) from shortlist."""
    if not student_result.shortlist:
        return None, None
    best = student_result.shortlist[0]  # already ordered best→worst
    return best.college_name, best.chance


def _authority_split(student_result: StudentResult) -> str:
    """Summarize how many colleges come from MCC vs KEA."""
    mcc = student_result.mcc_summary.total
    kea = student_result.kea_summary.total
    return f"MCC: {mcc}, KEA: {kea}"


def compare_scenarios(results: list[ScenarioResult]) -> ScenarioComparison:
    """Build a comparison table across all scenario results."""
    rows: list[ComparisonRow] = []
    best_label: str | None = None
    best_score = -1
    notes: list[str] = []

    for sr in results:
        if sr.error or sr.student_result is None:
            rows.append(ComparisonRow(
                label=sr.spec.label,
                safe_count=0,
                likely_count=0,
                borderline_count=0,
                total_options=0,
                best_college=None,
                best_chance=None,
                authority_split="Error",
            ))
            continue

        student_result: StudentResult = sr.student_result  # type: ignore[assignment]
        counts = _count_by_chance(student_result)
        best_college, best_chance = _best_college_from(student_result)
        auth_split = _authority_split(student_result)

        safe = counts["Safe"]
        likely = counts["Likely"]
        borderline = counts["Borderline"]
        total = safe + likely + borderline

        rows.append(ComparisonRow(
            label=sr.spec.label,
            safe_count=safe,
            likely_count=likely,
            borderline_count=borderline,
            total_options=total,
            best_college=best_college,
            best_chance=best_chance,
            authority_split=auth_split,
        ))

        # Score: Safe×3 + Likely×2 + Borderline×1
        score = safe * 3 + likely * 2 + borderline
        if score > best_score:
            best_score = score
            best_label = sr.spec.label

    # ── Generate comparison notes ──
    if len(rows) >= 2:
        # Compare first (primary) with others
        primary = rows[0]
        for other in rows[1:]:
            delta = other.total_options - primary.total_options
            if delta > 0:
                notes.append(
                    f"'{other.label}' adds {delta} more options vs '{primary.label}'"
                )
            elif delta < 0:
                notes.append(
                    f"'{primary.label}' has {-delta} more options than '{other.label}'"
                )

    return ScenarioComparison(
        results=tuple(results),
        comparison_table=tuple(rows),
        best_scenario_label=best_label,
        notes=tuple(notes),
    )
