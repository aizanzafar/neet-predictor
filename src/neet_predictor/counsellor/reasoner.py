"""Layer 5: Reasoner — generates counselling narrative via LLM.

Single LLM call (gpt-oss-120b). Takes comparison output + knowledge context,
produces CounsellingNarrative.
"""

from __future__ import annotations

import re

from neet_predictor.counsellor.knowledge import build_knowledge_context
from neet_predictor.counsellor.llm_client import LLMClient, LLMResponse
from neet_predictor.counsellor.models import (
    CounsellingNarrative,
    ScenarioComparison,
    StudentIntent,
)
from neet_predictor.counsellor.prompts import (
    format_reasoner_system_prompt,
    format_reasoner_user_prompt,
)
from neet_predictor.integrated.summary import CHANCE_ORDER, StudentResult


def _build_profile_summary(intent: StudentIntent) -> str:
    """Build a human-readable student profile for the LLM prompt."""
    parts: list[str] = []
    if intent.marks:
        parts.append(f"NEET 2025 Marks: {intent.marks}/720")
    if intent.actual_air:
        parts.append(f"AIR: {intent.actual_air}")
    if intent.national_category:
        parts.append(f"Category: {intent.national_category}")
    if intent.home_state:
        parts.append(f"Home State: {intent.home_state}")
    if intent.karnataka_interest:
        parts.append("Karnataka interest: Yes")
        if intent.karnataka_domicile:
            parts.append("Karnataka domicile: Yes")
        if intent.karnataka_category:
            parts.append(f"KEA category: {intent.karnataka_category}")
    if intent.course_pref and intent.course_pref != "MBBS":
        parts.append(f"Course preference: {intent.course_pref}")
    if intent.college_type_pref and intent.college_type_pref != "any":
        parts.append(f"College type: {intent.college_type_pref}")
    return "\n".join(parts) if parts else "No profile details available"


def _build_scenario_data(comparison: ScenarioComparison) -> str:
    """Format scenario results for LLM consumption."""
    sections: list[str] = []

    for sr in comparison.results:
        if sr.error:
            sections.append(f"### {sr.spec.label}\nError: {sr.error}")
            continue

        if sr.student_result is None:
            sections.append(f"### {sr.spec.label}\nNo results available.")
            continue

        student_result: StudentResult = sr.student_result  # type: ignore[assignment]
        lines: list[str] = [f"### {sr.spec.label}"]
        lines.append(f"Rank used: AIR {student_result.rank_used.air}")
        lines.append(f"Total options: {len(student_result.shortlist)}")
        lines.append("")

        # Top colleges by chance
        by_chance: dict[str, list[str]] = {}
        for entry in student_result.shortlist[:15]:  # cap at 15 for prompt
            label = entry.chance
            if label not in by_chance:
                by_chance[label] = []
            by_chance[label].append(
                f"  - {entry.college_name} ({entry.course}, {entry.authority})"
            )

        for chance in CHANCE_ORDER:
            if chance in by_chance:
                lines.append(f"**{chance}:**")
                lines.extend(by_chance[chance])
                lines.append("")

        # ── R2 Opportunity Analysis ──
        # Identify colleges that are Unlikely/Borderline in R1 but achievable in R2
        air_used = student_result.rank_used.air
        r2_opportunities: list[str] = []
        for entry in student_result.shortlist:
            if entry.chance not in ("Unlikely", "Borderline"):
                continue
            r2_data = entry.supplementary_rounds.get("R2", {})
            if not r2_data:
                continue
            # Check if any R2 closing rank is >= our AIR (meaning we'd get in)
            r2_achievable_years = [
                (yr, rank) for yr, rank in r2_data.items()
                if rank >= air_used
            ]
            if r2_achievable_years:
                r2_str = ", ".join(f"{yr}: {r:,}" for yr, r in sorted(r2_achievable_years))
                r1_latest = max(entry.r1_closing_ranks.items(), key=lambda x: x[0]) if entry.r1_closing_ranks else None
                r1_info = f"R1={r1_latest[1]:,} ({r1_latest[0]})" if r1_latest else "no R1"
                r2_opportunities.append(
                    f"  - {entry.college_name}: {entry.chance} in R1 ({r1_info}), "
                    f"but achievable in R2 ({r2_str})"
                )

        if r2_opportunities:
            lines.append("**R2 Round Opportunities (historically achievable in later rounds):**")
            lines.extend(r2_opportunities[:8])  # cap at 8
            lines.append("")

        # Warnings
        if student_result.warnings:
            lines.append("**Warnings:**")
            for w in student_result.warnings:
                lines.append(f"  ⚠️ {w}")

        sections.append("\n".join(lines))

    return "\n\n---\n\n".join(sections)


