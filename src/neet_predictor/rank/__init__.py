"""Rank estimation subpackage (Phase 1B-B/C: Marks-to-AIR estimator)."""

from neet_predictor.rank.calibration import NormalizationMode, YearNormParams
from neet_predictor.rank.estimator import (
    RankEstimator,
    RankEstimate,
    run_validation,
    compare_normalization_strategies,
)

__all__ = [
    "RankEstimator",
    "RankEstimate",
    "run_validation",
    "compare_normalization_strategies",
    "NormalizationMode",
    "YearNormParams",
]
