"""Dataclass contracts for the counsellor pipeline.

All layers communicate through these frozen/immutable structures.
No prediction logic lives here — pure data containers.
"""

from __future__ import annotations

from dataclasses import dataclass, field


# ═══════════════════════════════════════════════════════════════════════════════
# Layer 1 Output: StudentIntent
# ═══════════════════════════════════════════════════════════════════════════════

VALID_NATIONAL_CATEGORIES = frozenset({"General", "OBC", "SC", "ST", "EWS"})
VALID_KEA_CATEGORIES = frozenset({"GM", "1", "2A", "2B", "3A", "3B", "SC", "ST"})
VALID_COURSE_PREFS = frozenset({"MBBS", "BDS", "MBBS+BDS"})
VALID_COLLEGE_TYPE_PREFS = frozenset({"any", "government", "deemed"})


@dataclass(frozen=True)
class StudentIntent:
    """Structured extraction from a student's natural-language query."""

    marks: int | None
    actual_air: int | None
    national_category: str | None
    home_state: str | None
    pwd: bool
    karnataka_interest: bool
    karnataka_domicile: bool | None  # None = not stated
    karnataka_category: str | None
    course_pref: str  # "MBBS" | "BDS" | "MBBS+BDS"
    college_type_pref: str  # "any" | "government" | "deemed"
    bds_backup: bool
    target_year: int | None  # None = current year (2025)
    missing_slots: tuple[str, ...]  # required but not provided
    uncertain_slots: tuple[str, ...]  # hedged ("maybe", "I think")
    ambiguity_notes: tuple[str, ...]  # human-readable notes
    raw_query: str  # original student message


@dataclass(frozen=True)
class ClarificationNeeded:
    """Returned when critical info is missing and we must ask the student."""

    questions: tuple[str, ...]
    partial_intent: StudentIntent | None


# ═══════════════════════════════════════════════════════════════════════════════
# Layer 2 Output: ScenarioSpec
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class ScenarioSpec:
    """Describes one scenario to run through the prediction engine."""

    label: str  # e.g. "MBBS, MCC OBC"
    description: str  # why this scenario exists
    marks: int | None
    actual_air: int | None
    national_category: str
    home_state: str
    pwd: bool
    karnataka_interest: bool
    karnataka_domicile: bool
    karnataka_category: str | None
    course_pref: str
    college_type_pref: str
    target_year: int | None = None  # None = current year (2025)


# ═══════════════════════════════════════════════════════════════════════════════
# Layer 3 Output: ScenarioResult
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class ScenarioResult:
    """One scenario's prediction result."""

    spec: ScenarioSpec
    # StudentResult from the existing engine (imported at call site to avoid
    # circular imports — stored as Any here, typed in executor.py)
    student_result: object
    error: str | None = None  # non-None if prediction failed


# ═══════════════════════════════════════════════════════════════════════════════
# Layer 4 Output: ScenarioComparison
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class ComparisonRow:
    """Summary of one scenario for the comparison table."""

    label: str
    safe_count: int
    likely_count: int
    borderline_count: int
    total_options: int
    best_college: str | None
    best_chance: str | None
    authority_split: str  # "MCC: 15, KEA: 8"


@dataclass(frozen=True)
class ScenarioComparison:
    """Cross-scenario comparison output."""

    results: tuple[ScenarioResult, ...]
    comparison_table: tuple[ComparisonRow, ...]
    best_scenario_label: str | None
    notes: tuple[str, ...]


# ═══════════════════════════════════════════════════════════════════════════════
# Layer 5 Output: CounsellingNarrative
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class CounsellingNarrative:
    """LLM-generated counselling text."""

    summary: str  # 2-3 sentence conclusion
    primary_path: str  # recommended strategy
    backup_path: str | None  # alternative
    top_colleges: list[str]  # from shortlists ONLY
    risk_areas: list[str]
    missing_data_caveats: list[str]
    full_narrative: str  # complete LLM text
    model_used: str
    raw_llm_response: str  # for debugging
    tokens_used: int | None = None


# ═══════════════════════════════════════════════════════════════════════════════
# Layer 6 Output: ValidatedResponse (FINAL output)
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class ValidatedResponse:
    """Final validated output — the contract delivered to consumers."""

    narrative: CounsellingNarrative | None  # None if validation failed
    scenarios: ScenarioComparison
    validation_passed: bool
    violations: list[str]  # what the LLM got wrong
    fallback_used: bool  # True = narrative stripped, raw results shown
    warnings: list[str]  # merged from engine
    limitations: list[str]  # always shown
    processing_time_ms: int = 0