def _build_comparison_notes(comparison: ScenarioComparison) -> str:
    """Format comparison table for LLM."""
    lines: list[str] = []

    if comparison.best_scenario_label:
        lines.append(f"Best scenario: **{comparison.best_scenario_label}**")

    for row in comparison.comparison_table:
        lines.append(
            f"- {row.label}: Safe={row.safe_count}, Likely={row.likely_count}, "
            f"Borderline={row.borderline_count} (Total viable: {row.total_options})"
        )

    for note in comparison.notes:
        lines.append(f"- {note}")

    return "\n".join(lines) if lines else "Single scenario — no comparison needed."


def _extract_colleges_from_response(text: str, comparison: ScenarioComparison) -> list[str]:
    """Extract mentioned college names that exist in the shortlists."""
    all_colleges: set[str] = set()
    for sr in comparison.results:
        if sr.error or sr.student_result is None:
            continue
        student_result: StudentResult = sr.student_result  # type: ignore[assignment]
        for entry in student_result.shortlist:
            all_colleges.add(entry.college_name)

    # Find which real colleges appear in the LLM response
    mentioned: list[str] = []
    for college in all_colleges:
        if college in text or college[:25] in text:
            mentioned.append(college)

    return mentioned[:10]  # Cap at 10


def _extract_section(text: str, header: str) -> str:
    """Extract content under a markdown ### header."""
    pattern = rf"###\s*{re.escape(header)}\s*\n(.*?)(?=\n###|\Z)"
    match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
    return match.group(1).strip() if match else ""


def generate_narrative(
    intent: StudentIntent,
    comparison: ScenarioComparison,
    client: LLMClient,
) -> CounsellingNarrative:
    """Generate counselling narrative via LLM.

    Args:
        intent: Student's parsed intent
        comparison: Cross-scenario comparison
        client: LLM client

    Returns:
        CounsellingNarrative (may contain issues — validator will check)
    """
    # Build prompts
    knowledge_context = build_knowledge_context(intent, comparison)
    system_prompt = format_reasoner_system_prompt(knowledge_context)
    user_prompt = format_reasoner_user_prompt(
        profile_summary=_build_profile_summary(intent),
        scenario_data=_build_scenario_data(comparison),
        comparison_notes=_build_comparison_notes(comparison),
    )

    # Call LLM
    response: LLMResponse = client.chat(
        system=system_prompt,
        user=user_prompt,
        model=client.narrative_model,
        temperature=0.3,
        max_tokens=2048,
    )

    text = response.content

    # Parse structured sections from response
    summary = _extract_section(text, "Summary") or text[:200]
    primary_path = _extract_section(text, "Top Recommendations") or ""
    backup_path = _extract_section(text, "Backup Options") or None
    risk_areas_text = _extract_section(text, "Risk Areas")
    risk_areas = [l.strip("- ").strip() for l in risk_areas_text.split("\n") if l.strip()] if risk_areas_text else []
    notes_text = _extract_section(text, "Important Notes")
    caveats = [l.strip("- ").strip() for l in notes_text.split("\n") if l.strip()] if notes_text else []

    # Extract real college names mentioned
    top_colleges = _extract_colleges_from_response(text, comparison)

    return CounsellingNarrative(
        summary=summary,
        primary_path=primary_path,
        backup_path=backup_path,
        top_colleges=top_colleges,
        risk_areas=risk_areas,
        missing_data_caveats=caveats,
        full_narrative=text,
        model_used=response.model,
        raw_llm_response=response.content,
        tokens_used=response.tokens_used,
    )
