"""Hybrid prediction agent — combines dataset predictions with web search.

This agent takes a user query, runs:
1. Our dataset-based estimator (verified historical data)
2. Web search for external rank predictions
3. Merges both sources with confidence weighting

The result is more robust than either source alone:
- Our dataset: precise but narrow (only marks→rank mapping)
- Web search: broader context (counselling advice, cutoffs, tie-breaking)
  but less precise / may have errors
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

from neet_predictor.rank.estimator import RankEstimator, RankEstimate
from neet_predictor.integrated.web_search import (
    search_neet_rank,
    WebSearchOutput,
    search_colleges_for_rank,
    WebCollegeSearchOutput,
    WebCollegeResult,
)

logger = logging.getLogger(__name__)


@dataclass
class HybridRankResult:
    """Combined rank prediction from dataset + web sources."""

    # Final merged estimates
    final_rank_min: int
    final_rank_max: int
    final_rank_mid: int

    # Source breakdown
    dataset_estimate: RankEstimate | None = None
    web_estimate: WebSearchOutput | None = None

    # Merge metadata
    agreement: str = "unknown"  # "strong", "moderate", "divergent"
    divergence_pct: float = 0.0  # % difference between sources
    primary_source: str = "dataset"  # which source dominated

    # Context that web adds but dataset doesn't
    tie_breaking_notes: str = ""
    counselling_context: str = ""
    percentile_context: str = ""

    # Explanation
    explanation: str = ""


def run_hybrid_prediction(
    marks: int,
    year: int,
    category: str = "General",
    estimator: RankEstimator | None = None,
) -> HybridRankResult:
    """Run hybrid prediction combining dataset + web search.

    Strategy:
    - Dataset is PRIMARY (verified, precise)
    - Web is SECONDARY (adds context, cross-checks)
    - If they agree: high confidence, use dataset values
    - If they diverge: flag it, explain why, use weighted average

    Args:
        marks: NEET marks (0-720)
        year: Target exam year
        category: Student category (General, OBC, SC, ST, EWS)
        estimator: Pre-built estimator (optional, creates one if not provided)

    Returns:
        HybridRankResult with merged prediction and source attribution
    """
    # ── Step 1: Dataset prediction (primary) ──
    if estimator is None:
        estimator = RankEstimator(use_validation_data=True)

    dataset_result: RankEstimate | None = None
    try:
        dataset_result = estimator.estimate(marks, target_year=year, category=category)
    except (ValueError, Exception) as e:
        logger.warning(f"Dataset estimation failed: {e}")

    # ── Step 2: Web search (secondary) ──
    web_result: WebSearchOutput | None = None
    try:
        web_result = search_neet_rank(marks, year, category)
    except Exception as e:
        logger.debug(f"Web search failed: {e}")

    # ── Step 3: Merge ──
    return _merge_predictions(marks, year, category, dataset_result, web_result)


def _merge_predictions(
    marks: int,
    year: int,
    category: str,
    dataset: RankEstimate | None,
    web: WebSearchOutput | None,
) -> HybridRankResult:
    """Merge dataset and web predictions with intelligent weighting."""

    # Case 1: Only dataset available
    if dataset and (not web or not web.results):
        return HybridRankResult(
            final_rank_min=dataset.best_case_air,
            final_rank_max=dataset.conservative_air,
            final_rank_mid=dataset.median_air,
            dataset_estimate=dataset,
            web_estimate=web,
            agreement="dataset_only",
            primary_source="dataset",
            explanation=_build_explanation_dataset_only(marks, year, dataset),
        )

    # Case 2: Only web available
    if web and web.results and not dataset:
        mid = web.consensus_rank_mid or 0
        r_min = web.consensus_rank_min or mid
        r_max = web.consensus_rank_max or mid
        return HybridRankResult(
            final_rank_min=r_min,
            final_rank_max=r_max,
            final_rank_mid=mid,
            web_estimate=web,
            agreement="web_only",
            primary_source="web",
            explanation=_build_explanation_web_only(marks, year, web),
        )

    # Case 3: Both available — compare and merge
    assert dataset is not None and web is not None and web.results

    ds_mid = dataset.median_air
    web_mid = web.consensus_rank_mid or ds_mid

    # Calculate divergence
    divergence = abs(ds_mid - web_mid) / max(ds_mid, web_mid, 1)

    # Check if this is a future year (dataset range is very wide = uncertain)
    ds_range_ratio = (dataset.conservative_air - dataset.best_case_air) / max(dataset.median_air, 1)
    is_uncertain_dataset = ds_range_ratio > 2.0  # range > 2x the median = very uncertain

    if divergence < 0.15:
        # Strong agreement (<15% difference) — trust dataset
        agreement = "strong"
        final_min = dataset.best_case_air
        final_max = dataset.conservative_air
        final_mid = dataset.median_air
        primary = "dataset"
    elif divergence < 0.35:
        # Moderate agreement — weighted average (dataset 70%, web 30%)
        agreement = "moderate"
        final_mid = int(0.7 * ds_mid + 0.3 * web_mid)
        # Expand range to cover both sources
        final_min = min(dataset.best_case_air, web.consensus_rank_min or ds_mid)
        final_max = max(dataset.conservative_air, web.consensus_rank_max or ds_mid)
        primary = "dataset"
    elif is_uncertain_dataset:
        # Dataset is highly uncertain (future year) — trust web more
        agreement = "future_year_blend"
        # For future years, web represents "expected" difficulty (moderate paper)
        # Weight: web 60%, dataset 40%
        final_mid = int(0.4 * ds_mid + 0.6 * web_mid)
        web_min = web.consensus_rank_min or web_mid
        web_max = web.consensus_rank_max or web_mid
        # Use web's range as primary, but widen slightly with dataset
        final_min = min(web_min, int(ds_mid * 0.5))
        final_max = max(web_max, int(ds_mid * 1.5))
        primary = "blended"
    else:
        # Divergent — investigate why, still trust dataset but flag
        agreement = "divergent"
        # Dataset is primary (verified data), but widen the range
        final_mid = dataset.median_air
        web_min = web.consensus_rank_min or web_mid
        web_max = web.consensus_rank_max or web_mid
        final_min = min(dataset.best_case_air, web_min)
        final_max = max(dataset.conservative_air, web_max)
        primary = "dataset"

    # ── Build contextual notes ──
    tie_notes = _get_tie_breaking_context(marks, year)
    percentile_ctx = _get_percentile_context(marks, year, dataset)
    counselling_ctx = _get_counselling_context(final_mid, category)

    explanation = _build_explanation_merged(
        marks, year, dataset, web, agreement, divergence
    )

    return HybridRankResult(
        final_rank_min=final_min,
        final_rank_max=final_max,
        final_rank_mid=final_mid,
        dataset_estimate=dataset,
        web_estimate=web,
        agreement=agreement,
        divergence_pct=divergence * 100,
        primary_source=primary,
        tie_breaking_notes=tie_notes,
        counselling_context=counselling_ctx,
        percentile_context=percentile_ctx,
        explanation=explanation,
    )


# ── Context builders ──


def _get_tie_breaking_context(marks: int, year: int) -> str:
    """Add tie-breaking factor explanation (from NEET rules)."""
    return (
        "NEET tie-breaking order: (1) Higher marks in Biology, "
        "(2) Higher marks in Chemistry, (3) Fewer incorrect answers, "
        "(4) Older candidate gets preference. "
        "This can shift AIR by ±50-200 positions at competitive mark ranges."
    )


def _get_percentile_context(
    marks: int, year: int, dataset: RankEstimate | None
) -> str:
    """Calculate percentile position for context."""
    if not dataset or not dataset.target_appeared:
        return ""

    appeared = dataset.target_appeared
    rank = dataset.median_air
    percentile = (1 - rank / appeared) * 100

    return (
        f"With AIR ~{rank:,} out of {appeared:,} candidates, "
        f"you are in the **top {100 - percentile:.2f}%** (percentile: {percentile:.2f}). "
        f"This places you among the top {rank:,} scorers nationally."
    )


def _get_counselling_context(air: int, category: str) -> str:
    """Generate counselling-level interpretation."""
    lines = []

    if air < 1000:
        lines.append("Eligible for: AIIMS Delhi, MAMC, JIPMER, top central institutes")
        lines.append("Strategy: Focus on AIQ Round 1 top choices")
    elif air < 5000:
        lines.append("Eligible for: AIIMS branches, top state GMCs, VMMC, UCMS-level colleges")
        lines.append("Strategy: Mix top GMCs + AIIMS branches in choice list")
    elif air < 15000:
        lines.append("Eligible for: Mid-tier Government Medical Colleges across states")
        lines.append("Strategy: Prioritize govt colleges in preferred states via AIQ + state counselling")
    elif air < 50000:
        lines.append("Eligible for: State Government Medical Colleges (via state quota primarily)")
        lines.append("Strategy: Register for BOTH MCC AIQ and state counselling. State quota is your best path.")
    elif air < 100000:
        lines.append("Options: Some state GMCs via state quota + Private/Deemed universities")
        lines.append("Strategy: State counselling priority. Keep private colleges as backup.")
    else:
        lines.append("Options: Private/Deemed medical colleges, some management quota seats")
        lines.append("Strategy: Register for all counselling rounds. Watch for mop-up/stray vacancy rounds.")

    if category in ("OBC", "SC", "ST", "EWS"):
        lines.append(
            f"Category advantage: As {category}, your effective cutoff is lower. "
            f"You may get colleges typically requiring 20-40% better rank in General category."
        )

    return " | ".join(lines)


# ── Explanation builders ──


def _build_explanation_dataset_only(
    marks: int, year: int, dataset: RankEstimate
) -> str:
    """Explanation when only dataset is available."""
    return (
        f"Prediction from verified dataset (6 years of NEET data, {dataset.method}). "
        f"Confidence: {dataset.confidence}. "
        f"Web cross-check unavailable — relying on historical data alone."
    )


def _build_explanation_web_only(
    marks: int, year: int, web: WebSearchOutput
) -> str:
    """Explanation when only web results are available."""
    return (
        f"Prediction from web sources ({web.source_count} results). "
        f"Dataset unavailable for this query. "
        f"Web estimates may be approximate — verify from official NTA results."
    )


def _build_explanation_merged(
    marks: int,
    year: int,
    dataset: RankEstimate,
    web: WebSearchOutput,
    agreement: str,
    divergence: float,
) -> str:
    """Build explanation for merged result."""
    lines = []

    if agreement == "strong":
        lines.append(
            f"✅ Strong agreement between our dataset (AIR {dataset.median_air:,}) "
            f"and web sources (AIR ~{web.consensus_rank_mid:,}). "
            f"Divergence: {divergence*100:.1f}%. Using verified dataset values."
        )
    elif agreement == "moderate":
        lines.append(
            f"🟡 Moderate agreement. Dataset: AIR {dataset.median_air:,}, "
            f"Web: AIR ~{web.consensus_rank_mid:,} ({divergence*100:.1f}% divergence). "
            f"Using weighted average (dataset 70% / web 30%)."
        )
    elif agreement == "future_year_blend":
        lines.append(
            f"🔮 Future year prediction (paper difficulty unknown). "
            f"Dataset across all years: AIR {dataset.median_air:,} "
            f"(range {dataset.best_case_air:,}–{dataset.conservative_air:,}). "
            f"Web consensus (assuming moderate paper): AIR ~{web.consensus_rank_mid:,}. "
            f"Using blended estimate (web 60% / dataset 40%) since paper difficulty is unknown."
        )
    else:
        lines.append(
            f"⚠️ Sources diverge significantly. Dataset: AIR {dataset.median_air:,}, "
            f"Web: AIR ~{web.consensus_rank_mid:,} ({divergence*100:.1f}% apart). "
            f"Trusting dataset (verified data) but widening range to account for uncertainty."
        )
        # Add possible reasons for divergence
        lines.append(
            "Possible reasons: different methodology, "
            "web using different year's data, or web aggregating multiple categories."
        )

    lines.append(f"Dataset confidence: {dataset.confidence} ({dataset.method}).")
    lines.append(f"Web sources consulted: {web.source_count}.")

    return " ".join(lines)


# ═══════════════════════════════════════════════════════════════════════════════
# COLLEGE HYBRID PREDICTION
# ═══════════════════════════════════════════════════════════════════════════════


@dataclass
class CollegeComparison:
    """A single college comparison between web and dataset."""

    college_name: str
    state: str = ""
    # Dataset prediction
    in_dataset: bool = False
    dataset_chance: str = ""  # Safe/Likely/Borderline/Unlikely
    dataset_closing_rank: int | None = None
    # Web source
    in_web: bool = False
    web_closing_rank: int | None = None
    web_source: str = ""
    # Merged assessment
    merged_verdict: str = ""  # "Confirmed", "Web-only suggestion", "Dataset-only"
    notes: str = ""


@dataclass
class HybridCollegeResult:
    """Combined college prediction from dataset + web sources."""

    # All compared colleges
    comparisons: list[CollegeComparison] = field(default_factory=list)

    # Colleges found by web but NOT in our dataset
    web_only_colleges: list[WebCollegeResult] = field(default_factory=list)

    # Summary stats
    total_dataset_colleges: int = 0
    total_web_colleges: int = 0
    confirmed_count: int = 0  # present in both

    # Web search output
    web_search_output: WebCollegeSearchOutput | None = None

    # Agreement assessment
    agreement: str = "unknown"  # "strong", "moderate", "divergent", "dataset_only"
    explanation: str = ""


def run_hybrid_college_prediction(
    air: int,
    year: int,
    category: str = "General",
    state: str | None = None,
    dataset_predictions: list | None = None,
) -> HybridCollegeResult:
    """Run hybrid college prediction combining dataset + web search.

    Args:
        air: All India Rank to search colleges for
        year: Target admission year
        category: Student category
        state: Home state (for state quota filtering)
        dataset_predictions: List of CollegePrediction from our pipeline
            (each has .college_name, .chance, .closing_rank_r1, etc.)

    Returns:
        HybridCollegeResult with merged college list and comparisons
    """
    result = HybridCollegeResult()

    # ── Step 1: Web search for colleges ──
    web_output: WebCollegeSearchOutput | None = None
    try:
        web_output = search_colleges_for_rank(air, year, category, state)
        result.web_search_output = web_output
        result.total_web_colleges = len(web_output.colleges) if web_output else 0
    except Exception as e:
        logger.debug(f"College web search failed: {e}")

    # ── Step 2: Get dataset prediction names (normalized for matching) ──
    ds_colleges: dict[str, object] = {}
    if dataset_predictions:
        result.total_dataset_colleges = len(dataset_predictions)
        for pred in dataset_predictions:
            # Normalize college name for fuzzy matching
            key = _normalize_college_name(getattr(pred, "college_name", str(pred)))
            ds_colleges[key] = pred

    # ── Step 3: Compare web colleges against dataset ──
    if web_output and web_output.colleges:
        for web_col in web_output.colleges:
            web_key = _normalize_college_name(web_col.college_name)

            # Try to find in dataset
            matched_pred = _fuzzy_find(web_key, ds_colleges)

            if matched_pred:
                # Found in both sources → confirmed
                ds_chance = getattr(matched_pred, "chance", "")
                # CollegePrediction uses r1_closing_ranks: dict[int, int]
                r1_ranks = getattr(matched_pred, "r1_closing_ranks", {})
                ds_closing = max(r1_ranks.values()) if r1_ranks else None
                comp = CollegeComparison(
                    college_name=web_col.college_name,
                    state=web_col.state,
                    in_dataset=True,
                    dataset_chance=ds_chance,
                    dataset_closing_rank=ds_closing,
                    in_web=True,
                    web_closing_rank=web_col.closing_rank,
                    web_source=web_col.source,
                    merged_verdict="Confirmed",
                    notes=f"Both dataset and web agree this college is accessible at AIR {air:,}",
                )
                result.comparisons.append(comp)
                result.confirmed_count += 1
            else:
                # Web-only college (not in our dataset)
                comp = CollegeComparison(
                    college_name=web_col.college_name,
                    state=web_col.state,
                    in_dataset=False,
                    in_web=True,
                    web_closing_rank=web_col.closing_rank,
                    web_source=web_col.source,
                    merged_verdict="Web-only suggestion",
                    notes="Found in web sources but not in our dataset — verify independently",
                )
                result.comparisons.append(comp)
                result.web_only_colleges.append(web_col)

    # ── Step 4: Add dataset-only colleges ──
    if dataset_predictions:
        matched_web_keys = set()
        if web_output and web_output.colleges:
            matched_web_keys = {
                _normalize_college_name(c.college_name) for c in web_output.colleges
            }

        for pred in dataset_predictions:
            pred_name = getattr(pred, "college_name", str(pred))
            pred_key = _normalize_college_name(pred_name)
            # Check if already matched
            if not _fuzzy_find_key(pred_key, matched_web_keys):
                r1_ranks = getattr(pred, "r1_closing_ranks", {})
                ds_closing = max(r1_ranks.values()) if r1_ranks else None
                comp = CollegeComparison(
                    college_name=pred_name,
                    state=getattr(pred, "state", ""),
                    in_dataset=True,
                    dataset_chance=getattr(pred, "chance", ""),
                    dataset_closing_rank=ds_closing,
                    in_web=False,
                    merged_verdict="Dataset-only",
                    notes="From our verified dataset (historical closing ranks)",
                )
                result.comparisons.append(comp)

    # ── Step 5: Compute agreement ──
    result.agreement = _compute_college_agreement(result)
    result.explanation = _build_college_explanation(result, air, year, category)

    return result


def _normalize_college_name(name: str) -> str:
    """Normalize college name for fuzzy matching."""
    import re

    name = name.lower().strip()
    # Remove common prefixes/suffixes
    name = re.sub(r"\[stretch\]\s*", "", name)
    name = re.sub(r"\b(govt\.?|government)\b", "govt", name)
    name = re.sub(r"\b(medical college|medical)\b", "mc", name)
    name = re.sub(r"\b(institute of medical sciences)\b", "ims", name)
    # Remove punctuation
    name = re.sub(r"[^\w\s]", "", name)
    # Collapse whitespace
    name = re.sub(r"\s+", " ", name).strip()
    return name


def _fuzzy_find(key: str, ds_colleges: dict[str, object]) -> object | None:
    """Find a matching college in the dataset (fuzzy keyword overlap)."""
    if key in ds_colleges:
        return ds_colleges[key]

    # Try substring matching (core words)
    key_words = set(key.split()) - {"mc", "govt", "of", "the", "and", "college"}
    for ds_key, pred in ds_colleges.items():
        ds_words = set(ds_key.split()) - {"mc", "govt", "of", "the", "and", "college"}
        # If >60% of significant words overlap, consider it a match
        if key_words and ds_words:
            overlap = len(key_words & ds_words) / min(len(key_words), len(ds_words))
            if overlap >= 0.6:
                return pred

    return None


def _fuzzy_find_key(key: str, key_set: set[str]) -> bool:
    """Check if a key fuzzy-matches any key in the set."""
    if key in key_set:
        return True

    key_words = set(key.split()) - {"mc", "govt", "of", "the", "and", "college"}
    for other in key_set:
        other_words = set(other.split()) - {"mc", "govt", "of", "the", "and", "college"}
        if key_words and other_words:
            overlap = len(key_words & other_words) / min(len(key_words), len(other_words))
            if overlap >= 0.6:
                return True

    return False


def _compute_college_agreement(result: HybridCollegeResult) -> str:
    """Compute agreement level between web and dataset college lists."""
    if result.total_web_colleges == 0:
        return "dataset_only"
    if result.total_dataset_colleges == 0:
        return "web_only"

    # Overlap ratio
    overlap = result.confirmed_count / max(
        min(result.total_web_colleges, result.total_dataset_colleges), 1
    )

    if overlap > 0.5:
        return "strong"
    elif overlap > 0.2:
        return "moderate"
    else:
        return "divergent"


def _build_college_explanation(
    result: HybridCollegeResult,
    air: int,
    year: int,
    category: str,
) -> str:
    """Build explanation for college hybrid result."""
    lines = []

    if result.agreement == "dataset_only":
        lines.append(
            f"College predictions from verified dataset only. "
            f"{result.total_dataset_colleges} colleges found for AIR {air:,} ({category})."
        )
    elif result.agreement == "strong":
        lines.append(
            f"✅ Strong overlap between dataset and web. "
            f"{result.confirmed_count} colleges confirmed by both sources."
        )
    elif result.agreement == "moderate":
        lines.append(
            f"🟡 Partial overlap. {result.confirmed_count} colleges confirmed by both, "
            f"{len(result.web_only_colleges)} web-only suggestions to explore."
        )
    elif result.agreement == "divergent":
        lines.append(
            f"⚠️ Limited overlap between sources. Web suggests colleges "
            f"not in our dataset — may be newer or different counselling authority."
        )
    else:
        lines.append(
            f"College list from web sources. "
            f"{result.total_web_colleges} colleges found for AIR {air:,}."
        )

    if result.web_only_colleges:
        web_names = [c.college_name for c in result.web_only_colleges[:5]]
        lines.append(
            f"Web also suggests: {', '.join(web_names)}. "
            f"These are not in our verified dataset — confirm from official sources."
        )

    return " ".join(lines)
