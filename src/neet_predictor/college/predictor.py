"""AIR-based college prediction engine.

Uses Round 1 closing ranks as the primary signal.
Later rounds (R2, MOPUP, STRAY) are shown as supplementary evidence only.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd

from neet_predictor.config import YEAR_WEIGHTS
from neet_predictor.dataio.loader import load_closing_ranks, load_colleges
from neet_predictor.college.eligibility import (
    CandidateProfile,
    get_mcc_eligible_categories,
    get_kea_eligible_categories,
)


# ── Data normalization ──
# MCC categories have both "X PwD" and "PwD X" forms in the data.
# Normalize to "PwD X" consistently.
_CATEGORY_NORMALIZE: dict[str, str] = {
    "Open PwD": "PwD Open",
    "OBC PwD": "PwD OBC",
    "SC PwD": "PwD SC",
    "ST PwD": "PwD ST",
    "EWS PwD": "PwD EWS",
}

# PDF-parsing artifacts in quota names.
_QUOTA_NORMALIZE: dict[str, str] = {
    "Deemed/Pai d Seats Quota": "Deemed/Paid Seats Quota",
    "Employees State Insurance Scheme(ESI )": "Employees State Insurance Scheme(ESI)",
    "Non- Resident Indian": "Non-Resident Indian",
    "Non- Resident Indian(AMU) Quota": "Non-Resident Indian(AMU) Quota",
    "Delhi NCR Children/Wi dows of Personnel of the Armed Forces (CW) Quota": (
        "Delhi NCR Children/Widows of Personnel of the Armed Forces (CW) Quota"
    ),
}

# MCC quotas accessible per college_type_pref (universally eligible quotas).
_QUOTA_GROUPS: dict[str, set[str]] = {
    "any": {"All India", "Open Seat Quota", "Deemed/Paid Seats Quota", "AMS"},
    "government": {"All India"},
    "deemed": {"Deemed/Paid Seats Quota"},
    "central": {"AMS", "Open Seat Quota"},
    "AIIMS": {"AMS"},
}

# Minimum R1 years for a real prediction.
MIN_R1_YEARS = 2

# ── Chance thresholds (conservative) ──
# Safe: admitted ALL years, min margin >= 20%, 3+ years of data.
# Likely: admitted ALL years (any margin > 0).
# Borderline: admitted SOME years, or weighted margin >= -10%.
# Unlikely: everything else.
SAFE_MIN_MARGIN = 0.20
SAFE_MIN_YEARS = 3
BORDERLINE_WEIGHTED_FLOOR = -0.10


@dataclass
class CollegePrediction:
    """Single (college, category, quota) prediction."""

    college_id: int
    college_name: str
    state: str
    course: str
    authority: str
    category: str
    quota: str
    chance: str  # Safe / Likely / Borderline / Unlikely / Insufficient data
    r1_closing_ranks: dict[int, int]
    r1_years_count: int
    supplementary_rounds: dict[str, dict[int, int]]
    weighted_margin: float | None
    confidence_notes: list[str] = field(default_factory=list)


@dataclass
class PredictionResult:
    """Complete prediction output for a candidate."""

    profile: CandidateProfile
    mcc_predictions: list[CollegePrediction]
    kea_predictions: list[CollegePrediction]
    kea_exploratory: bool
    summary: dict


# ── Internal helpers ──


def normalize_closing_ranks(df: pd.DataFrame) -> pd.DataFrame:
    """Normalize category names and quotas; remove pseudo-categories."""
    df = df.copy()
    df["category"] = df["category"].replace(_CATEGORY_NORMALIZE)
    df["quota"] = df["quota"].fillna("").replace(_QUOTA_NORMALIZE)
    df = df[df["category"] != "Reported"]
    return df


def classify_chance(
    air: int,
    r1_data: dict[int, int],
    year_weights: dict[int, float] | None = None,
) -> tuple[str, float | None]:
    """Classify admission chance for one (college, category, quota) combo.

    Returns (chance_label, weighted_margin).

    Conservative rules:
    - < 2 R1 years → "Insufficient data"
    - Admitted ALL years AND min_margin >= 20% AND 3+ years → "Safe"
    - Admitted ALL years → "Likely"
    - Admitted SOME years OR weighted margin >= -10% → "Borderline"
    - Otherwise → "Unlikely"
    """
    if year_weights is None:
        year_weights = YEAR_WEIGHTS

    n = len(r1_data)
    if n < MIN_R1_YEARS:
        return "Insufficient data", None

    # margin > 0 ⇒ AIR is better (lower) than closing rank ⇒ admitted
    margins = {y: (cr - air) / cr for y, cr in r1_data.items()}
    min_margin = min(margins.values())

    weights = {y: year_weights.get(y, 0.05) for y in margins}
    total_w = sum(weights.values())
    w_margin = sum(weights[y] * margins[y] for y in margins) / total_w

    admitted_all = all(m >= 0 for m in margins.values())
    admitted_any = any(m >= 0 for m in margins.values())

    # Conservative classification
    if admitted_all and min_margin >= SAFE_MIN_MARGIN and n >= SAFE_MIN_YEARS:
        return "Safe", w_margin
    if admitted_all:
        return "Likely", w_margin
    if admitted_any or w_margin >= BORDERLINE_WEIGHTED_FLOOR:
        return "Borderline", w_margin
    return "Unlikely", w_margin


# ── Main predict function ──


def predict(profile: CandidateProfile) -> PredictionResult:
    """Run college predictions for a candidate profile."""
    cr_df = normalize_closing_ranks(load_closing_ranks())
    colleges_df = load_colleges()

    # Build college lookup
    college_info: dict[int, dict] = {}
    for _, row in colleges_df.iterrows():
        college_info[int(row["college_id"])] = {
            "name": row["college_name"],
            "state": row.get("state", "Unknown"),
        }

    # ── MCC predictions ──
    mcc_cats = get_mcc_eligible_categories(profile)
    mcc_quotas = _QUOTA_GROUPS.get(profile.college_type_pref, _QUOTA_GROUPS["any"])
    mcc_preds = _predict_authority(
        profile.air, profile.course_pref, cr_df, college_info,
        "MCC", mcc_cats, mcc_quotas,
    )

    # ── KEA predictions (if interested) ──
    kea_preds: list[CollegePrediction] = []
    kea_exploratory = False
    if profile.karnataka_interest:
        kea_cats = get_kea_eligible_categories(profile)
        if profile.karnataka_domicile and not profile.karnataka_category:
            kea_exploratory = True
        kea_preds = _predict_authority(
            profile.air, profile.course_pref, cr_df, college_info,
            "KEA", kea_cats, None,  # KEA has no quota column
        )

    summary = _build_summary(mcc_preds, kea_preds)

    return PredictionResult(
        profile=profile,
        mcc_predictions=mcc_preds,
        kea_predictions=kea_preds,
        kea_exploratory=kea_exploratory,
        summary=summary,
    )


def _predict_authority(
    air: int,
    course: str,
    cr_df: pd.DataFrame,
    college_info: dict[int, dict],
    authority: str,
    categories: list[str],
    quotas: set[str] | None,
) -> list[CollegePrediction]:
    """Generate predictions for one counselling authority."""
    mask = (cr_df["authority"] == authority) & (cr_df["course"] == course)
    mask &= cr_df["category"].isin(categories)
    if quotas:
        mask &= cr_df["quota"].isin(quotas)

    filtered = cr_df[mask]
    predictions: list[CollegePrediction] = []

    for (cid, cat, quota), grp in filtered.groupby(
        ["college_id", "category", "quota"]
    ):
        r1 = grp[grp["round"] == "R1"]
        later = grp[grp["round"] != "R1"]

        r1_data = dict(
            zip(r1["year"].astype(int), r1["closing_rank"].astype(int))
        )
        chance, w_margin = classify_chance(air, r1_data)

        # Supplementary rounds
        supp: dict[str, dict[int, int]] = {}
        for rnd, rnd_grp in later.groupby("round"):
            supp[rnd] = dict(
                zip(
                    rnd_grp["year"].astype(int),
                    rnd_grp["closing_rank"].astype(int),
                )
            )

        info = college_info.get(
            int(cid), {"name": f"College {cid}", "state": "Unknown"}
        )

        notes: list[str] = []
        if len(r1_data) == 0:
            notes.append("No R1 data — prediction from later rounds only")
        elif len(r1_data) == 1:
            notes.append("Only 1 year of R1 data")
        elif len(r1_data) == 2:
            notes.append("Only 2 years of R1 data — limited confidence")

        predictions.append(
            CollegePrediction(
                college_id=int(cid),
                college_name=info["name"],
                state=info["state"],
                course=course,
                authority=authority,
                category=cat,
                quota=str(quota),
                chance=chance,
                r1_closing_ranks=r1_data,
                r1_years_count=len(r1_data),
                supplementary_rounds=supp,
                weighted_margin=w_margin,
                confidence_notes=notes,
            )
        )

    # Sort: Safe first, then Likely, Borderline, Unlikely, Insufficient data
    _ORDER = {
        "Safe": 0,
        "Likely": 1,
        "Borderline": 2,
        "Unlikely": 3,
        "Insufficient data": 4,
    }
    predictions.sort(
        key=lambda p: (_ORDER.get(p.chance, 5), p.college_name)
    )
    return predictions


def _build_summary(
    mcc_preds: list[CollegePrediction],
    kea_preds: list[CollegePrediction],
) -> dict:
    """Build a compact summary of prediction counts by chance label."""

    def _count(preds: list[CollegePrediction]) -> dict[str, int]:
        counts: dict[str, int] = {}
        for p in preds:
            counts[p.chance] = counts.get(p.chance, 0) + 1
        return counts

    return {
        "mcc_total": len(mcc_preds),
        "mcc_by_chance": _count(mcc_preds),
        "kea_total": len(kea_preds),
        "kea_by_chance": _count(kea_preds),
    }
