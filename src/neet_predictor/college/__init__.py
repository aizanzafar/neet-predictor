"""College prediction subpackage (Phase 1B-A: AIR-based predictor)."""

from neet_predictor.college.eligibility import CandidateProfile
from neet_predictor.college.predictor import predict, PredictionResult, CollegePrediction
from neet_predictor.college.explainer import format_results

__all__ = [
    "CandidateProfile",
    "predict",
    "PredictionResult",
    "CollegePrediction",
    "format_results",
]
