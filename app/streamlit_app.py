"""NEET UG College Predictor — Streamlit UI.

Two input modes:
1. Form mode: Marks → Rank scenarios + College predictions (fast, no LLM)
2. Chat mode: Natural language → AI counsellor pipeline

Run:
    streamlit run app/streamlit_app.py
"""

from __future__ import annotations

import sys
from pathlib import Path

# Add src to Python path
_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / "src"))

import streamlit as st
import pandas as pd

from neet_predictor.config import VALIDATION_YEAR, TRAINING_YEARS
from neet_predictor.rank.estimator import RankEstimator, RankEstimate
from neet_predictor.rank.calibration import NormalizationMode
from neet_predictor.integrated.pipeline import UnifiedInput, run_prediction, UnifiedResult
from neet_predictor.integrated.summary import build_student_result, StudentResult, CHANCE_ORDER
from neet_predictor.integrated.reasoning import generate_reasoning, ReasoningOutput

# ── Constants ──
ALL_YEARS = sorted(TRAINING_YEARS + [VALIDATION_YEAR])

# Paper difficulty classification based on highest marks and competition
_PAPER_DIFFICULTY = {
    2020: ("Moderate", "🟡"),   # highest=720, cutoff=147, appeared=1.37M
    2021: ("Moderate", "🟡"),   # highest=720, cutoff=138, appeared=1.54M
    2022: ("Moderate", "🟡"),   # highest=715, cutoff=117, appeared=1.76M
    2023: ("Easy", "🟢"),       # highest=720, cutoff=137, appeared=2.04M, high scoring
    2024: ("Easy", "🟢"),       # highest=720, cutoff=164, 61 toppers, appeared=2.33M
    2025: ("Tough", "🔴"),      # highest=686(!), cutoff=144, appeared=2.21M
}


# ── Page Config ──
st.set_page_config(
    page_title="NEET UG College Predictor",
    page_icon="🏥",
    layout="wide",
)

# ── Session State ──
if "results" not in st.session_state:
    st.session_state.results = None


# ═══════════════════════════════════════════════════════════════════════════════
# SIDEBAR
# ═══════════════════════════════════════════════════════════════════════════════

with st.sidebar:
    st.title("⚙️ Settings")
    input_mode = st.radio("Input Mode", ["📝 Form", "💬 Chat (AI)"], index=0)
    st.divider()
    st.caption("**Data: 2020-2025**")
    st.caption("45,139 closing ranks • 530 KEA calibration points")
    st.caption("MCC All India + KEA Karnataka")
    st.divider()
    st.caption("⚠️ Not an admission guarantee.")


# ═══════════════════════════════════════════════════════════════════════════════
# HEADER
# ═══════════════════════════════════════════════════════════════════════════════

st.title("🏥 NEET UG College Predictor")
st.caption("Verified data from 6 years of NEET (2020–2025) • Actual ranks, not formulas")


# ═══════════════════════════════════════════════════════════════════════════════
# CORE PREDICTION ENGINE
# ═══════════════════════════════════════════════════════════════════════════════

@st.cache_resource
def get_estimator() -> RankEstimator:
    """Cached rank estimator (loads data once)."""
    return RankEstimator(use_validation_data=True)


def get_year_over_year(marks: int) -> list[dict]:
    """Get rank for given marks across ALL years — our transparency advantage."""
    est = get_estimator()
    results = []
    for year in ALL_YEARS:
        # Skip years where marks exceed the highest recorded score
        highest = est._highest.get(year, 720)
        if marks > highest:
            continue
        r = est.estimate(marks, target_year=year, category="General")
        if r:
            diff, icon = _PAPER_DIFFICULTY.get(year, ("Unknown", "⚪"))
            results.append({
                "year": year,
                "air": r.median_air,
                "best": r.best_case_air,
                "conservative": r.conservative_air,
                "confidence": r.confidence,
                "difficulty": diff,
                "icon": icon,
                "highest": highest,
            })
    return results


