"""Paper-difficulty normalization for marks-to-AIR estimation.

When exam difficulty varies across years, raw marks are not directly comparable.
A harder paper (lower topper score) compresses scores downward, making the same
numerical marks correspond to a better rank.

This module provides normalization strategies that map query marks from the
target year's scale to each training year's scale before curve interpolation.

Strategies
----------
NONE
    No normalization.  Baseline behaviour (Phase 1B-B).
TOPPER_SCORE
    Single-point linear scaling using highest score achieved in each year.
    ``normalized = marks × (training_highest / target_highest)``
AFFINE_TWO_POINT
    Two-point affine mapping using both the topper score and the UR qualifying
    cutoff.  This anchors both ends of the "meaningful" marks range.
    ``normalized = train_cutoff + (marks − target_cutoff)
                   × (train_highest − train_cutoff)
                   / (target_highest − target_cutoff)``
"""

from __future__ import annotations

from enum import Enum
from typing import NamedTuple

from neet_predictor.config import MAX_MARKS, MIN_MARKS


# ── Public types ────────────────────────────────────────


class NormalizationMode(Enum):
    """Paper-difficulty normalization strategy."""

    NONE = "none"
    TOPPER_SCORE = "topper_score"
    AFFINE_TWO_POINT = "affine_two_point"
    PIECEWISE_AFFINE = "piecewise_affine"


class YearNormParams(NamedTuple):
    """Normalization parameters for a single exam year."""

    year: int
    highest_marks: int  # max score achieved (e.g. 686 for 2025)
    cutoff_ur: int  # UR qualifying cutoff marks
    toppers_at_highest: int = 1  # number of candidates at highest score
    appeared: int = 0  # appeared candidates


# ── Normalization functions ─────────────────────────────


def normalize_marks_topper(
    marks: float,
    target_highest: int,
    training_highest: int,
) -> float:
    """Scale *marks* from target-year scale to training-year scale.

    Uses ratio of highest achieved scores.  When target paper was harder
    (lower ``target_highest``), the same raw marks maps to *higher* marks
    on the training year's (easier) scale, reflecting better performance.

    Clamped to [0, MAX_MARKS].
    """
    if target_highest <= 0 or training_highest <= 0:
        return float(marks)
    normalized = marks * (training_highest / target_highest)
    return max(float(MIN_MARKS), min(float(MAX_MARKS), normalized))


def normalize_marks_affine(
    marks: float,
    target_highest: int,
    target_cutoff: int,
    training_highest: int,
    training_cutoff: int,
) -> float:
    """Two-point affine mapping from target to training scale.

    Maps ``[target_cutoff, target_highest]`` → ``[training_cutoff, training_highest]``
    linearly.  Extrapolates below cutoff (clamped to [0, MAX_MARKS]).

    This is more robust than topper-only scaling when cutoff marks also
    shifted significantly between years.
    """
    target_range = target_highest - target_cutoff
    training_range = training_highest - training_cutoff
    if target_range <= 0 or training_range <= 0:
        return float(marks)
    normalized = training_cutoff + (marks - target_cutoff) * (
        training_range / target_range
    )
    return max(float(MIN_MARKS), min(float(MAX_MARKS), normalized))


_TOP_BAND_FRACTION = 0.10  # top 10% of marks range gets extra compression


def normalize_marks_piecewise_affine(
    marks: float,
    target_highest: int,
    target_cutoff: int,
    training_highest: int,
    training_cutoff: int,
    target_toppers: int = 1,
    target_appeared: int = 0,
    training_toppers: int = 1,
    training_appeared: int = 0,
) -> float:
    """Piecewise affine with top-band compression.

    Below the top band (marks < 90% of target_highest): identical to
    ``normalize_marks_affine``.

    In the top band (marks >= 90% of target_highest): apply additional
    non-linear compression.  The compression factor is derived from the
    ratio of *topper densities* (toppers_at_highest / appeared) between
    target and training years.  When the target paper is harder, fewer
    students crowd at the top, so each marks increment in the top band
    spans more ranks proportionally.  The compression stretches the
    normalised marks toward the training year's maximum more aggressively
    than plain affine.

    The factor is bounded: at most ×1.05 additional stretch beyond affine,
    to avoid over-correcting.
    """
    # Start with affine as the baseline
    base = normalize_marks_affine(
        marks, target_highest, target_cutoff, training_highest, training_cutoff
    )

    # Only compress in the top band
    top_threshold = target_highest * (1.0 - _TOP_BAND_FRACTION)
    if marks < top_threshold:
        return base

    # How far into the top band (0 at threshold, 1 at highest)
    top_range = target_highest - top_threshold
    if top_range <= 0:
        return base
    t = (marks - top_threshold) / top_range  # 0..1

    # Compute topper density ratio
    if target_appeared > 0 and training_appeared > 0:
        target_density = max(target_toppers, 1) / target_appeared
        training_density = max(training_toppers, 1) / training_appeared
        # Ratio < 1 means target top is less dense → harder paper
        density_ratio = target_density / training_density
    else:
        density_ratio = 1.0

    # Compression boost: when density_ratio < 1 (harder paper), the top band
    # should stretch further toward training_highest.  Cap at 5%.
    if density_ratio < 1.0:
        boost = min(0.05, (1.0 - density_ratio) * 0.10)
    else:
        boost = 0.0

    # Affine-normalised top of range
    affine_at_highest = normalize_marks_affine(
        target_highest, target_highest, target_cutoff,
        training_highest, training_cutoff,
    )
    affine_at_threshold = normalize_marks_affine(
        top_threshold, target_highest, target_cutoff,
        training_highest, training_cutoff,
    )
    affine_top_range = affine_at_highest - affine_at_threshold
    if affine_top_range <= 0:
        return base

    # Apply power-law stretch: t^(1-boost) pushes the curve slightly upward
    # in the top band, mapping to higher training-year marks.
    t_stretched = t ** max(0.5, 1.0 - boost)  # bounded power
    compressed = affine_at_threshold + t_stretched * affine_top_range

    return max(float(MIN_MARKS), min(float(MAX_MARKS), compressed))


def normalize_marks(
    marks: float,
    mode: NormalizationMode,
    target_params: YearNormParams,
    training_params: YearNormParams,
) -> float:
    """Dispatch to the appropriate normalization strategy."""
    if mode == NormalizationMode.NONE:
        return float(marks)
    if mode == NormalizationMode.TOPPER_SCORE:
        return normalize_marks_topper(
            marks, target_params.highest_marks, training_params.highest_marks
        )
    if mode == NormalizationMode.AFFINE_TWO_POINT:
        return normalize_marks_affine(
            marks,
            target_params.highest_marks,
            target_params.cutoff_ur,
            training_params.highest_marks,
            training_params.cutoff_ur,
        )
    if mode == NormalizationMode.PIECEWISE_AFFINE:
        return normalize_marks_piecewise_affine(
            marks,
            target_params.highest_marks,
            target_params.cutoff_ur,
            training_params.highest_marks,
            training_params.cutoff_ur,
            target_toppers=target_params.toppers_at_highest,
            target_appeared=target_params.appeared,
            training_toppers=training_params.toppers_at_highest,
            training_appeared=training_params.appeared,
        )
    return float(marks)
