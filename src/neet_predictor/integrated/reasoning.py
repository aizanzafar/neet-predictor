"""LLM Reasoning Layer — intelligent interpretation of prediction results.

Takes structured prediction output (rank estimate, college shortlist) and generates
a natural language analysis that helps students understand their realistic options.

Falls back to rule-based reasoning when LLM API is unavailable.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

from neet_predictor.integrated.pipeline import UnifiedResult
from neet_predictor.integrated.summary import StudentResult

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════════
# SYSTEM PROMPT — the core intelligence
# ═══════════════════════════════════════════════════════════════════════════════

REASONING_SYSTEM_PROMPT = """\
You are an expert NEET UG medical admissions counsellor for India. You analyze prediction data \
and give students a REALISTIC, honest assessment of their college options.

RULES:
1. Be DIRECT. No filler, no motivational quotes. Students want facts.
2. Use the ACTUAL data provided — do not hallucinate colleges or ranks.
3. Always mention the rank RANGE (best–conservative), not just one number.
4. For college predictions, focus on the TOP 5-8 REALISTIC options (Safe + Likely).
5. Mention the R1 closing rank when discussing colleges.
6. If a student has many Safe colleges, highlight the BEST ones (lowest closing rank = most prestigious).
7. Paper difficulty context: explain WHY the same marks give different ranks across years.
8. Category advantage: if student is OBC/SC/ST, mention their category cutoffs explicitly.
9. NEVER say "you will definitely get X" — always frame as "historically, students with rank ~X have secured..."
10. Keep response under 300 words. Use bullet points for college recommendations.

PAPER DIFFICULTY CONTEXT:
- 2025: TOUGH paper (highest=686). Same marks → much better rank than other years.
- 2024: EASY paper (61 toppers, highest=720). Same marks → worse rank.
- 2023: EASY paper. Similar to 2024.
- 2020-2022: MODERATE papers. Middle ground.

COLLEGE TIERS (approximate AIR ranges for General/UR category, MBBS, MCC AIQ):
- Tier 1 (AIR <1,000): AIIMS Delhi, MAMC, JIPMER, KGMU, BHU
- Tier 2 (AIR 1,000-5,000): Other AIIMS, top state GMCs, VMMC, UCMS
- Tier 3 (AIR 5,000-15,000): Mid-tier GMCs, good state medical colleges
- Tier 4 (AIR 15,000-50,000): District GMCs, newer state colleges
- Tier 5 (AIR 50,000-100,000): Private/Deemed considered, some state quota options
- Tier 6 (AIR >100,000): Limited options — private deemed, management quota