def get_paper_scenarios(marks: int) -> dict:
    """Group year results into Tough/Moderate/Easy paper scenarios."""
    yoy = get_year_over_year(marks)
    if not yoy:
        return {}

    # Classify by paper difficulty
    tough = [r for r in yoy if r["difficulty"] == "Tough"]
    moderate = [r for r in yoy if r["difficulty"] == "Moderate"]
    easy = [r for r in yoy if r["difficulty"] == "Easy"]

    scenarios = {}
    if tough:
        best = min(tough, key=lambda x: x["air"])
        scenarios["tough"] = {"air": best["air"], "year": best["year"], "label": "TOUGH PAPER", "icon": "🔴"}

    return scenarios


def run_form_prediction(marks, actual_air, target_year, national_category,
                        home_state, karnataka_interest, karnataka_domicile,
                        karnataka_category, course_pref, college_type_pref):
    """Run prediction from structured form input."""
    try:
        inp = UnifiedInput(
            marks=marks if marks else None,
            actual_air=actual_air if actual_air else None,
            national_category=national_category,
            home_state=home_state,
            karnataka_interest=karnataka_interest,
            karnataka_domicile=karnataka_domicile,
            karnataka_category=karnataka_category if karnataka_category != "None" else None,
            course_pref=course_pref,
            college_type_pref=college_type_pref.lower(),
            target_year=target_year,
        )
        unified_result = run_prediction(inp)
        student_result = build_student_result(unified_result)
        return unified_result, student_result, None
    except Exception as e:
        return None, None, str(e)


# ═══════════════════════════════════════════════════════════════════════════════
# DISPLAY: RANK SCENARIOS (Competitive with Formity — but HONEST)
# ═══════════════════════════════════════════════════════════════════════════════

def display_rank_scenarios(marks: int, target_year: int, unified_result: UnifiedResult):
    """Display rank in clean range format with paper scenarios as context."""
    rank_est = unified_result.rank_estimate
    est = get_estimator()
    highest = est._highest.get(target_year, 720)

    # Warn if marks exceed highest possible for that year
    if marks > highest:
        st.warning(f"⚠️ {marks} marks exceeds the highest score in {target_year} ({highest}). "
                   f"This score was not possible in that year's exam.")

    if not rank_est:
        st.info(f"Using actual AIR: **{unified_result.rank_used.air:,}**")
        return

    diff_label, diff_icon = _PAPER_DIFFICULTY.get(target_year, ("Unknown", "⚪"))

    # ── Primary: Clean range display (like Formity) ──
    st.markdown(f"### Rank for {marks} marks in {target_year}")

    col1, col2 = st.columns([2, 1])
    with col1:
        st.markdown(f"## #{rank_est.median_air:,}")
        st.caption(f"Range: #{rank_est.best_case_air:,} – #{rank_est.conservative_air:,}")
    with col2:
        conf_colors = {"high": "🟢 HIGH", "medium": "🟡 MEDIUM", "low": "🔴 LOW"}
        st.markdown(f"**{conf_colors.get(rank_est.confidence, rank_est.confidence)}**")
        st.caption(f"{diff_icon} {diff_label} paper • Actual data")

    # ── Paper difficulty scenarios (collapsed — context only) ──
    scenarios = get_paper_scenarios(marks)
    if scenarios and len(scenarios) >= 1:
        with st.expander("📊 Same marks, different paper difficulty", expanded=False):
            st.caption("How paper difficulty affects rank — from actual NEET data across years:")
            cols = st.columns(len(scenarios))
            for i, (key, sc) in enumerate(scenarios.items()):
                with cols[i]:
                    st.markdown(f"**{sc['icon']} {sc['label']}**")
                    st.markdown(f"#{sc['air']:,}")
                    st.caption(f"Like {sc['year']}")

            # Year-over-year table
            yoy = get_year_over_year(marks)
            if yoy:
                st.caption("")
                rows = []
                for r in sorted(yoy, key=lambda x: x["year"], reverse=True):
                    rows.append({
                        "Year": r["year"],
                        "AIR": f"#{r['air']:,}",
                        "Paper": f"{r['icon']} {r['difficulty']}",
                    })
                st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    # Category qualification
    _display_category_info(marks, target_year)


