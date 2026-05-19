"""Orchestrator — wires all 6 layers into a single pipeline entry point.

Flow:
  Query → [Intent Parser (LLM)] → [Slot Resolver] → [Executor] →
  [Comparator] → [Reasoner (LLM)] → [Validator] → ValidatedResponse

Only 2 LLM calls total. Everything else is deterministic.
"""

from __future__ import annotations

import time

from neet_predictor.counsellor.comparator import compare_scenarios
from neet_predictor.counsellor.executor import execute_all
from neet_predictor.counsellor.intent_parser import parse_intent
from neet_predictor.counsellor.llm_client import LLMClient, LLMClientError
from neet_predictor.counsellor.models import (
    ClarificationNeeded,
    CounsellingNarrative,
    ScenarioComparison,
    StudentIntent,
    ValidatedResponse,
)
from neet_predictor.counsellor.reasoner import generate_narrative
from neet_predictor.counsellor.slot_resolver import resolve_slots
from neet_predictor.counsellor.validator import validate


def run_counsellor(
    query: str,
    *,
    client: LLMClient | None = None,
) -> ValidatedResponse | ClarificationNeeded:
    """Full counsellor pipeline: query → validated response.

    Args:
        query: Free-text student query
        client: Optional LLM client (created from env if not provided)

    Returns:
        ValidatedResponse on success, ClarificationNeeded if info is missing.

    Raises:
        LLMClientError: If LLM calls fail after retries
    """
    start_ms = time.perf_counter()

    if client is None:
        client = LLMClient()

    # ── Layer 1: Intent Parser (LLM call #1) ──
    intent: StudentIntent = parse_intent(query, client)

    # ── Layer 2: Slot Resolver (deterministic) ──
    resolved = resolve_slots(intent)

    if isinstance(resolved, ClarificationNeeded):
        return resolved

    scenarios = resolved  # list[ScenarioSpec]

    # ── Layer 3: Executor (deterministic) ──
    results = execute_all(scenarios)

    # ── Layer 4: Comparator (deterministic) ──
    comparison: ScenarioComparison = compare_scenarios(results)

    # ── Layer 5: Reasoner (LLM call #2) ──
    narrative: CounsellingNarrative = generate_narrative(intent, comparison, client)

    # ── Layer 6: Validator (deterministic) ──
    marks_based = intent.marks is not None and intent.actual_air is None
    validated: ValidatedResponse = validate(
        narrative, comparison, marks_based=marks_based
    )

    # Record timing
    elapsed_ms = int((time.perf_counter() - start_ms) * 1000)
    validated = ValidatedResponse(
        narrative=validated.narrative,
        scenarios=validated.scenarios,
        validation_passed=validated.validation_passed,
        violations=validated.violations,
        fallback_used=validated.fallback_used,
        warnings=validated.warnings,
        limitations=validated.limitations,
        processing_time_ms=elapsed_ms,
    )

    return validated


def run_counsellor_with_intent(
    intent: StudentIntent,
    *,
    client: LLMClient | None = None,
) -> ValidatedResponse | ClarificationNeeded:
    """Run pipeline from a pre-parsed intent (skips Layer 1).

    Useful for testing or when intent is built programmatically.
    """
    start_ms = time.perf_counter()

    if client is None:
        client = LLMClient()

    # ── Layer 2: Slot Resolver ──
    resolved = resolve_slots(intent)
    if isinstance(resolved, ClarificationNeeded):
        return resolved

    scenarios = resolved

    # ── Layer 3: Executor ──
    results = execute_all(scenarios)

    # ── Layer 4: Comparator ──
    comparison: ScenarioComparison = compare_scenarios(results)

    # ── Layer 5: Reasoner (LLM call) ──
    narrative: CounsellingNarrative = generate_narrative(intent, comparison, client)

    # ── Layer 6: Validator ──
    marks_based = intent.marks is not None and intent.actual_air is None
    validated: ValidatedResponse = validate(
        narrative, comparison, marks_based=marks_based
    )

    elapsed_ms = int((time.perf_counter() - start_ms) * 1000)
    validated = ValidatedResponse(
        narrative=validated.narrative,
        scenarios=validated.scenarios,
        validation_passed=validated.validation_passed,
        violations=validated.violations,
        fallback_used=validated.fallback_used,
        warnings=validated.warnings,
        limitations=validated.limitations,
        processing_time_ms=elapsed_ms,
    )

    return validated
