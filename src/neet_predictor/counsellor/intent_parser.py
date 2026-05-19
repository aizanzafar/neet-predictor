"""Layer 1: Intent Parser — extracts structured slots from user query via LLM.

Single LLM call (deepseek-v4-flash). Converts free-text query into StudentIntent.
"""

from __future__ import annotations

from neet_predictor.counsellor.llm_client import LLMClient, LLMClientError
from neet_predictor.counsellor.models import StudentIntent
from neet_predictor.counsellor.prompts import INTENT_PARSER_SYSTEM, format_intent_user_prompt


def parse_intent(query: str, client: LLMClient) -> StudentIntent:
    """Parse a student query into structured StudentIntent.

    Args:
        query: Free-text query from the student
        client: LLM client instance

    Returns:
        StudentIntent with extracted slots

    Raises:
        LLMClientError: If LLM call fails
    """
    user_prompt = format_intent_user_prompt(query)

    parsed = client.chat_json(
        system=INTENT_PARSER_SYSTEM,
        user=user_prompt,
        model=client.primary_model,
        temperature=0.1,
        max_tokens=512,
    )

    # Determine missing/uncertain slots
    missing: list[str] = []
    if not parsed.get("national_category"):
        missing.append("national_category")
    if not parsed.get("home_state"):
        missing.append("home_state")
    if not parsed.get("marks") and not parsed.get("actual_air"):
        missing.append("marks_or_air")

    ambiguities = parsed.get("ambiguities") or []

    # Map parsed JSON to StudentIntent
    return StudentIntent(
        marks=_safe_int(parsed.get("marks")),
        actual_air=_safe_int(parsed.get("actual_air")),
        national_category=_safe_str(parsed.get("national_category")),
        home_state=_safe_str(parsed.get("home_state")),
        pwd=False,  # LLM doesn't extract PwD reliably; handled via follow-up
        karnataka_interest=_safe_bool(parsed.get("karnataka_interest")) or False,
        karnataka_domicile=_safe_bool(parsed.get("karnataka_domicile")),
        karnataka_category=_safe_str(parsed.get("karnataka_category")),
        course_pref=_safe_str(parsed.get("course_pref")) or "MBBS",
        college_type_pref=_safe_str(parsed.get("college_type_pref")) or "any",
        bds_backup=(parsed.get("course_pref") or "").upper() == "MBBS+BDS",
        target_year=_safe_int(parsed.get("target_year")),
        missing_slots=tuple(missing),
        uncertain_slots=tuple(ambiguities),
        ambiguity_notes=tuple(ambiguities),
        raw_query=query,
    )


def _safe_int(val) -> int | None:
    """Safely convert to int or None."""
    if val is None:
        return None
    try:
        return int(val)
    except (ValueError, TypeError):
        return None


def _safe_str(val) -> str | None:
    """Safely convert to str or None."""
    if val is None or val == "":
        return None
    return str(val)


def _safe_bool(val) -> bool | None:
    """Safely convert to bool or None."""
    if val is None:
        return None
    if isinstance(val, bool):
        return val
    if isinstance(val, str):
        return val.lower() in ("true", "yes", "1")
    return bool(val)