def _display_category_info(marks: int, target_year: int):
    """Show category cutoff qualification status."""
    try:
        ey = pd.read_csv(_ROOT / "neet-predictor" / "data" / "curated" / "exam_years.csv")
        row = ey[ey["year"] == target_year]
        if row.empty:
            return

        row = row.iloc[0]
        cutoffs = {
            "General": int(row["cutoff_ur"]),
            "OBC": int(row["cutoff_obc"]),
            "SC": int(row["cutoff_sc"]),
            "ST": int(row["cutoff_st"]),
            "EWS": int(row["cutoff_ews"]),
        }

        with st.expander("📋 Category Cutoffs & Qualification", expanded=False):
            cols = st.columns(5)
            for i, (cat, cutoff) in enumerate(cutoffs.items()):
                qualifies = marks >= cutoff
                icon = "✅" if qualifies else "❌"
                cols[i].metric(f"{cat}", f"{icon} {cutoff}",
                               delta=f"+{marks - cutoff}" if qualifies else f"{marks - cutoff}",
                               delta_color="normal" if qualifies else "inverse")
            st.caption(f"Minimum qualifying marks for NEET {target_year}")
    except Exception:
        pass


# ═══════════════════════════════════════════════════════════════════════════════
# DISPLAY: COLLEGE PREDICTIONS
# ═══════════════════════════════════════════════════════════════════════════════


def _display_reasoning(reasoning: ReasoningOutput):
    """Display the AI reasoning analysis."""
    header = "### 🧠 AI Analysis"
    if "llm" in reasoning.source:
        header += " _(powered by LLM)_"
    if "hybrid" in reasoning.source:
        header += " _(web cross-checked)_"

    st.markdown(header)
    st.markdown(reasoning.full_text)

    # Show agreement badge
    if reasoning.hybrid_agreement:
        badge_map = {
            "strong": "🟢 Web sources agree with our prediction",
            "moderate": "🟡 Moderate agreement with web sources",
            "divergent": "🔴 Our data diverges from web — verified dataset used as primary",
            "future_year_blend": "🔮 Future year — blended estimate (web + historical data)",
            "dataset_only": "📊 Dataset only (web unavailable)",
        }
        badge = badge_map.get(reasoning.hybrid_agreement, "")
        if badge:
            st.caption(badge)

    # Show college cross-check badge
    if reasoning.college_hybrid_agreement:
        college_badge_map = {
            "strong": "🏥🟢 College list confirmed by web sources",
            "moderate": "🏥🟡 Partial overlap — web suggests additional colleges",
            "divergent": "🏥🔴 Limited overlap — web mentions colleges outside our dataset",
            "dataset_only": "🏥📊 College list from dataset only",
            "web_only": "🏥🌐 College list from web only",
        }
        college_badge = college_badge_map.get(reasoning.college_hybrid_agreement, "")
        if college_badge:
            st.caption(college_badge)


def _get_chance_count(summary, label: str) -> int:
    """Get count for a chance label from AuthoritySummary."""
    for bucket in summary.by_chance:
        if bucket.label == label:
            return bucket.count
    return 0


def display_college_section(student_result: StudentResult):
    """Display college predictions — clean sortable tables."""
    st.markdown("### 🏫 College Predictions")

    # Quick summary
    mcc = student_result.mcc_summary
    kea = student_result.kea_summary
    total_safe = _get_chance_count(mcc, "Safe") + _get_chance_count(kea, "Safe")
    total_likely = _get_chance_count(mcc, "Likely") + _get_chance_count(kea, "Likely")
    total_borderline = _get_chance_count(mcc, "Borderline") + _get_chance_count(kea, "Borderline")

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("✅ Safe", total_safe)
    col2.metric("🟡 Likely", total_likely)
    col3.metric("🟠 Borderline", total_borderline)
    col4.metric("📍 AIR Used", f"#{student_result.rank_used.air:,}")

    # Tabs
    tab_all, tab_mcc, tab_kea, tab_r2 = st.tabs(
        ["All Colleges", "MCC All India", "KEA Karnataka", "🔄 R2 Opportunities"]
    )

    with tab_all:
        _display_college_table(student_result, authority=None)
    with tab_mcc:
        _display_college_table(student_result, authority="MCC")
    with tab_kea:
        _display_college_table(student_result, authority="KEA")
    with tab_r2:
        _display_r2_opportunities(student_result)