OUTPUT FORMAT:
Start with a one-line summary: "With [marks] marks in [year] ([difficulty] paper), your estimated rank is ~[median] (range: [best]–[conservative])."
Then give specific college recommendations with closing ranks.
End with ONE practical next step.
"""


def build_reasoning_user_prompt(
    marks: int,
    target_year: int,
    unified_result: UnifiedResult,
    student_result: StudentResult,
) -> str:
    """Build the user prompt with all structured data for LLM reasoning."""
    rank_est = unified_result.rank_estimate
    rank_used = unified_result.rank_used

    lines = []
    lines.append(f"STUDENT QUERY: {marks} marks in NEET {target_year}")
    lines.append(f"CATEGORY: {unified_result.input_echo.get('national_category', 'General')}")

    if rank_est:
        lines.append(f"\nRANK ESTIMATE:")
        lines.append(f"  Median AIR: {rank_est.median_air:,}")
        lines.append(f"  Best case: {rank_est.best_case_air:,}")
        lines.append(f"  Conservative: {rank_est.conservative_air:,}")
        lines.append(f"  Confidence: {rank_est.confidence}")
    else:
        lines.append(f"\nACTUAL AIR: {rank_used.air:,}")

    lines.append(f"\nAIR USED FOR COLLEGE MATCHING: {rank_used.air:,} ({rank_used.source})")

    # Top colleges by chance
    safe = [e for e in student_result.shortlist if e.chance == "Safe"]
    likely = [e for e in student_result.shortlist if e.chance == "Likely"]
    borderline = [e for e in student_result.shortlist if e.chance == "Borderline"]

    # Sort each by closing rank (ascending = most competitive first)
    def _sort_key(entry):
        if entry.r1_closing_ranks:
            return min(entry.r1_closing_ranks.values())
        return 999999

    safe.sort(key=_sort_key)
    likely.sort(key=_sort_key)
    borderline.sort(key=_sort_key)

    lines.append(f"\nCOLLEGE SHORTLIST SUMMARY:")
    lines.append(f"  Safe: {len(safe)} colleges")
    lines.append(f"  Likely: {len(likely)} colleges")
    lines.append(f"  Borderline: {len(borderline)} colleges")

    # Top 5 safe colleges
    if safe:
        lines.append(f"\nTOP SAFE COLLEGES (best first):")
        for e in safe[:5]:
            r1 = max(e.r1_closing_ranks.items(), key=lambda x: x[0]) if e.r1_closing_ranks else (None, None)
            closing = f"R1 closing: {r1[1]:,} ({r1[0]})" if r1[0] else "no closing data"
            lines.append(f"  - {e.college_name} [{e.state}] — {closing} ({e.authority})")

    # Top 5 likely colleges
    if likely:
        lines.append(f"\nTOP LIKELY COLLEGES:")
        for e in likely[:5]:
            r1 = max(e.r1_closing_ranks.items(), key=lambda x: x[0]) if e.r1_closing_ranks else (None, None)
            closing = f"R1 closing: {r1[1]:,} ({r1[0]})" if r1[0] else "no closing data"
            lines.append(f"  - {e.college_name} [{e.state}] — {closing} ({e.authority})")

    # Top 3 borderline (stretch goals)
    if borderline:
        lines.append(f"\nTOP BORDERLINE (stretch goals):")
        for e in borderline[:3]:
            r1 = max(e.r1_closing_ranks.items(), key=lambda x: x[0]) if e.r1_closing_ranks else (None, None)
            closing = f"R1 closing: {r1[1]:,} ({r1[0]})" if r1[0] else "no closing data"
            lines.append(f"  - {e.college_name} [{e.state}] — {closing} ({e.authority})")

    lines.append(f"\nPlease provide your analysis and top recommendations.")
    return "\n".join(lines)


# ═══════════════════════════════════════════════════════════════════════════════
# RULE-BASED FALLBACK (when LLM unavailable)
# ═══════════════════════════════════════════════════════════════════════════════

_PAPER_DIFFICULTY = {
    2020: ("Moderate", "🟡"),
    2021: ("Moderate", "🟡"),
    2022: ("Moderate", "🟡"),
    2023: ("Easy", "🟢"),
    2024: ("Easy", "🟢"),
    2025: ("Tough", "🔴"),
}


@dataclass
class ReasoningOutput:
    """Result of the reasoning layer."""
    summary_line: str
    college_recommendations: str
    next_step: str
    full_text: str
    source: str  # "llm", "rule_based", or "hybrid"
    web_cross_check: str = ""  # web search comparison info
    hybrid_agreement: str = ""  # "strong", "moderate", "divergent"
    college_web_cross_check: str = ""  # college web comparison info
    college_hybrid_agreement: str = ""  # college agreement level


def generate_reasoning(
    marks: int,
    target_year: int,
    unified_result: UnifiedResult,
    student_result: StudentResult,
    use_web_search: bool = True,
) -> ReasoningOutput:
    """Generate intelligent reasoning — tries LLM, falls back to rules.

    When use_web_search=True (default), also runs web search cross-check
    and includes the comparison in the output.

    Returns a structured ReasoningOutput with summary, recommendations, and advice.
    """
    # Try LLM first
    try:
        result = _reasoning_via_llm(marks, target_year, unified_result, student_result)
    except Exception as e:
        logger.debug(f"LLM reasoning unavailable ({e}), using rule-based fallback")
        result = _reasoning_rule_based(marks, target_year, unified_result, student_result)

    # Augment with web search cross-check
    if use_web_search:
        result = _augment_with_web_search(result, marks, target_year, unified_result)

    return result


def _augment_with_web_search(
    result: ReasoningOutput,
    marks: int,
    target_year: int,
    unified_result: UnifiedResult,
) -> ReasoningOutput:
    """Cross-check prediction with web search and add context."""
    try:
        from neet_predictor.integrated.hybrid_agent import (
            run_hybrid_prediction,
            run_hybrid_college_prediction,
        )

        category = unified_result.input.national_category or "General"
        hybrid = run_hybrid_prediction(marks, target_year, category)

        # Add web cross-check info
        web_info_lines = []
        if hybrid.web_estimate and hybrid.web_estimate.results:
            web_mid = hybrid.web_estimate.consensus_rank_mid
            ds_mid = unified_result.rank_used.air

            if web_mid:
                web_info_lines.append(
                    f"\n\n---\n**🌐 Web Cross-Check:** "
                    f"External sources estimate AIR ~{web_mid:,} "
                    f"(our data: {ds_mid:,}). "
                )
                if hybrid.agreement == "strong":
                    web_info_lines.append("✅ Strong agreement — prediction is well-corroborated.")
                elif hybrid.agreement == "moderate":
                    web_info_lines.append(
                        f"🟡 Moderate agreement ({hybrid.divergence_pct:.0f}% divergence). "
                        f"Range widened to {hybrid.final_rank_min:,}–{hybrid.final_rank_max:,}."
                    )
                elif hybrid.agreement == "future_year_blend":
                    web_info_lines.append(
                        f"🔮 Future year — paper difficulty unknown. "
                        f"Blended estimate: AIR ~{hybrid.final_rank_mid:,} "
                        f"(range: {hybrid.final_rank_min:,}–{hybrid.final_rank_max:,}). "
                        f"If tough paper → rank improves; if easy → rank drops."
                    )
                elif hybrid.agreement == "divergent":
                    web_info_lines.append(
                        f"⚠️ Sources diverge ({hybrid.divergence_pct:.0f}%). "
                        f"Our verified data is primary. Web range: "
                        f"{hybrid.web_estimate.consensus_rank_min:,}–"
                        f"{hybrid.web_estimate.consensus_rank_max:,}."
                    )

        # Add counselling context and tie-breaking notes
        context_lines = []
        if hybrid.percentile_context:
            context_lines.append(f"\n\n**📊 Context:** {hybrid.percentile_context}")
        if hybrid.counselling_context:
            context_lines.append(f"\n**🎓 Counselling:** {hybrid.counselling_context}")
        if hybrid.tie_breaking_notes:
            context_lines.append(f"\n**⚖️ Tie-breaking:** {hybrid.tie_breaking_notes}")

        web_check_text = "".join(web_info_lines)
        context_text = "".join(context_lines)

        # Update result with hybrid info
        result.full_text += web_check_text + context_text
        result.web_cross_check = web_check_text
        result.hybrid_agreement = hybrid.agreement
        result.source = f"{result.source}+hybrid"

        # ── College web cross-check ──
        air = unified_result.rank_used.air
        state = getattr(unified_result.input, "home_state", None)
        # PredictionResult has mcc_predictions + kea_predictions
        pred_result = unified_result.college_predictions
        dataset_preds = []
        if pred_result:
            dataset_preds = (
                getattr(pred_result, "mcc_predictions", [])
                + getattr(pred_result, "kea_predictions", [])
            )

        college_hybrid = run_hybrid_college_prediction(
            air=air,
            year=target_year,
            category=category,
            state=state,
            dataset_predictions=dataset_preds,
        )

        college_web_lines = []
        if college_hybrid.comparisons:
            college_web_lines.append(
                f"\n\n---\n**🏥 College Web Cross-Check:** "
            )
            confirmed = [c for c in college_hybrid.comparisons if c.merged_verdict == "Confirmed"]
            web_only = [c for c in college_hybrid.comparisons if c.merged_verdict == "Web-only suggestion"]

            if confirmed:
                names = [c.college_name for c in confirmed[:5]]
                college_web_lines.append(
                    f"✅ Confirmed by both sources: {', '.join(names)}"
                )
                if len(confirmed) > 5:
                    college_web_lines.append(f" (+{len(confirmed)-5} more)")

            if web_only:
                names = [c.college_name for c in web_only[:5]]
                college_web_lines.append(
                    f"\n🌐 Web also suggests: {', '.join(names)}. "
                    f"_Not in our verified dataset — confirm from official counselling data._"
                )

            if college_hybrid.agreement == "strong":
                college_web_lines.append("\n✅ Strong overlap between dataset and web college lists.")
            elif college_hybrid.agreement == "moderate":
                college_web_lines.append(
                    f"\n🟡 Partial overlap — {college_hybrid.confirmed_count} colleges confirmed."
                )
            elif college_hybrid.agreement == "divergent":
                college_web_lines.append(
                    "\n⚠️ Limited overlap — web mentions colleges outside our dataset."
                )

        college_web_text = "".join(college_web_lines)
        result.full_text += college_web_text
        result.college_web_cross_check = college_web_text
        result.college_hybrid_agreement = college_hybrid.agreement

    except Exception as e:
        logger.debug(f"Web search augmentation failed: {e}")

    return result


def _reasoning_via_llm(
    marks: int,
    target_year: int,
    unified_result: UnifiedResult,
    student_result: StudentResult,
) -> ReasoningOutput:
    """Call LLM API for reasoning."""
    from neet_predictor.counsellor.llm_client import LLMClient, LLMClientError

    client = LLMClient(timeout=15.0, max_retries=1)
    user_prompt = build_reasoning_user_prompt(marks, target_year, unified_result, student_result)

    response = client.chat(
        system=REASONING_SYSTEM_PROMPT,
        user=user_prompt,
        temperature=0.2,
        max_tokens=1024,
    )

    text = response.content.strip()
    # Split into sections (best effort)
    lines = text.split("\n")
    summary_line = lines[0] if lines else ""
    rest = "\n".join(lines[1:]) if len(lines) > 1 else ""

    return ReasoningOutput(
        summary_line=summary_line,
        college_recommendations=rest,
        next_step="",
        full_text=text,
        source="llm",
    )


def _reasoning_rule_based(
    marks: int,
    target_year: int,
    unified_result: UnifiedResult,
    student_result: StudentResult,
) -> ReasoningOutput:
    """Generate structured reasoning without LLM — pure data interpretation."""
    rank_est = unified_result.rank_estimate
    rank_used = unified_result.rank_used
    diff_label, diff_icon = _PAPER_DIFFICULTY.get(target_year, ("Unknown", "⚪"))

    # Summary line
    if rank_est:
        summary = (
            f"With **{marks} marks** in NEET {target_year} ({diff_icon} {diff_label} paper), "
            f"your estimated rank is **~{rank_est.median_air:,}** "
            f"(range: {rank_est.best_case_air:,} – {rank_est.conservative_air:,})."
        )
    else:
        summary = f"With AIR **{rank_used.air:,}** in NEET {target_year}, here's your analysis."

    # Determine tier
    air = rank_used.air
    if air < 1000:
        tier = "Tier 1 — top institutes (AIIMS Delhi, MAMC, JIPMER level)"
    elif air < 5000:
        tier = "Tier 2 — excellent GMCs and AIIMS branches"
    elif air < 15000:
        tier = "Tier 3 — mid-tier Government Medical Colleges"
    elif air < 50000:
        tier = "Tier 4 — state GMCs and newer government colleges"
    elif air < 100000:
        tier = "Tier 5 — private/deemed options worth considering alongside state quota"
    else:
        tier = "Tier 6 — limited government seats; private/deemed colleges realistic"

    # College recommendations
    safe = [e for e in student_result.shortlist if e.chance == "Safe"]
    likely = [e for e in student_result.shortlist if e.chance == "Likely"]
    borderline = [e for e in student_result.shortlist if e.chance == "Borderline"]

    def _sort_key(entry):
        if entry.r1_closing_ranks:
            return min(entry.r1_closing_ranks.values())
        return 999999

    safe.sort(key=_sort_key)
    likely.sort(key=_sort_key)
    borderline.sort(key=_sort_key)

    rec_lines = []
    rec_lines.append(f"**Your position:** {tier}")
    rec_lines.append("")

    if safe:
        rec_lines.append(f"**✅ Safe ({len(safe)} colleges)** — historically, your rank secures admission:")
        for e in safe[:5]:
            r1 = max(e.r1_closing_ranks.items(), key=lambda x: x[0]) if e.r1_closing_ranks else (None, None)
            closing_str = f"R1 closing: {r1[1]:,} ({r1[0]})" if r1[0] else ""
            rec_lines.append(f"- {e.college_name.split(',')[0][:50]} • {e.state} • {closing_str}")
        if len(safe) > 5:
            rec_lines.append(f"  _...and {len(safe) - 5} more safe options_")
        rec_lines.append("")

    if likely:
        rec_lines.append(f"**🟡 Likely ({len(likely)} colleges)** — good chance based on trends:")
        for e in likely[:4]:
            r1 = max(e.r1_closing_ranks.items(), key=lambda x: x[0]) if e.r1_closing_ranks else (None, None)
            closing_str = f"R1 closing: {r1[1]:,} ({r1[0]})" if r1[0] else ""
            rec_lines.append(f"- {e.college_name.split(',')[0][:50]} • {e.state} • {closing_str}")
        rec_lines.append("")

    if borderline:
        rec_lines.append(f"**🟠 Stretch goals ({len(borderline)} colleges)** — possible in later rounds:")
        for e in borderline[:3]:
            r1 = max(e.r1_closing_ranks.items(), key=lambda x: x[0]) if e.r1_closing_ranks else (None, None)
            closing_str = f"R1 closing: {r1[1]:,} ({r1[0]})" if r1[0] else ""
            rec_lines.append(f"- {e.college_name.split(',')[0][:50]} • {e.state} • {closing_str}")

    college_recommendations = "\n".join(rec_lines)

    # Next step
    if air < 15000:
        next_step = (
            "**Next step:** Focus on MCC AIQ Round 1 choice filling. "
            "Prioritize government colleges in states you prefer — all should be Safe/Likely for you."
        )
    elif air < 50000:
        next_step = (
            "**Next step:** Fill choices strategically in MCC counselling. "
            "List all Safe colleges first, then Likely ones. Also register for state counselling."
        )
    else:
        next_step = (
            "**Next step:** Register for BOTH MCC AIQ and state-level counselling. "
            "Consider private/deemed colleges as backup. Watch for R2/mop-up round upgrades."
        )

    full_text = f"{summary}\n\n{college_recommendations}\n\n{next_step}"

    return ReasoningOutput(
        summary_line=summary,
        college_recommendations=college_recommendations,
        next_step=next_step,
        full_text=full_text,
        source="rule_based",
    )
