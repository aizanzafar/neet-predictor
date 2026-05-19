"""Student-facing result contract (Phase 1D).

Converts ``UnifiedResult`` into a stable ``StudentResult`` structure
suitable for consumption by:
  - Streamlit UI
  - PDF / export layer
  - LLM counselling layer

No prediction logic lives here.  This module is a *pure transform*
from backend dataclasses to a student-friendly view.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from neet_predictor.integrated.pipeline import UnifiedResult, RankUsed
from neet_predictor.college.predictor import CollegePrediction


# ── Constants ──

# Chance labels in display order (best → worst).
CHANCE_ORDER: list[str] = [
    "Safe",
    "Likely",
    "Borderline",
    "Unlikely",
    "Insufficient data",
]

# Default top-N shortlist size.
DEFAULT_TOP_N = 50


# ── Dataclasses ──

@dataclass(frozen=True)
class InputSummary:
    """Echo of what the student provided."""

    marks: int | None
    actual_air: int | None
    national_category: str
    home_state: str
    pwd: bool
    course: str
    college_type: str
    karnataka_interest: bool
    karnataka_domicile: bool
    karnataka_category: str | None
    target_year: int
    normalization: str  # string name of the strategy


@dataclass(frozen=True)
class RankSummary:
    """Summarises the rank estimation for the student."""

    has_estimate: bool
    best_case_air: int | None
    median_air: int | None
    conservative_air: int | None
    confidence: str | None  # "high" / "medium" / "low" / None
    method: str | None
    below_cutoff_warning: str | None


@dataclass(frozen=True)
class RankUsedSummary:
    """Which AIR drives college prediction."""

    air: int
    source: str  # "actual" | "estimated_conservative"
    explanation: str


@dataclass(frozen=True)
class CollegeEntry:
    """One row in the student-facing shortlist."""

    college_name: str
    college_id: int
    state: str
    course: str
    authority: str  # "MCC" | "KEA"
    category: str
    quota: str
    chance: str  # Safe / Likely / Borderline / Unlikely / Insufficient data
    r1_closing_ranks: dict[int, int]
    r1_years_count: int
    supplementary_rounds: dict[str, dict[int, int]]  # {"R2": {2022: 10413, ...}, ...}
    weighted_margin: float | None
    confidence_notes: list[str]


@dataclass(frozen=True)
class ChanceBucket:
    """Count of colleges per chance label, for a given authority."""

    label: str
    count: int


@dataclass(frozen=True)
class AuthoritySummary:
    """Summary statistics for one counselling authority (MCC or KEA)."""

    authority: str
    total: int
    by_chance: list[ChanceBucket]
    exploratory: bool  # True when KEA category not specified


@dataclass(frozen=True)
class CourseSplit:
    """Count of shortlisted colleges per course."""

    course: str
    count: int


@dataclass(frozen=True)
class Metadata:
    """Generation metadata for traceability."""

    generated_at: str  # ISO-8601 timestamp
    engine_version: str
    top_n: int
    total_mcc_predictions: int
    total_kea_predictions: int


@dataclass(frozen=True)
class StudentResult:
    """Stable, student-facing result contract.

    Designed to be serialisable (all fields are simple types or frozen
    dataclasses).  Consumers include Streamlit UI, PDF export, and
    the future LLM counselling layer.
    """

    input_summary: InputSummary
    rank_summary: RankSummary
    rank_used: RankUsedSummary
    shortlist: list[CollegeEntry]  # top-N, ordered best → worst
    mcc_summary: AuthoritySummary
    kea_summary: AuthoritySummary
    course_split: list[CourseSplit]
    warnings: list[str]
    limitations: list[str]
    metadata: Metadata


# ── Limitations (always shown) ──

_LIMITATIONS: list[str] = [
    "Predictions are based on historical Round 1 closing ranks only.",
    "Year-to-year fluctuations in difficulty and participation can shift outcomes.",
    "Special quotas (NRI, DU, IP, ESI, AMU) are not fully covered.",
    "KEA data is currently limited — all KEA predictions may show 'Insufficient data'.",
    "This tool is not an admission guarantee. Verify all information from official sources.",
]


# ── Engine version ──

ENGINE_VERSION = "1.0.0-phase1d"


# ── Builder ──

def build_student_result(
    result: UnifiedResult,
    *,
    top_n: int = DEFAULT_TOP_N,
) -> StudentResult:
    """Transform a ``UnifiedResult`` into a ``StudentResult``.

    Parameters
    ----------
    result:
        The raw pipeline output from ``run_prediction()``.
    top_n:
        Maximum number of colleges in the shortlist.  Colleges are
        ranked by chance label (Safe first) then by weighted margin.
    """
    inp = result.input

    # ── Input summary ──
    input_summary = InputSummary(
        marks=inp.marks,
        actual_air=inp.actual_air,
        national_category=inp.national_category,
        home_state=inp.home_state,
        pwd=inp.pwd,
        course=inp.course_pref,
        college_type=inp.college_type_pref,
        karnataka_interest=inp.karnataka_interest,
        karnataka_domicile=inp.karnataka_domicile,
        karnataka_category=inp.karnataka_category,
        target_year=inp.target_year,
        normalization=inp.normalization.value,
    )

    # ── Rank summary ──
    re = result.rank_estimate
    rank_summary = RankSummary(
        has_estimate=re is not None,
        best_case_air=re.best_case_air if re else None,
        median_air=re.median_air if re else None,
        conservative_air=re.conservative_air if re else None,
        confidence=re.confidence if re else None,
        method=re.method if re else None,
        below_cutoff_warning=re.below_cutoff_warning if re else None,
    )

    # ── Rank used ──
    ru = result.rank_used
    rank_used = RankUsedSummary(
        air=ru.air,
        source=ru.source,
        explanation=ru.explanation,
    )

    # ── College predictions → shortlist ──
    cp = result.college_predictions
    # Build shortlist ensuring BOTH authorities are represented
    shortlist = _build_shortlist_balanced(cp.mcc_predictions, cp.kea_predictions, top_n)

    # ── Authority summaries ──
    mcc_summary = _build_authority_summary(
        "MCC", cp.mcc_predictions, exploratory=False,
    )
    kea_summary = _build_authority_summary(
        "KEA", cp.kea_predictions, exploratory=cp.kea_exploratory,
    )

    # ── Course split (from shortlist only) ──
    course_counts: dict[str, int] = {}
    for entry in shortlist:
        course_counts[entry.course] = course_counts.get(entry.course, 0) + 1
    course_split = [
        CourseSplit(course=c, count=n)
        for c, n in sorted(course_counts.items())
    ]

    # ── Metadata ──
    metadata = Metadata(
        generated_at=datetime.now(timezone.utc).isoformat(),
        engine_version=ENGINE_VERSION,
        top_n=top_n,
        total_mcc_predictions=len(cp.mcc_predictions),
        total_kea_predictions=len(cp.kea_predictions),
    )

    return StudentResult(
        input_summary=input_summary,
        rank_summary=rank_summary,
        rank_used=rank_used,
        shortlist=shortlist,
        mcc_summary=mcc_summary,
        kea_summary=kea_summary,
        course_split=course_split,
        warnings=list(result.warnings),
        limitations=list(_LIMITATIONS),
        metadata=metadata,
    )


# ── Internal helpers ──

def _pred_to_entry(pred: CollegePrediction) -> CollegeEntry:
    """Convert a backend ``CollegePrediction`` to a ``CollegeEntry``."""
    return CollegeEntry(
        college_name=pred.college_name,
        college_id=pred.college_id,
        state=pred.state,
        course=pred.course,
        authority=pred.authority,
        category=pred.category,
        quota=pred.quota,
        chance=pred.chance,
        r1_closing_ranks=dict(pred.r1_closing_ranks),
        r1_years_count=pred.r1_years_count,
        supplementary_rounds=dict(pred.supplementary_rounds),
        weighted_margin=pred.weighted_margin,
        confidence_notes=list(pred.confidence_notes),
    )


def _sort_key(pred: CollegePrediction) -> tuple[int, float, str]:
    """Sort key: chance order (best first), then margin (highest first), then name."""
    chance_idx = CHANCE_ORDER.index(pred.chance) if pred.chance in CHANCE_ORDER else 99
    margin = -(pred.weighted_margin or -999.0)  # negate so higher margin sorts first
    return (chance_idx, margin, pred.college_name)


def _build_shortlist_balanced(
    mcc_preds: list[CollegePrediction],
    kea_preds: list[CollegePrediction],
    top_n: int,
) -> list[CollegeEntry]:
    """Build shortlist ensuring both MCC and KEA are represented.

    Allocates slots proportionally, with a minimum of 30% for each
    authority that has usable predictions.
    """
    def _usable(preds):
        u = [p for p in preds if p.chance != "Insufficient data"]
        u.sort(key=_sort_key)
        return u

    mcc_usable = _usable(mcc_preds)
    kea_usable = _usable(kea_preds)

    if not mcc_usable and not kea_usable:
        # Fall back to insufficient data
        all_preds = mcc_preds + kea_preds
        all_preds.sort(key=_sort_key)
        return [_pred_to_entry(p) for p in all_preds[:top_n]]

    # Allocate: if both have data, give each at least 30% of slots
    if mcc_usable and kea_usable:
        min_each = max(top_n * 3 // 10, 5)  # at least 30% or 5
        mcc_slots = max(min_each, top_n - min_each)
        kea_slots = max(min_each, top_n - mcc_slots)
        # Rebalance if one has fewer than allocated
        if len(mcc_usable) < mcc_slots:
            kea_slots += mcc_slots - len(mcc_usable)
            mcc_slots = len(mcc_usable)
        if len(kea_usable) < kea_slots:
            mcc_slots += kea_slots - len(kea_usable)
            kea_slots = len(kea_usable)
    elif mcc_usable:
        mcc_slots, kea_slots = top_n, 0
    else:
        mcc_slots, kea_slots = 0, top_n

    selected = mcc_usable[:mcc_slots] + kea_usable[:kea_slots]
    selected.sort(key=_sort_key)
    return [_pred_to_entry(p) for p in selected[:top_n]]


def _build_authority_summary(
    authority: str,
    preds: list[CollegePrediction],
    exploratory: bool,
) -> AuthoritySummary:
    """Build summary counts for one authority."""
    counts: dict[str, int] = {}
    for p in preds:
        counts[p.chance] = counts.get(p.chance, 0) + 1

    by_chance = [
        ChanceBucket(label=label, count=counts[label])
        for label in CHANCE_ORDER
        if label in counts
    ]

    return AuthoritySummary(
        authority=authority,
        total=len(preds),
        by_chance=by_chance,
        exploratory=exploratory,
    )