def _display_college_table(student_result: StudentResult, authority: str | None):
    """Render a filterable college table."""
    if authority:
        entries = [e for e in student_result.shortlist if e.authority == authority]
    else:
        entries = student_result.shortlist

    if not entries:
        st.info("No predictions available for this selection.")
        return

    # Compact filters
    col1, col2, col3 = st.columns(3)
    with col1:
        chance_filter = st.multiselect(
            "Chance", ["Safe", "Likely", "Borderline", "Unlikely"],
            default=["Safe", "Likely", "Borderline"],
            key=f"chance_{authority or 'all'}",
        )
    with col2:
        type_filter = st.selectbox(
            "Type", ["All", "Government", "Deemed/Private"],
            key=f"type_{authority or 'all'}",
        )
    with col3:
        state_filter = st.text_input("State", "", key=f"state_{authority or 'all'}",
                                     placeholder="Filter by state...")

    # Apply filters
    filtered = [e for e in entries if e.chance in chance_filter]
    if type_filter == "Government":
        filtered = [e for e in filtered if "Deemed" not in (e.quota or "") and "Paid" not in (e.quota or "")]
    elif type_filter == "Deemed/Private":
        filtered = [e for e in filtered if "Deemed" in (e.quota or "") or "Paid" in (e.quota or "")]
    if state_filter:
        filtered = [e for e in filtered if state_filter.lower() in e.state.lower()]

    if not filtered:
        st.warning("No colleges match filters.")
        return

    # Build table
    rows = []
    for e in filtered:
        r1_latest = max(e.r1_closing_ranks.items(), key=lambda x: x[0]) if e.r1_closing_ranks else (None, None)
        rows.append({
            "College": e.college_name.split(",")[0][:45],
            "State": e.state,
            "Chance": e.chance,
            "Margin": f"{e.weighted_margin:+.0%}" if e.weighted_margin else "—",
            "R1 Closing": f"{r1_latest[1]:,} ({r1_latest[0]})" if r1_latest[0] else "—",
            "Category": e.category,
            "Authority": e.authority,
        })

    df = pd.DataFrame(rows)
    st.dataframe(df, use_container_width=True, hide_index=True)
    st.caption(f"{len(filtered)} of {len(entries)} colleges shown")


def _display_r2_opportunities(student_result: StudentResult):
    """Show colleges achievable in R2 but unlikely in R1."""
    air_used = student_result.rank_used.air
    opportunities = []

    for entry in student_result.shortlist:
        if entry.chance not in ("Unlikely", "Borderline"):
            continue
        r2_data = entry.supplementary_rounds.get("R2", {})
        if not r2_data:
            continue
        achievable_years = [(yr, rank) for yr, rank in r2_data.items() if rank >= air_used]
        if achievable_years:
            r1_latest = max(entry.r1_closing_ranks.items(), key=lambda x: x[0]) if entry.r1_closing_ranks else (None, None)
            opportunities.append({
                "College": entry.college_name.split(",")[0][:45],
                "State": entry.state,
                "R1 Chance": entry.chance,
                "R1 Closing": f"{r1_latest[1]:,}" if r1_latest[1] else "—",
                "R2 History": ", ".join(f"{yr}:#{r:,}" for yr, r in sorted(achievable_years)),
                "Authority": entry.authority,
            })

    if not opportunities:
        st.info("No R2 opportunities. All viable colleges are in R1.")
        return

    st.markdown("**Unlikely/Borderline in R1, but historically achievable in R2:**")
    df = pd.DataFrame(opportunities)
    st.dataframe(df, use_container_width=True, hide_index=True)
    st.caption(f"{len(opportunities)} colleges become achievable in supplementary rounds")


# ═══════════════════════════════════════════════════════════════════════════════
# CHAT MODE (with LLM fallback)
# ═══════════════════════════════════════════════════════════════════════════════

