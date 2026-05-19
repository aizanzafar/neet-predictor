"""Knowledge injection — builds domain context for LLM prompts.

Selects relevant facts from analysis data based on the student's profile.
No LLM involved — pure data lookup and formatting.
"""

from __future__ import annotations

from neet_predictor.counsellor.models import ScenarioComparison, StudentIntent
from neet_predictor.integrated.summary import StudentResult


# ── Static knowledge derived from data/analysis/air_insights_log.md ──

_CATEGORY_MULTIPLIERS = {
    "OBC": "OBC closing ranks are typically 1.3-1.8x the General rank for the same college.",
    "SC": "SC closing ranks are typically 3-6x the General rank for the same college.",
    "ST": "ST closing ranks are typically 4-8x the General rank for the same college.",
    "EWS": "EWS closing ranks are typically 1.2-1.5x the General rank for the same college.",
    "General": "General category has the most competitive (lowest) closing ranks.",
}

_TIER_CONTEXT = {
    "elite": "Student is in ELITE tier (AIR ≤1000). Colleges here have very stable ranks (CV<0.02). 15 colleges in this band.",
    "tier1": "Student is in Tier 1 (AIR 1k-5k). Most colleges stable (CV 0.01-0.05). 88 colleges in this band.",
    "tier2": "Student is in Tier 2 (AIR 5k-15k). Most predictable tier (median error ~9.5%). 211 colleges.",
    "tier3": "Student is in Tier 3 (AIR 15k-40k). Moderate predictability. 125 colleges.",
    "tier4": "Student is in Tier 4 (AIR 40k-100k). Limited AIQ options, mostly deemed universities.",
    "tier5": "Student is in Tier 5 (AIR 100k+). Primarily deemed/paid seats available through AIQ.",
}

_MARKS_TO_AIR_APPROX_2025 = [
    (686, 1), (682, 2), (681, 3), (678, 8),
    (650, 77), (635, 170), (630, 250),
    (622, 412), (609, 845), (607, 981), (601, 1302),
    (589, 2341), (577, 4000), (571, 5123), (563, 7296),
    (549, 12860), (540, 17370), (528, 25541),
    (525, 27698), (515, 36843), (481, 76510),
    (478, 80336), (459, 107944), (435, 146846),
    (402, 206050), (398, 213371), (302, 436777),
    (257, 577330), (228, 684232), (172, 937041),
    (135, 1152192),
]

_ROUND_DYNAMICS = (
    "If not allotted in R1: R2 adds ~4,000 to closing rank (median). "
    "R3 and MOPUP add more. STRAY adds ~14,500 to median closing rank."
)

_STRAY_INFO = "94% of STRAY round candidates are new entries (not from R1)."

_COMPETITION_2025 = "2025 competition: 46:1 (1.2M qualified for 26K AIQ seats). First registration decline (-5.4%)."

_NEW_COLLEGES_WARNING = "159 new colleges in 2025 have NO historical data — predictions may be unavailable for them."

_KEA_CAVEAT = (
    "KEA Karnataka predictions use data from 2020-2025 (21,052 rows across R1, R2, R3, and STRAY rounds). "
    "Predictions based on R1 cutoffs are most conservative. R2 cutoffs are typically 15-30% more relaxed."
)

_TIEBREAKER_2025 = (
    "2025 tie-breaking changed: Physics > Chemistry > Biology "
    "(was Biology > Chemistry in 2020-2024)."
)


def _get_tier_key(air: int) -> str:
    """Map AIR to tier key."""
    if air <= 1000:
        return "elite"
    elif air <= 5000:
        return "tier1"
    elif air <= 15000:
        return "tier2"
    elif air <= 40000:
        return "tier3"
    elif air <= 100000:
        return "tier4"
    else:
        return "tier5"


def _approx_air_from_marks(marks: int) -> str:
    """Rough AIR estimate from marks using 2025 anchors."""
    if marks >= 686:
        return "~1"
    for i, (m, r) in enumerate(_MARKS_TO_AIR_APPROX_2025):
        if marks >= m:
            if i == 0:
                return f"~{r:,}"
            prev_m, prev_r = _MARKS_TO_AIR_APPROX_2025[i - 1]
            # Linear interpolation
            frac = (prev_m - marks) / (prev_m - m) if prev_m != m else 0
            approx = int(prev_r + frac * (r - prev_r))
            return f"~{approx:,}"
    return ">1,200,000"


def build_knowledge_context(
    intent: StudentIntent,
    comparison: ScenarioComparison,
) -> str:
    """Build domain knowledge context string for LLM system prompt.

    Selects relevant facts based on the student's profile.
    """
    sections: list[str] = []

    # 1. Category multiplier
    cat = intent.national_category or "General"
    if cat in _CATEGORY_MULTIPLIERS:
        sections.append(_CATEGORY_MULTIPLIERS[cat])

    # 2. Marks-to-AIR context
    if intent.marks and not intent.actual_air:
        approx = _approx_air_from_marks(intent.marks)
        sections.append(
            f"At {intent.marks} marks (2025 scale), approximate AIR ≈ {approx}."
        )
        sections.append(
            "Marks-to-AIR conversion is EXPERIMENTAL. Real AIR can differ by ±30%."
        )

    # 3. Tier context (from first successful scenario)
    for sr in comparison.results:
        if sr.error or sr.student_result is None:
            continue
        student_result: StudentResult = sr.student_result  # type: ignore[assignment]
        air = student_result.rank_used.air
        tier_key = _get_tier_key(air)
        sections.append(_TIER_CONTEXT[tier_key])
        break

    # 4. Round dynamics
    sections.append(_ROUND_DYNAMICS)
    sections.append(_STRAY_INFO)

    # 5. Competition
    sections.append(_COMPETITION_2025)

    # 6. New colleges warning
    sections.append(_NEW_COLLEGES_WARNING)

    # 7. KEA caveat (if Karnataka interest)
    if intent.karnataka_interest:
        sections.append(_KEA_CAVEAT)

    # 8. Tiebreaker change
    sections.append(_TIEBREAKER_2025)

    return "\n".join(f"• {s}" for s in sections)
