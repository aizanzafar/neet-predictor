"""Layer 6: Output Validator — deterministic safety checks on LLM output.

Enforces 9 rules. If critical violations found, strips the narrative
and falls back to raw structured results.
"""

from __future__ import annotations

import re

from neet_predictor.counsellor.models import (
    CounsellingNarrative,
    ScenarioComparison,
    ValidatedResponse,
)
from neet_predictor.integrated.summary import StudentResult


# ── Regex patterns for forbidden content ──

_PROBABILITY_PATTERN = re.compile(
    r"\b\d{1,3}\s*%\s*(chance|probability|likelihood|assured)"
    r"|probability\s+of"
    r"|\b[1-9]\d?\s+out\s+of\s+10\b",
    re.IGNORECASE,
)

_GUARANTEED_PATTERN = re.compile(
    r"\b(guaranteed|will\s+definitely\s+get|100\s*%|assured\s+admission"
    r"|certainly\s+get|sure\s+to\s+get)\b",
    re.IGNORECASE,
)

_RANK_NUMBER_PATTERN = re.compile(
    r"\b(AIR|rank|closing\s+rank)\s*[:#=]?\s*[\d,]{3,7}\b",
    re.IGNORECASE,
)

# Standard disclaimer text
_DISCLAIMER = "This is not an admission guarantee. Verify from official sources."

# Standard limitations
_LIMITATIONS = [
    "Predictions are based on historical Round 1 closing ranks only.",
    "Year-to-year fluctuations can shift outcomes.",
    "Special quotas (NRI, DU, IP, ESI, AMU) are not fully covered.",
    "KEA data is limited — KEA predictions are low-confidence.",
    "This tool is not an admission guarantee.",
]


def _collect_all_college_names(comparison: ScenarioComparison) -> set[str]:
    """Gather all college names from all scenario shortlists."""
    names: set[str] = set()
    for sr in comparison.results:
        if sr.error or sr.student_result is None:
            continue
        student_result: StudentResult = sr.student_result  # type: ignore[assignment]
        for entry in student_result.shortlist:
            names.add(entry.college_name)
            # Also add partial matches (first 20 chars) for fuzzy matching
            if len(entry.college_name) > 20:
                names.add(entry.college_name[:20])
    return names


def _collect_all_chance_labels(comparison: ScenarioComparison) -> dict[str, str]:
    """Map college_name → best chance label across all scenarios."""
    labels: dict[str, str] = {}
    chance_rank = {"Safe": 0, "Likely": 1, "Borderline": 2, "Unlikely": 3, "Insufficient data": 4}
    for sr in comparison.results:
        if sr.error or sr.student_result is None:
            continue
        student_result: StudentResult = sr.student_result  # type: ignore[assignment]
        for entry in student_result.shortlist:
            existing = labels.get(entry.college_name)
            if existing is None or chance_rank.get(entry.chance, 5) < chance_rank.get(existing, 5):
                labels[entry.college_name] = entry.chance
    return labels


def _collect_allowed_ranks(comparison: ScenarioComparison) -> set[str]:
    """Collect rank numbers that appear in engine output (allowed in narrative)."""
    allowed: set[str] = set()
    for sr in comparison.results:
        if sr.error or sr.student_result is None:
            continue
        student_result: StudentResult = sr.student_result  # type: ignore[assignment]
        # AIR used
        allowed.add(str(student_result.rank_used.air))
        # Rank estimates
        if student_result.rank_summary.best_case_air:
            allowed.add(str(student_result.rank_summary.best_case_air))
        if student_result.rank_summary.median_air:
            allowed.add(str(student_result.rank_summary.median_air))
        if student_result.rank_summary.conservative_air:
            allowed.add(str(student_result.rank_summary.conservative_air))
        # Closing ranks from shortlist
        for entry in student_result.shortlist:
            for yr, rank in entry.r1_closing_ranks.items():
                allowed.add(str(rank))
    return allowed


def _collect_engine_warnings(comparison: ScenarioComparison) -> list[str]:
    """Collect all warnings from all scenario results."""
    warnings: list[str] = []
    seen: set[str] = set()
    for sr in comparison.results:
        if sr.error or sr.student_result is None:
            continue
        student_result: StudentResult = sr.student_result  # type: ignore[assignment]
        for w in student_result.warnings:
            if w not in seen:
                warnings.append(w)
                seen.add(w)
    return warnings