def _parse_query_fallback(query: str) -> dict:
    """Simple regex-based intent extraction when LLM is unavailable."""
    import re

    result = {
        "marks": None, "actual_air": None, "target_year": None,
        "national_category": "General", "home_state": None,
        "karnataka_interest": False, "karnataka_domicile": False,
        "karnataka_category": None, "course_pref": "MBBS",
        "college_type_pref": "any",
    }

    # Extract marks
    marks_match = re.search(r'(\d{2,3})\s*(?:marks?|score)', query, re.IGNORECASE)
    if not marks_match:
        marks_match = re.search(r'(?:scored?|got|have|get)\s*(\d{2,3})', query, re.IGNORECASE)
    if not marks_match:
        marks_match = re.search(r'\b(\d{3})\b', query)
    if marks_match:
        m = int(marks_match.group(1))
        if 100 <= m <= 720:
            result["marks"] = m

    # Extract AIR
    air_match = re.search(r'(?:AIR|rank|air)\s*(?:is\s*)?(\d{1,7})', query, re.IGNORECASE)
    if air_match:
        result["actual_air"] = int(air_match.group(1))

    # Extract year
    year_match = re.search(r'(20[2][0-6])', query)
    if year_match:
        result["target_year"] = int(year_match.group(1))

    # Category
    cat_map = {r'\bOBC\b': "OBC", r'\bSC\b': "SC", r'\bST\b': "ST", r'\bEWS\b': "EWS"}
    for pattern, cat in cat_map.items():
        if re.search(pattern, query):
            result["national_category"] = cat
            break

    # State / Karnataka
    if "karnataka" in query.lower():
        result["home_state"] = "Karnataka"
        result["karnataka_interest"] = True
        result["karnataka_domicile"] = True
        result["karnataka_category"] = "GM"

    # College type
    if re.search(r'\bgov(?:ernment|t)\b', query, re.IGNORECASE):
        result["college_type_pref"] = "government"

    return result


def run_chat_prediction(query: str):
    """Run prediction — LLM first, regex fallback."""
    try:
        from neet_predictor.counsellor import (
            LLMClient, run_counsellor, ClarificationNeeded, ValidatedResponse,
        )
        client = LLMClient()
        result = run_counsellor(query, client=client)
        return result, None, "llm"
    except Exception:
        pass

    # Fallback: regex → form engine
    try:
        parsed = _parse_query_fallback(query)
        if not parsed["marks"] and not parsed["actual_air"]:
            return None, "Could not extract marks or rank. Try: 'I scored 550 in 2025'", "error"

        unified_result, student_result, error = run_form_prediction(
            marks=parsed["marks"],
            actual_air=parsed["actual_air"],
            target_year=parsed["target_year"] or 2026,
            national_category=parsed["national_category"],
            home_state=parsed["home_state"] or "Karnataka",
            karnataka_interest=parsed["karnataka_interest"],
            karnataka_domicile=parsed["karnataka_domicile"],
            karnataka_category=parsed["karnataka_category"] or "None",
            course_pref=parsed["course_pref"],
            college_type_pref=parsed["college_type_pref"].capitalize(),
        )
        if error:
            return None, error, "error"
        return (unified_result, student_result, parsed), None, "fallback"
    except Exception as e:
        return None, f"Error: {e}", "error"


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN UI — FORM MODE
# ═══════════════════════════════════════════════════════════════════════════════

if input_mode == "📝 Form":
    st.markdown("---")

    # Compact input — primary fields
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        marks = st.number_input("NEET Marks", min_value=0, max_value=720,
                                value=550, step=1)
    with col2:
        target_year = st.selectbox("Year", [2026, 2025, 2024, 2023, 2022, 2021, 2020], index=0)
    with col3:
        actual_air = st.number_input("AIR (0 = predict)", min_value=0, value=0, step=1)

    # Secondary fields in expander
    with st.expander("⚙️ Category & State Preferences", expanded=False):
        col4, col5, col6 = st.columns(3)
        with col4:
            national_category = st.selectbox("Category", ["General", "OBC", "SC", "ST", "EWS"])
        with col5:
            home_state = st.text_input("Home State", "Karnataka")
        with col6:
            course_pref = st.selectbox("Course", ["MBBS", "BDS", "MBBS+BDS"])

        col7, col8, col9 = st.columns(3)
        with col7:
            karnataka_interest = st.checkbox("Karnataka interest", value=True)
        with col8:
            karnataka_domicile = st.checkbox("Karnataka domicile", value=True)
        with col9:
            karnataka_category = st.selectbox("KEA Category",
                                              ["None", "GM", "1", "2A", "2B", "3A", "3B", "SC", "ST"], index=1)

        college_type_pref = st.selectbox("College Type", ["Any", "Government", "Deemed"])

    # Predict button
    if st.button("🔍 Predict My Rank & Colleges", type="primary", use_container_width=True):
        with st.spinner("Crunching 6 years of NEET data..."):
            unified_result, student_result, error = run_form_prediction(
                marks=marks if marks > 0 else None,
                actual_air=actual_air if actual_air > 0 else None,
                target_year=target_year,
                national_category=national_category,
                home_state=home_state,
                karnataka_interest=karnataka_interest,
                karnataka_domicile=karnataka_domicile,
                karnataka_category=karnataka_category,
                course_pref=course_pref,
                college_type_pref=college_type_pref,
            )

        if error:
            st.error(f"❌ {error}")
        else:
            st.session_state.results = (unified_result, student_result, marks, target_year)

    # Display results
    if st.session_state.results:
        unified_result, student_result, res_marks, res_year = st.session_state.results
        st.markdown("---")

        # Section 1: Rank Scenarios
        if res_marks:
            display_rank_scenarios(res_marks, res_year, unified_result)
        else:
            st.markdown(f"### Using actual AIR: #{unified_result.rank_used.air:,}")

        st.markdown("---")

        # Section 2: AI Analysis (LLM reasoning layer)
        if res_marks:
            reasoning = generate_reasoning(res_marks, res_year, unified_result, student_result)
            _display_reasoning(reasoning)
            st.markdown("---")

        # Section 3: College Predictions
        display_college_section(student_result)

        # Warnings
        if unified_result.warnings:
            with st.expander("⚠️ Methodology Notes"):
                for w in unified_result.warnings:
                    st.caption(f"• {w}")


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN UI — CHAT MODE
# ═══════════════════════════════════════════════════════════════════════════════

