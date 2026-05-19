"""Counsellor module — LLM-based reasoning layer for NEET UG prediction.

Wraps the deterministic prediction engine with natural-language
intent parsing and narrative generation using Siemens LLM API.
"""

from neet_predictor.counsellor.llm_client import LLMClient, LLMClientError
from neet_predictor.counsellor.models import (
    ClarificationNeeded,
    CounsellingNarrative,
    ScenarioComparison,
    StudentIntent,
    ValidatedResponse,
)
from neet_predictor.counsellor.orchestrator import run_counsellor, run_counsellor_with_intent

__all__ = [
    "LLMClient",
    "LLMClientError",
    "ClarificationNeeded",
    "CounsellingNarrative",
    "ScenarioComparison",
    "StudentIntent",
    "ValidatedResponse",
    "run_counsellor",
    "run_counsellor_with_intent",
]
