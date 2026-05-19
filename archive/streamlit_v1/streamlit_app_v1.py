"""NEET UG College Predictor — Streamlit UI.

Two input modes:
1. Form mode: Direct structured input → fast (no LLM needed)
2. Chat mode: Natural language → LLM intent parser → full counsellor pipeline

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

# ── Page Config ──
st.set_page_config(
    page_title="NEET UG College Predictor",
    page_icon="🏥",
    layout="wide",
)

# ── Session State Init ──
if "results" not in st.session_state:
    st.session_state.results = None
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []


# ═══════════════════════════════════════════════════════════════════════════════
# SIDEBAR
# ═══════════════════════════════════════════════════════════════════════════════

with st.sidebar:
    st.title("⚙️ Settings")
    input_mode = st.radio("Input Mode", ["📝 Form", "💬 Chat (AI)"], index=0)
    st.divider()
    st.caption("**Data Coverage**")
    st.caption(f"Training years: {min(TRAINING_YEARS)}-{max(TRAINING_YEARS)}")
    st.caption(f"Validation year: {VALIDATION_YEAR}")
    st.caption("Sources: MCC + KEA (45,139 closing ranks)")
    st.divider()
    st.caption("⚠️ Not an admission guarantee. Verify from official sources.")


# ═══════════════════════════════════════════════════════════════════════════════
# HEADER
# ═══════════════════════════════════════════════════════════════════════════════

st.title("🏥 NEET UG College Predictor")
st.caption("Powered by historical data (2020-2025) • MCC All India Quota + KEA Karnataka")


# ═══════════════════════════════════════════════════════════════════════════════
# FORM MODE
# ═══════════════════════════════════════════════════════════════════════════════

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


def display_rank_section(unified_result: UnifiedResult):
    """Display rank estimation results."""
    st.subheader("📊 Rank Estimation")

    rank_est = unified_result.rank_estimate
    if rank_est is None:
        st.info(f"Using actual AIR: **{unified_result.rank_used.air:,}**")
        return

    # Confidence color
    conf_colors = {"high": "🟢", "medium": "🟡", "low": "🔴"}
    conf_icon = conf_colors.get(rank_est.confidence, "⚪")

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Best Case AIR", f"{rank_est.best_case_air:,}")
    with col2:
        st.metric("Median AIR", f"{rank_est.median_air:,}")
    with col3:
        st.metric("Conservative AIR", f"{rank_est.conservative_air:,}")
    with col4:
        st.metric("Confidence", f"{conf_icon} {rank_est.confidence.upper()}")

    # Method info
    method_desc = {
        "direct_interpolation": "Direct interpolation from same-year dense data",
        "weighted_percentile": "Weighted cross-year percentile interpolation",
    }
    st.caption(f"Method: {method_desc.get(rank_est.method, rank_est.method)}")
    st.caption(f"Rank used for college prediction: AIR **{unified_result.rank_used.air:,}** ({unified_result.rank_used.source})")


def _get_chance_count(summary, label: str) -> int:
    """Get count for a chance label from AuthoritySummary."""
    for bucket in summary.by_chance:
        if bucket.label == label:
            return bucket.count
    return 0


def display_college_section(student_result: StudentResult):
    """Display college predictions as filterable tables."""
    st.subheader("🏫 College Predictions")

    # Summary metrics
    mcc = student_result.mcc_summary
    kea = student_result.kea_summary

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**MCC All India Quota**")
        mcol1, mcol2, mcol3 = st.columns(3)
        mcol1.metric("Safe", _get_chance_count(mcc, "Safe"))
        mcol2.metric("Likely", _get_chance_count(mcc, "Likely"))
        mcol3.metric("Borderline", _get_chance_count(mcc, "Borderline"))

    with col2:
        st.markdown("**KEA Karnataka**")
        kcol1, kcol2, kcol3 = st.columns(3)
        kcol1.metric("Safe", _get_chance_count(kea, "Safe"))
        kcol2.metric("Likely", _get_chance_count(kea, "Likely"))
        kcol3.metric("Borderline", _get_chance_count(kea, "Borderline"))

    # Tabs for MCC and KEA
    tab_mcc, tab_kea, tab_r2 = st.tabs(["MCC All India", "KEA Karnataka", "🔄 R2 Opportunities"])

    with tab_mcc:
        _display_college_table(student_result, authority="MCC")

    with tab_kea:
        _display_college_table(student_result, authority="KEA")

    with tab_r2:
        _display_r2_opportunities(student_result)


def _display_college_table(student_result: StudentResult, authority: str):
    """Render a filterable college table for one authority."""
    entries = [e for e in student_result.shortlist if e.authority == authority]

    if not entries:
        st.info(f"No {authority} predictions available.")
        return

    # Filters
    col1, col2, col3 = st.columns(3)
    with col1:
        chance_filter = st.multiselect(
            "Chance", ["Safe", "Likely", "Borderline", "Unlikely"],
            default=["Safe", "Likely", "Borderline"],
            key=f"chance_{authority}",
        )
    with col2:
        type_filter = st.selectbox(
            "College Type", ["All", "Government", "Deemed/Private"],
            key=f"type_{authority}",
        )
    with col3:
        state_filter = st.text_input("State filter", "", key=f"state_{authority}")

    # Filter entries
    filtered = [e for e in entries if e.chance in chance_filter]
    if type_filter == "Government":
        filtered = [e for e in filtered if "Deemed" not in e.quota and "Paid" not in e.quota]
    elif type_filter == "Deemed/Private":
        filtered = [e for e in filtered if "Deemed" in e.quota or "Paid" in e.quota]
    if state_filter:
        filtered = [e for e in filtered if state_filter.lower() in e.state.lower()]

    if not filtered:
        st.warning("No colleges match the current filters.")
        return

    # Build dataframe
    rows = []
    for e in filtered:
        r1_latest = max(e.r1_closing_ranks.items(), key=lambda x: x[0]) if e.r1_closing_ranks else (None, None)
        rows.append({
            "College": e.college_name.split(",")[0][:50],
            "State": e.state,
            "Chance": e.chance,
            "Margin": f"{e.weighted_margin:+.0%}" if e.weighted_margin else "N/A",
            "Latest R1": f"{r1_latest[1]:,} ({r1_latest[0]})" if r1_latest[0] else "N/A",
            "Category": e.category,
            "Quota": e.quota[:30] if e.quota else "",
        })

    df = pd.DataFrame(rows)
    st.dataframe(df, use_container_width=True, hide_index=True)
    st.caption(f"Showing {len(filtered)} of {len(entries)} {authority} colleges")


def _display_r2_opportunities(student_result: StudentResult):
    """Show colleges that are Unlikely in R1 but achievable in R2."""
    air_used = student_result.rank_used.air
    opportunities = []

    for entry in student_result.shortlist:
        if entry.chance not in ("Unlikely", "Borderline"):
            continue
        r2_data = entry.supplementary_rounds.get("R2", {})
        if not r2_data:
            continue
        # Check if any R2 closing rank >= our AIR (achievable)
        achievable_years = [(yr, rank) for yr, rank in r2_data.items() if rank >= air_used]
        if achievable_years:
            r1_latest = max(entry.r1_closing_ranks.items(), key=lambda x: x[0]) if entry.r1_closing_ranks else (None, None)
            opportunities.append({
                "College": entry.college_name.split(",")[0][:50],
                "State": entry.state,
                "R1 Chance": entry.chance,
                "R1 Closing": f"{r1_latest[1]:,}" if r1_latest[1] else "N/A",
                "R2 Achievable": ", ".join(f"{yr}: {r:,}" for yr, r in sorted(achievable_years)),
                "Authority": entry.authority,
            })

    if not opportunities:
        st.info("No R2 opportunities found. All viable colleges are already in R1 predictions.")
        return

    st.markdown("""
    **These colleges are Unlikely/Borderline based on R1 cutoffs, but historically
    become achievable in Round 2.** Consider waiting for R2 if your preferred college appears here.
    """)
    df = pd.DataFrame(opportunities)
    st.dataframe(df, use_container_width=True, hide_index=True)
    st.caption(f"{len(opportunities)} colleges become achievable in R2")


# ═══════════════════════════════════════════════════════════════════════════════
# CHAT MODE
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

    # Extract marks (e.g. "375 marks", "scored 627", "got 450")
    marks_match = re.search(r'(\d{2,3})\s*(?:marks?|score)', query, re.IGNORECASE)
    if not marks_match:
        marks_match = re.search(r'(?:scored?|got|have|get)\s*(\d{2,3})', query, re.IGNORECASE)
    if not marks_match:
        # Try standalone 3-digit number that could be marks (100-720)
        marks_match = re.search(r'\b(\d{3})\b', query)
    if marks_match:
        m = int(marks_match.group(1))
        if 100 <= m <= 720:
            result["marks"] = m

    # Extract AIR (e.g. "AIR 15000", "rank 10000")
    air_match = re.search(r'(?:AIR|rank|air)\s*(?:is\s*)?(\d{1,7})', query, re.IGNORECASE)
    if air_match:
        result["actual_air"] = int(air_match.group(1))

    # Extract year (e.g. "in 2022", "NEET 2025", "2026")
    year_match = re.search(r'(20[2][0-6])', query)
    if year_match:
        result["target_year"] = int(year_match.group(1))

    # Extract category
    cat_map = {
        r'\bOBC\b': "OBC", r'\bSC\b': "SC", r'\bST\b': "ST",
        r'\bEWS\b': "EWS", r'\b[Gg]eneral\b': "General",
    }
    for pattern, cat in cat_map.items():
        if re.search(pattern, query):
            result["national_category"] = cat
            break

    # Extract state
    states = ["Karnataka", "Tamil Nadu", "Maharashtra", "Kerala", "Bihar",
              "UP", "Uttar Pradesh", "Rajasthan", "MP", "Madhya Pradesh",
              "Andhra Pradesh", "Telangana", "West Bengal", "Gujarat"]
    for state in states:
        if state.lower() in query.lower():
            result["home_state"] = state
            if state == "Karnataka":
                result["karnataka_interest"] = True
                result["karnataka_domicile"] = True
                result["karnataka_category"] = "GM"
            break

    # Karnataka interest
    if "karnataka" in query.lower():
        result["karnataka_interest"] = True
        result["karnataka_domicile"] = True
        result["karnataka_category"] = "GM"

    # College type
    if re.search(r'\bgov(?:ernment|t)\b', query, re.IGNORECASE):
        result["college_type_pref"] = "government"

    return result


def run_chat_prediction(query: str):
    """Run prediction from natural language — tries LLM first, falls back to regex."""
    # Try LLM-based pipeline first
    try:
        from neet_predictor.counsellor import (
            LLMClient, LLMClientError,
            run_counsellor, ClarificationNeeded, ValidatedResponse,
        )
        client = LLMClient()
        result = run_counsellor(query, client=client)
        return result, None, "llm"
    except Exception as llm_error:
        # LLM unavailable — fall back to regex parsing + direct engine
        pass

    # Fallback: regex parse → form-mode prediction
    try:
        parsed = _parse_query_fallback(query)
        if not parsed["marks"] and not parsed["actual_air"]:
            return None, "Could not extract marks or rank from your query. Please use the Form mode or try: 'I scored 550 marks in 2025'", "error"

        unified_result, student_result, error = run_form_prediction(
            marks=parsed["marks"],
            actual_air=parsed["actual_air"],
            target_year=parsed["target_year"] or VALIDATION_YEAR,
            national_category=parsed["national_category"],
            home_state=parsed["home_state"] or "Unknown",
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


def display_chat_result(result, mode: str):
    """Display counsellor pipeline result."""
    if mode == "fallback":
        # Fallback mode: show form results with extracted params
        unified_result, student_result, parsed = result
        st.info("🔄 **AI unavailable** — used smart text parsing instead. "
                "For best results, ensure Siemens API is accessible or use Form mode.")

        # Show what was extracted
        with st.expander("📝 Extracted from your query"):
            cols = st.columns(4)
            if parsed["marks"]:
                cols[0].metric("Marks", parsed["marks"])
            if parsed["target_year"]:
                cols[1].metric("Year", parsed["target_year"])
            if parsed["national_category"]:
                cols[2].metric("Category", parsed["national_category"])
            if parsed["home_state"]:
                cols[3].metric("State", parsed["home_state"])

        display_rank_section(unified_result)
        st.markdown("---")
        display_college_section(student_result)
        return

    # LLM mode
    from neet_predictor.counsellor import ClarificationNeeded, ValidatedResponse

    if isinstance(result, ClarificationNeeded):
        st.warning("Need more information:")
        for q in result.questions:
            st.markdown(f"- {q}")
        return

    if not isinstance(result, ValidatedResponse):
        st.error("Unexpected result type")
        return

    # Show narrative
    if result.narrative and not result.fallback_used:
        st.subheader("🤖 AI Analysis")
        st.markdown(result.narrative.full_narrative)
        st.caption(f"Model: {result.narrative.model_used} | Tokens: {result.narrative.tokens_used}")
    elif result.fallback_used:
        st.warning("AI narrative was removed due to validation issues. Showing raw results.")
        if result.violations:
            with st.expander("Validation issues"):
                for v in result.violations:
                    st.markdown(f"- ❌ {v}")

    # Show scenario comparison
    st.subheader("📊 Scenario Comparison")
    rows = []
    for row in result.scenarios.comparison_table:
        rows.append({
            "Scenario": row.label,
            "Safe": row.safe_count,
            "Likely": row.likely_count,
            "Borderline": row.borderline_count,
            "Total Viable": row.total_options,
            "Best College": (row.best_college or "N/A")[:40],
        })
    if rows:
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    # Show detailed results per scenario
    for sr in result.scenarios.results:
        if sr.error or sr.student_result is None:
            continue
        student_result = sr.student_result
        with st.expander(f"📋 {sr.spec.label} — Details"):
            display_rank_section_from_student(student_result)
            display_college_section(student_result)

    # Warnings and limitations
    if result.warnings:
        with st.expander("⚠️ Warnings"):
            for w in result.warnings:
                st.markdown(f"- {w}")
    if result.limitations:
        with st.expander("📝 Limitations"):
            for l in result.limitations:
                st.markdown(f"- {l}")

    st.caption(f"⏱️ Processing time: {result.processing_time_ms}ms")


def display_rank_section_from_student(student_result: StudentResult):
    """Display rank info from StudentResult."""
    st.markdown(f"**Rank used:** AIR {student_result.rank_used.air:,} ({student_result.rank_used.source})")


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN UI LOGIC
# ═══════════════════════════════════════════════════════════════════════════════

if input_mode == "📝 Form":
    st.markdown("---")

    # Form inputs
    col1, col2, col3 = st.columns(3)
    with col1:
        marks = st.number_input("NEET Marks (0-720)", min_value=0, max_value=720,
                                value=550, step=1)
    with col2:
        actual_air = st.number_input("Actual AIR (optional, 0=not known)",
                                     min_value=0, value=0, step=1)
    with col3:
        target_year = st.selectbox("Exam Year",
                                   [2026, 2025, 2024, 2023, 2022, 2021, 2020],
                                   index=1)

    col4, col5, col6 = st.columns(3)
    with col4:
        national_category = st.selectbox("National Category",
                                         ["General", "OBC", "SC", "ST", "EWS"])
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
                                          ["None", "GM", "1", "2A", "2B", "3A", "3B", "SC", "ST"],
                                          index=1)

    college_type_pref = st.selectbox("College Type Preference",
                                     ["Any", "Government", "Deemed"])

    # Year confidence indicator
    if target_year in TRAINING_YEARS:
        st.success(f"✅ Year {target_year} has training data — HIGH confidence prediction")
    elif target_year == VALIDATION_YEAR:
        st.success(f"✅ Year {target_year} has 530 calibration points — HIGH confidence")
    else:
        st.warning(f"⚠️ Year {target_year} has NO historical data — forward extrapolation (LOWER confidence)")

    # Predict button
    if st.button("🔍 Predict", type="primary", use_container_width=True):
        with st.spinner("Running prediction engine..."):
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
            st.session_state.results = (unified_result, student_result)

    # Display results
    if st.session_state.results:
        unified_result, student_result = st.session_state.results
        st.markdown("---")
        display_rank_section(unified_result)
        st.markdown("---")
        display_college_section(student_result)

        # Warnings
        if unified_result.warnings:
            st.markdown("---")
            st.subheader("⚠️ Warnings")
            for w in unified_result.warnings:
                st.caption(f"• {w}")

elif input_mode == "💬 Chat (AI)":
    st.markdown("---")
    st.markdown("**Ask anything about NEET admissions in natural language.**")
    st.caption("Examples: _'I scored 627 in 2022, General category from Karnataka, what colleges can I get?'_")
    st.caption("_'If I get 450 marks in 2026, what rank will I get?'_")

    # Chat input
    query = st.text_area("Your question:", height=80,
                         placeholder="Type your question here...")

    if st.button("🤖 Ask AI Counsellor", type="primary", use_container_width=True):
        if not query.strip():
            st.warning("Please enter a question.")
        else:
            with st.spinner("Analyzing your query..."):
                result, error, mode = run_chat_prediction(query)

            if error:
                st.error(f"❌ {error}")
            else:
                display_chat_result(result, mode)


# ═══════════════════════════════════════════════════════════════════════════════
# FOOTER
# ═══════════════════════════════════════════════════════════════════════════════

st.markdown("---")
st.caption("⚠️ **Disclaimer:** This tool provides predictions based on historical data (2020-2025). "
           "It is NOT an admission guarantee. Always verify from official MCC/KEA sources. "
           "Marks-to-rank conversion is experimental when actual AIR is not provided.")
