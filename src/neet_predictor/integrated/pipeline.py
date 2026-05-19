"""Unified Marks/AIR → College prediction pipeline.

Supports three flows:
  A. Actual AIR only → direct college prediction.
  B. Marks only → estimate AIR, then college prediction using conservative AIR.
  C. Marks + actual AIR → college prediction using actual AIR,
     marks-based estimate shown for comparison only.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from neet_predictor.config import MAX_MARKS, MAX_YEAR, MIN_MARKS, VALIDATION_YEAR
from neet_predictor.rank.calibration import NormalizationMode
from neet_predictor.rank.estimator import RankEstimator, RankEstimate
from neet_predictor.college.eligibility import CandidateProfile
from neet_predictor.college.predictor import predict, PredictionResult


# ── Valid values ──

VALID_NATIONAL_CATEGORIES = frozenset({"General", "OBC", "SC", "ST", "EWS"})

# KEA categories that a user may supply.  We never infer these from national.
VALID_KEA_CATEGORIES = frozenset({
    "GM", "1", "2A", "2B", "3A", "3B", "SC", "ST",
})

# ── Warnings ──

_WARN_HISTORICAL = (
    "Prediction is based on historical data and is not an admission guarantee."
)
_WARN_MARKS_EXPERIMENTAL = (
    "Marks-to-AIR estimator is experimental and medium confidence. "
    "Exact AIR cannot be predicted from marks alone."
)
_WARN_ESTIMATED_AIR_USED = (
    "College prediction uses conservative estimated AIR because actual AIR "
    "was not provided. College predictions are therefore lower-confidence."
)
_WARN_ACTUAL_AIR_USED = (
    "Actual AIR was provided, so college prediction uses actual AIR, "
    "not estimated AIR."
)
_WARN_MCC_KEA_VERIFY = (
    "MCC and KEA eligibility/category rules must be verified from "
    "official documents."
)
_WARN_KEA_SPARSE = (
    "KEA predictions are limited because KEA R1 data is sparse."
)


# ── Input model ──

@dataclass(frozen=True)
class UnifiedInput:
    """Unified input for the integrated prediction pipeline.

    At least one of ``marks`` or ``actual_air`` must be provided.
    """

    national_category: str
    home_state: str
    marks: int | None = None
    actual_air: int | None = None
    pwd: bool = False
    karnataka_interest: bool = False
    karnataka_domicile: bool = False
    karnataka_category: str | None = None
    course_pref: str = "MBBS"
    college_type_pref: str = "any"
    target_year: int = VALIDATION_YEAR
    normalization: NormalizationMode = NormalizationMode.AFFINE_TWO_POINT

    def __post_init__(self) -> None:
        # At least one of marks or actual_air
        if self.marks is None and self.actual_air is None:
            raise ValueError(
                "At least one of 'marks' or 'actual_air' must be provided."
            )

        # Marks range
        if self.marks is not None:
            if not (MIN_MARKS <= self.marks <= MAX_MARKS):
                raise ValueError(
                    f"marks must be between {MIN_MARKS} and {MAX_MARKS}, "
                    f"got {self.marks}."
                )

        # AIR positive
        if self.actual_air is not None:
            if self.actual_air < 1:
                raise ValueError(
                    f"actual_air must be a positive integer, got {self.actual_air}."
                )

        # National category
        if self.national_category not in VALID_NATIONAL_CATEGORIES:
            raise ValueError(
                f"national_category must be one of {sorted(VALID_NATIONAL_CATEGORIES)}, "
                f"got '{self.national_category}'."
            )

        # Karnataka category must not be auto-derived
        if self.karnataka_category is not None:
            if self.karnataka_category not in VALID_KEA_CATEGORIES:
                raise ValueError(
                    f"karnataka_category must be one of {sorted(VALID_KEA_CATEGORIES)}, "
                    f"got '{self.karnataka_category}'."
                )


# ── Rank-used descriptor ──

@dataclass(frozen=True)
class RankUsed:
    """Describes which AIR was used for college prediction and why."""

    air: int
    source: str  # "actual" | "estimated_conservative"
    explanation: str


# ── Result model ──

@dataclass
class UnifiedResult:
    """Complete output of the integrated pipeline."""

    input: UnifiedInput

    # Rank section
    rank_estimate: RankEstimate | None  # None when actual AIR only
    rank_used: RankUsed

    # College section
    college_predictions: PredictionResult

    # Warnings
    warnings: list[str] = field(default_factory=list)


# ── Pipeline ──

def run_prediction(inp: UnifiedInput) -> UnifiedResult:
    """Execute the unified prediction pipeline.

    Returns a ``UnifiedResult`` containing rank estimation (if applicable),
    the AIR used for college prediction, college predictions, and warnings.
    """
    warnings: list[str] = [_WARN_HISTORICAL]
    rank_estimate: RankEstimate | None = None

    # ── Step 1: Determine AIR ──

    has_actual = inp.actual_air is not None
    has_marks = inp.marks is not None

    if has_marks:
        # Always compute the marks-based estimate when marks are provided.
        # use_validation_data=True enables direct interpolation for all years
        # including VALIDATION_YEAR (production mode).
        estimator = RankEstimator(
            normalization=inp.normalization,
            use_validation_data=True,
        )
        rank_estimate = estimator.estimate(
            inp.marks,
            target_year=inp.target_year,
            category=inp.national_category,
        )
        warnings.append(_WARN_MARKS_EXPERIMENTAL)

    if has_actual:
        # Case A or C: use actual AIR
        air_for_college = inp.actual_air
        rank_used = RankUsed(
            air=air_for_college,
            source="actual",
            explanation=(
                "Using actual AIR provided by the user."
                if not has_marks
                else "Both marks and actual AIR provided. "
                "College prediction uses actual AIR."
            ),
        )
        warnings.append(_WARN_ACTUAL_AIR_USED if has_marks else _WARN_HISTORICAL)
    else:
        # Case B: marks only → use best-case AIR for future years (paper
        # difficulty unknown), median for known years.
        assert rank_estimate is not None
        is_future = inp.target_year > MAX_YEAR
        if is_future:
            air_for_college = rank_estimate.best_case_air
            rank_used = RankUsed(
                air=air_for_college,
                source="estimated_best_case",
                explanation=(
                    f"Future year ({inp.target_year}): using best-case AIR "
                    f"({rank_estimate.best_case_air:,}) from marks={inp.marks}. "
                    f"Range: {rank_estimate.best_case_air:,}–{rank_estimate.conservative_air:,}."
                ),
            )
        else:
            air_for_college = rank_estimate.median_air
            rank_used = RankUsed(
                air=air_for_college,
                source="estimated_median",
                explanation=(
                    f"No actual AIR provided. Using median estimated AIR "
                    f"({rank_estimate.median_air:,}) from marks={inp.marks}. "
                    f"Range: {rank_estimate.best_case_air:,}–{rank_estimate.conservative_air:,}."
                ),
            )
        warnings.append(_WARN_ESTIMATED_AIR_USED)

    # ── Step 2: Build CandidateProfile for college predictor ──

    profile = CandidateProfile(
        air=air_for_college,
        national_category=inp.national_category,
        home_state=inp.home_state,
        pwd=inp.pwd,
        course_pref=inp.course_pref,
        college_type_pref=inp.college_type_pref,
        karnataka_interest=inp.karnataka_interest,
        karnataka_domicile=inp.karnataka_domicile,
        karnataka_category=inp.karnataka_category,
    )

    # ── Step 3: Run college prediction ──

    college_result = predict(profile)

    # ── Step 4: Common warnings ──

    warnings.append(_WARN_MCC_KEA_VERIFY)
    warnings.append(_WARN_KEA_SPARSE)

    return UnifiedResult(
        input=inp,
        rank_estimate=rank_estimate,
        rank_used=rank_used,
        college_predictions=college_result,
        warnings=warnings,
    )