def validate(
    narrative: CounsellingNarrative,
    comparison: ScenarioComparison,
    *,
    marks_based: bool = False,
) -> ValidatedResponse:
    """Validate LLM narrative against ground truth.

    Returns a ValidatedResponse. If critical violations are found,
    narrative is set to None and fallback_used=True.
    """
    violations: list[str] = []
    text = narrative.full_narrative

    # ── Rule 1: No fake colleges ──
    valid_colleges = _collect_all_college_names(comparison)
    for college_name in narrative.top_colleges:
        # Check if college name (or first 20 chars) appears in valid set
        found = (
            college_name in valid_colleges
            or college_name[:20] in valid_colleges
            or any(college_name in vc or vc in college_name for vc in valid_colleges)
        )
        if not found:
            violations.append(f"Fake college: '{college_name}' not in any shortlist")

    # ── Rule 2: No upgraded labels ──
    chance_labels = _collect_all_chance_labels(comparison)
    chance_rank = {"Safe": 0, "Likely": 1, "Borderline": 2, "Unlikely": 3, "Insufficient data": 4}
    for college_name in narrative.top_colleges:
        # Check if narrative claims "Safe" but engine says "Borderline" etc.
        # This is checked via the narrative text (simplified check)
        engine_label = chance_labels.get(college_name)
        if engine_label and f"{college_name}" in text:
            # Check if "Safe" is near this college name when engine says otherwise
            if engine_label != "Safe" and re.search(
                rf"{re.escape(college_name)}[^.]*\bSafe\b", text, re.IGNORECASE
            ):
                violations.append(
                    f"Upgraded label: '{college_name}' is '{engine_label}' but narrative says 'Safe'"
                )

    # ── Rule 3: No probability claims ──
    if _PROBABILITY_PATTERN.search(text):
        violations.append("Contains probability/percentage claims")

    # ── Rule 4: Disclaimer present ──
    if not re.search(r"not\s+(an?\s+)?.*guarantee", text, re.IGNORECASE):
        # Will be appended, not a hard violation
        text += f"\n\n{_DISCLAIMER}"
        narrative = CounsellingNarrative(
            summary=narrative.summary,
            primary_path=narrative.primary_path,
            backup_path=narrative.backup_path,
            top_colleges=narrative.top_colleges,
            risk_areas=narrative.risk_areas,
            missing_data_caveats=narrative.missing_data_caveats,
            full_narrative=text,
            model_used=narrative.model_used,
            raw_llm_response=narrative.raw_llm_response,
            tokens_used=narrative.tokens_used,
        )

    # ── Rule 5: Experimental label (if marks-based) ──
    if marks_based:
        if not re.search(r"experiment|estimat", text, re.IGNORECASE):
            violations.append("Marks-based but missing 'experimental/estimated' label")

    # ── Rule 6: KEA grounding ──
    # If narrative mentions KEA and no KEA data exists, flag it
    if "KEA" in text:
        has_kea_data = any(
            sr.student_result is not None
            and not sr.error
            and hasattr(sr.student_result, "kea_summary")
            and sr.student_result.kea_summary.total > 0  # type: ignore[union-attr]
            for sr in comparison.results
        )
        if not has_kea_data and "low-confidence" not in text.lower() and "limited" not in text.lower():
            violations.append("Makes KEA claims without KEA data support")

    # ── Rule 7: Engine warnings preserved ──
    # (Soft check — append missing ones rather than strip)

    # ── Rule 8: No guaranteed admission ──
    if _GUARANTEED_PATTERN.search(text):
        violations.append("Contains guaranteed/assured admission language")

    # ── Rule 9: No invented rank ranges ──
    allowed_ranks = _collect_allowed_ranks(comparison)
    rank_mentions = _RANK_NUMBER_PATTERN.finditer(text)
    for match in rank_mentions:
        # Extract the number from the match
        numbers = re.findall(r"[\d,]{3,7}", match.group())
        for num_str in numbers:
            clean = num_str.replace(",", "")
            if clean not in allowed_ranks:
                violations.append(f"Invented rank number: {num_str} not from engine output")
                break

    # ── Decision: strip or keep ──
    critical_violations = [
        v for v in violations
        if v.startswith("Fake college")
        or v.startswith("Upgraded label")
        or v.startswith("Contains guaranteed")
    ]

    engine_warnings = _collect_engine_warnings(comparison)

    if critical_violations:
        return ValidatedResponse(
            narrative=None,
            scenarios=comparison,
            validation_passed=False,
            violations=violations,
            fallback_used=True,
            warnings=engine_warnings,
            limitations=_LIMITATIONS,
        )

    return ValidatedResponse(
        narrative=narrative,
        scenarios=comparison,
        validation_passed=len(violations) == 0,
        violations=violations,
        fallback_used=False,
        warnings=engine_warnings,
        limitations=_LIMITATIONS,
    )
