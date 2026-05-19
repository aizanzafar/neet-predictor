"""Format predictions into human-readable explanations."""

from __future__ import annotations

from neet_predictor.college.predictor import CollegePrediction, PredictionResult


def explain_prediction(pred: CollegePrediction) -> str:
    """Generate one-block explanation for a single college prediction."""
    quota_display = pred.quota if pred.quota else "State Quota"
    lines = [
        f"  {pred.college_name}",
        f"  State: {pred.state} | Category: {pred.category}"
        f" | Quota: {quota_display}",
        f"  Chance: {pred.chance}",
    ]

    if pred.r1_closing_ranks:
        r1_str = ", ".join(
            f"{y}: {r:,}" for y, r in sorted(pred.r1_closing_ranks.items())
        )
        lines.append(f"  R1 Closing Ranks: {r1_str}")

    if pred.weighted_margin is not None:
        lines.append(f"  Weighted Margin: {pred.weighted_margin:+.1%}")

    if pred.supplementary_rounds:
        for rnd, data in sorted(pred.supplementary_rounds.items()):
            rnd_str = ", ".join(
                f"{y}: {r:,}" for y, r in sorted(data.items())
            )
            lines.append(f"  {rnd} (supplementary): {rnd_str}")

    for note in pred.confidence_notes:
        lines.append(f"  NOTE: {note}")

    return "\n".join(lines)


def format_results(result: PredictionResult) -> str:
    """Format the full PredictionResult into a printable report."""
    lines: list[str] = []
    p = result.profile

    lines.append("=" * 72)
    lines.append("NEET AIR-Based College Predictor  —  Results")
    lines.append("=" * 72)
    lines.append(f"AIR: {p.air:,}")
    lines.append(
        f"Category: {p.national_category}"
        + (f" (PwD)" if p.pwd else "")
    )
    lines.append(f"Home State: {p.home_state}")
    lines.append(f"Course: {p.course_pref} | College Type: {p.college_type_pref}")
    if p.karnataka_interest:
        lines.append(
            f"Karnataka: Interest=Yes, Domicile={p.karnataka_domicile}"
        )
        if p.karnataka_category:
            lines.append(f"  KEA Category: {p.karnataka_category}")
        elif p.karnataka_domicile:
            lines.append(
                "  KEA Category: Not specified (showing GM only)"
            )
    lines.append("")

    # ── Summary ──
    s = result.summary
    lines.append("-- Summary " + "-" * 61)
    lines.append(f"MCC predictions: {s['mcc_total']}")
    for label in ("Safe", "Likely", "Borderline", "Unlikely", "Insufficient data"):
        count = s["mcc_by_chance"].get(label, 0)
        if count:
            lines.append(f"  {label}: {count}")
    if result.kea_predictions:
        lines.append(f"KEA predictions: {s['kea_total']}")
        for label in (
            "Safe", "Likely", "Borderline", "Unlikely", "Insufficient data",
        ):
            count = s["kea_by_chance"].get(label, 0)
            if count:
                lines.append(f"  {label}: {count}")
    lines.append("")

    # ── MCC predictions ──
    if result.mcc_predictions:
        lines.append("-- MCC All-India Counselling " + "-" * 44)
        _append_grouped_predictions(lines, result.mcc_predictions)

    # ── KEA predictions ──
    if result.kea_predictions:
        lines.append("-- KEA Karnataka State Counselling " + "-" * 38)
        if result.kea_exploratory:
            lines.append(
                "*** EXPLORATORY: KEA category not specified. ***"
            )
            lines.append(
                "    Showing GM (General Merit) results only."
            )
            lines.append(
                "    Actual results may differ with specific KEA category."
            )
            lines.append("")
        _append_grouped_predictions(lines, result.kea_predictions)

    # ── Limitations ──
    lines.append("-- Limitations " + "-" * 58)
    lines.append(
        "* Predictions based on historical R1 closing ranks only."
    )
    lines.append(
        "* Chance labels are estimates, not guarantees."
    )
    lines.append(
        "* Year-to-year fluctuations can shift outcomes."
    )
    lines.append(
        "* Special quotas (NRI, DU, IP, ESI, AMU) not included."
    )
    lines.append(
        "* KEA data currently limited to 2023 R1 only — "
        "all KEA predictions show 'Insufficient data'."
    )
    if result.kea_exploratory:
        lines.append(
            "* KEA results are exploratory due to unspecified category."
        )

    return "\n".join(lines)


def _append_grouped_predictions(
    lines: list[str], predictions: list[CollegePrediction]
) -> None:
    """Group predictions by chance label and append to lines."""
    chance_groups: dict[str, list[CollegePrediction]] = {}
    for pred in predictions:
        chance_groups.setdefault(pred.chance, []).append(pred)

    for label in ("Safe", "Likely", "Borderline", "Unlikely", "Insufficient data"):
        preds = chance_groups.get(label, [])
        if not preds:
            continue
        lines.append(f"\n[{label}] ({len(preds)} options)")
        lines.append("-" * 40)
        for pred in preds:
            lines.append(explain_prediction(pred))
            lines.append("")
