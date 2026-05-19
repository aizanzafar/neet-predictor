"""Format unified pipeline results into human-readable output."""

from __future__ import annotations

from neet_predictor.integrated.pipeline import UnifiedResult
from neet_predictor.college.explainer import (
    explain_prediction,
    _append_grouped_predictions,
)


def format_unified_result(result: UnifiedResult) -> str:
    """Format a ``UnifiedResult`` into a complete printable report."""
    lines: list[str] = []
    inp = result.input

    lines.append("=" * 72)
    lines.append("NEET Integrated Predictor  —  Results")
    lines.append("=" * 72)

    # ── Input summary ──
    lines.append("")
    lines.append("-- Input " + "-" * 63)
    if inp.marks is not None:
        lines.append(f"Marks: {inp.marks}")
    if inp.actual_air is not None:
        lines.append(f"Actual AIR: {inp.actual_air:,}")
    lines.append(f"Category: {inp.national_category}" + (" (PwD)" if inp.pwd else ""))
    lines.append(f"Home State: {inp.home_state}")
    lines.append(f"Course: {inp.course_pref} | College Type: {inp.college_type_pref}")
    if inp.karnataka_interest:
        lines.append(f"Karnataka: Interest=Yes, Domicile={inp.karnataka_domicile}")
        if inp.karnataka_category:
            lines.append(f"  KEA Category: {inp.karnataka_category}")
        elif inp.karnataka_domicile:
            lines.append("  KEA Category: Not specified (showing GM only)")

    # ── Rank estimation section ──
    lines.append("")
    lines.append("-- Rank Estimation " + "-" * 53)

    re = result.rank_estimate
    if re is not None:
        lines.append(f"Marks: {re.marks}")
        lines.append(f"Best-case AIR:    {re.best_case_air:>10,}")
        lines.append(f"Median AIR:       {re.median_air:>10,}")
        lines.append(f"Conservative AIR: {re.conservative_air:>10,}")
        lines.append(f"Confidence: {re.confidence}")
        lines.append(f"Method: {re.method}")
        if re.below_cutoff_warning:
            lines.append(f"WARNING: {re.below_cutoff_warning}")
    else:
        lines.append("Marks-based estimation: Not applicable (actual AIR provided).")

    # ── Rank used for college prediction ──
    lines.append("")
    lines.append("-- AIR Used for College Prediction " + "-" * 38)
    ru = result.rank_used
    lines.append(f"AIR: {ru.air:,}")
    lines.append(f"Source: {ru.source}")
    lines.append(f"  {ru.explanation}")

    # ── College predictions summary ──
    cp = result.college_predictions
    s = cp.summary
    lines.append("")
    lines.append("-- College Prediction Summary " + "-" * 43)
    lines.append(f"MCC predictions: {s['mcc_total']}")
    for label in ("Safe", "Likely", "Borderline", "Unlikely", "Insufficient data"):
        count = s["mcc_by_chance"].get(label, 0)
        if count:
            lines.append(f"  {label}: {count}")
    if cp.kea_predictions:
        lines.append(f"KEA predictions: {s['kea_total']}")
        for label in ("Safe", "Likely", "Borderline", "Unlikely", "Insufficient data"):
            count = s["kea_by_chance"].get(label, 0)
            if count:
                lines.append(f"  {label}: {count}")

    # ── MCC detail ──
    if cp.mcc_predictions:
        lines.append("")
        lines.append("-- MCC All-India Counselling " + "-" * 44)
        _append_grouped_predictions(lines, cp.mcc_predictions)

    # ── KEA detail ──
    if cp.kea_predictions:
        lines.append("")
        lines.append("-- KEA Karnataka State Counselling " + "-" * 38)
        if cp.kea_exploratory:
            lines.append("*** EXPLORATORY: KEA category not specified. ***")
            lines.append("    Showing GM (General Merit) results only.")
            lines.append("    Actual results may differ with specific KEA category.")
            lines.append("")
        _append_grouped_predictions(lines, cp.kea_predictions)

    # ── Warnings ──
    lines.append("")
    lines.append("-- Warnings & Limitations " + "-" * 47)
    for w in result.warnings:
        lines.append(f"* {w}")

    return "\n".join(lines)
