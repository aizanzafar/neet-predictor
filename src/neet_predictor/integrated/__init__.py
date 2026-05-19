"""Integrated prediction subpackage (Phase 1C/1D: Marks/AIR → College)."""

from neet_predictor.integrated.pipeline import (
    UnifiedInput,
    UnifiedResult,
    run_prediction,
)
from neet_predictor.integrated.explainer import format_unified_result
from neet_predictor.integrated.summary import (
    StudentResult,
    build_student_result,
)

__all__ = [
    "UnifiedInput",
    "UnifiedResult",
    "run_prediction",
    "format_unified_result",
    "StudentResult",
    "build_student_result",
]
