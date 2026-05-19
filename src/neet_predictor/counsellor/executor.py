"""Layer 3: Deterministic Executor — runs prediction engine per scenario.

No LLM involved. Calls the existing run_prediction() + build_student_result().
"""

from __future__ import annotations

from neet_predictor.counsellor.models import ScenarioResult, ScenarioSpec
from neet_predictor.config import VALIDATION_YEAR
from neet_predictor.integrated.pipeline import UnifiedInput, run_prediction
from neet_predictor.integrated.summary import StudentResult, build_student_result


def _spec_to_unified_input(spec: ScenarioSpec) -> UnifiedInput:
    """Convert a ScenarioSpec to the engine's UnifiedInput."""
    # Map course_pref: engine expects "MBBS" or "BDS", not "MBBS+BDS"
    # For MBBS+BDS, we pass "MBBS" (engine returns both MBBS and BDS)
    course = spec.course_pref if spec.course_pref != "MBBS+BDS" else "MBBS"

    return UnifiedInput(
        marks=spec.marks,
        actual_air=spec.actual_air,
        national_category=spec.national_category,
        home_state=spec.home_state,
        pwd=spec.pwd,
        karnataka_interest=spec.karnataka_interest,
        karnataka_domicile=spec.karnataka_domicile,
        karnataka_category=spec.karnataka_category,
        course_pref=course,
        college_type_pref=spec.college_type_pref,
        target_year=spec.target_year or VALIDATION_YEAR,
    )


def execute_scenario(spec: ScenarioSpec) -> ScenarioResult:
    """Run one scenario through the deterministic prediction engine."""
    try:
        unified_input = _spec_to_unified_input(spec)
        unified_result = run_prediction(unified_input)
        student_result = build_student_result(unified_result)
        return ScenarioResult(spec=spec, student_result=student_result, error=None)
    except Exception as e:
        return ScenarioResult(spec=spec, student_result=None, error=str(e))  # type: ignore[arg-type]


def execute_all(scenarios: list[ScenarioSpec]) -> list[ScenarioResult]:
    """Run all scenarios. Returns results in same order."""
    return [execute_scenario(spec) for spec in scenarios]