elif input_mode == "💬 Chat (AI)":
    st.markdown("---")
    st.markdown("**Ask in natural language** — AI parses your query and runs predictions.")
    st.caption("_'I scored 627 in 2022, General from Karnataka'_ • _'450 marks 2026 what rank?'_")

    query = st.text_area("Your question:", height=80,
                         placeholder="e.g. 605 marks in 2025, OBC category, Karnataka")

    if st.button("🔍 Predict", type="primary", use_container_width=True):
        if not query.strip():
            st.warning("Please enter a question.")
        else:
            with st.spinner("Analyzing..."):
                result, error, mode = run_chat_prediction(query)

            if error:
                st.error(f"❌ {error}")
            elif mode == "fallback":
                unified_result, student_result, parsed = result
                st.info("💡 Using direct prediction engine (AI unavailable).")

                # Show extracted params
                tags = []
                if parsed["marks"]:
                    tags.append(f"**{parsed['marks']}** marks")
                if parsed["target_year"]:
                    tags.append(f"year **{parsed['target_year']}**")
                if parsed["national_category"] != "General":
                    tags.append(f"**{parsed['national_category']}**")
                if tags:
                    st.caption(f"Extracted: {' • '.join(tags)}")

                st.markdown("---")
                if parsed["marks"]:
                    display_rank_scenarios(parsed["marks"], parsed["target_year"] or VALIDATION_YEAR, unified_result)
                    st.markdown("---")
                    # AI reasoning
                    reasoning = generate_reasoning(
                        parsed["marks"], parsed["target_year"] or VALIDATION_YEAR,
                        unified_result, student_result
                    )
                    _display_reasoning(reasoning)
                    st.markdown("---")
                display_college_section(student_result)

            elif mode == "llm":
                # Full AI counsellor response
                from neet_predictor.counsellor import ClarificationNeeded, ValidatedResponse

                if isinstance(result, ClarificationNeeded):
                    st.warning("Need more info:")
                    for q in result.questions:
                        st.markdown(f"- {q}")
                elif isinstance(result, ValidatedResponse):
                    if result.narrative and not result.fallback_used:
                        st.markdown(result.narrative.full_narrative)
                    if result.scenarios and result.scenarios.comparison_table:
                        rows = []
                        for row in result.scenarios.comparison_table:
                            rows.append({
                                "Scenario": row.label,
                                "Safe": row.safe_count,
                                "Likely": row.likely_count,
                                "Borderline": row.borderline_count,
                                "Best College": (row.best_college or "—")[:40],
                            })
                        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
                    st.caption(f"⏱️ {result.processing_time_ms}ms")


# ═══════════════════════════════════════════════════════════════════════════════
# FOOTER
# ═══════════════════════════════════════════════════════════════════════════════

st.markdown("---")
st.caption("⚠️ Predictions from verified historical data (2020–2025). Not an admission guarantee. "
           "Verify from MCC/KEA official sources.")
