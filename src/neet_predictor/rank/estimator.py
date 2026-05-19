"""Marks-to-AIR rank estimator using weighted percentile-space interpolation.

Algorithm:
1. Convert historical (marks, rank) anchors to percentile space per year.
2. Build monotonic piecewise-linear curves per year.
3. For input marks, interpolate each year's curve.
4. Combine using year weights (renormalized for missing years).
5. Convert weighted percentile back to AIR using target-year candidate count.
6. Produce best-case, median, and conservative AIR estimates with confidence.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np
import pandas as pd

from neet_predictor.config import (
    CURATED_DIR,
    SOURCES_DIR,
    YEAR_WEIGHTS,
    TRAINING_YEARS,
    VALIDATION_YEAR,
    MAX_MARKS,
    MIN_MARKS,
)
from neet_predictor.rank.calibration import (
    NormalizationMode,
    YearNormParams,
    normalize_marks,
)


# ── Data paths ──
_EXAM_YEARS_PATH = CURATED_DIR / "exam_years.csv"
_MARKS_RANK_PATH = CURATED_DIR / "marks_rank_points.csv"
_CUTOFF_STATS_PATH = CURATED_DIR / "category_cutoff_stats.csv"
_TIE_BREAKING_PATH = CURATED_DIR / "tie_breaking_rules.csv"

# Proximity-weight decay constant (marks).
# Full weight when anchor is right on the input marks;
# weight halves every ~21 marks of distance.
_PROXIMITY_DECAY = 30.0

# A year must have at least this fraction of the best year's effective weight
# to participate in the envelope (best/conservative) calculation.
_SIGNIFICANT_WEIGHT_FRACTION = 0.10

# Direct interpolation: minimum number of high-confidence anchors needed
# within a year for the "fast path" (direct lookup) to activate.
_DIRECT_INTERP_MIN_ANCHORS = 5

# Maximum distance (marks) from nearest anchor for direct interpolation.
_DIRECT_INTERP_MAX_GAP = 15

# When target year has direct data, it gets this weight (vs normal ~0.18)
_TARGET_YEAR_BOOST_WEIGHT = 0.75

# Other years get reduced weight when direct path is active
_OTHER_YEAR_REDUCTION = 0.25


# ── Result schema ──


@dataclass
class RankEstimate:
    """Result of marks-to-AIR estimation."""

    marks: int
    best_case_air: int
    median_air: int
    conservative_air: int
    confidence: str  # "high", "medium", "low"
    method: str
    training_years: list[int]
    validation_year: int
    explanation: str
    nearest_anchors: list[dict[str, Any]]
    below_cutoff_warning: str | None = None
    target_year: int | None = None
    target_appeared: int | None = None


# ── Year Curve ──


@dataclass
class _YearCurve:
    """Monotonic interpolation curve for one year."""

    year: int
    appeared: int
    marks_points: np.ndarray  # sorted ascending
    pct_best: np.ndarray  # decreasing (lower = better rank)
    pct_worst: np.ndarray  # decreasing
    pct_mid: np.ndarray  # decreasing
    marks_min: float  # lowest anchor marks
    marks_max: float  # highest anchor marks


# ── Core estimator ──


class RankEstimator:
    """Marks-to-AIR estimator using weighted percentile-space interpolation."""

    def __init__(
        self,
        use_validation_data: bool = False,
        normalization: NormalizationMode = NormalizationMode.NONE,
    ):
        """Initialize estimator.

        Args:
            use_validation_data: If False (default), exclude 2025 from training.
                Set True ONLY for testing the validation harness itself.
            normalization: Paper-difficulty normalization strategy.
        """
        self._use_validation = use_validation_data
        self._normalization = normalization
        self._exam_years: pd.DataFrame = pd.DataFrame()
        self._marks_rank: pd.DataFrame = pd.DataFrame()
        self._cutoff_stats: pd.DataFrame = pd.DataFrame()
        self._curves: dict[int, _YearCurve] = {}
        self._appeared: dict[int, int] = {}
        self._highest: dict[int, int] = {}  # year → highest_marks
        self._cutoff_ur: dict[int, int] = {}  # year → UR cutoff marks
        self._cutoffs: dict[int, dict[str, int]] = {}  # {year: {category: marks}}
        self._norm_params: dict[int, YearNormParams] = {}
        self._load_data()
        self._build_curves()

    def _load_data(self) -> None:
        """Load curated data files."""
        self._exam_years = pd.read_csv(_EXAM_YEARS_PATH)
        self._marks_rank = pd.read_csv(_MARKS_RANK_PATH)
        self._cutoff_stats = pd.read_csv(_CUTOFF_STATS_PATH)

        # Build appeared / highest / cutoff_ur lookups
        for _, row in self._exam_years.iterrows():
            yr = int(row["year"])
            self._appeared[yr] = int(row["appeared_candidates"])
            self._highest[yr] = int(row["highest_marks"])
            self._cutoff_ur[yr] = int(row["cutoff_ur"])
            self._norm_params[yr] = YearNormParams(
                year=yr,
                highest_marks=int(row["highest_marks"]),
                cutoff_ur=int(row["cutoff_ur"]),
                toppers_at_highest=int(row["toppers_at_highest"]),
                appeared=int(row["appeared_candidates"]),
            )

        # Build cutoff lookup {year: {"UR": marks, "OBC": marks, ...}}
        for _, row in self._cutoff_stats.iterrows():
            yr = int(row["year"])
            cat = row["category"]
            if yr not in self._cutoffs:
                self._cutoffs[yr] = {}
            self._cutoffs[yr][cat] = int(row["marks_min"])

    def _build_curves(self) -> None:
        """Build monotonic interpolation curves for each training year."""
        years_to_use = TRAINING_YEARS
        if self._use_validation:
            years_to_use = TRAINING_YEARS + [VALIDATION_YEAR]

        for year in years_to_use:
            year_data = self._marks_rank[self._marks_rank["year"] == year]
            if year_data.empty:
                continue  # Skip years with no data (e.g., 2021)

            appeared = self._appeared.get(year)
            if not appeared:
                continue

            curve = self._build_one_curve(year, year_data, appeared)
            if curve is not None:
                self._curves[year] = curve

    def _build_one_curve(
        self, year: int, data: pd.DataFrame, appeared: int
    ) -> _YearCurve | None:
        """Build a monotonic curve for one year."""
        # Compute marks midpoint and percentiles
        points = []
        for _, row in data.iterrows():
            marks_mid = (row["marks_min"] + row["marks_max"]) / 2.0
            rank_min = row["rank_min"]
            rank_max = row["rank_max"]

            # Percentile = rank / appeared (lower = better)
            pct_best = rank_min / appeared
            pct_worst = rank_max / appeared
            pct_mid = (pct_best + pct_worst) / 2.0

            points.append((marks_mid, pct_best, pct_worst, pct_mid))

        if not points:
            return None

        # Sort by marks ascending
        points.sort(key=lambda x: x[0])

        marks_arr = np.array([p[0] for p in points])
        pct_best_arr = np.array([p[1] for p in points])
        pct_worst_arr = np.array([p[2] for p in points])
        pct_mid_arr = np.array([p[3] for p in points])

        # Enforce monotonicity: as marks increase, percentile must decrease
        pct_best_arr = _enforce_decreasing(pct_best_arr)
        pct_worst_arr = _enforce_decreasing(pct_worst_arr)
        pct_mid_arr = _enforce_decreasing(pct_mid_arr)

        return _YearCurve(
            year=year,
            appeared=appeared,
            marks_points=marks_arr,
            pct_best=pct_best_arr,
            pct_worst=pct_worst_arr,
            pct_mid=pct_mid_arr,
            marks_min=float(marks_arr[0]),
            marks_max=float(marks_arr[-1]),
        )

    def _try_direct_interpolation(
        self, marks: int, target_year: int, target_appeared: int
    ) -> dict | None:
        """Attempt direct linear interpolation within target year's precise data.

        Returns dict with rank_min, rank_mid, rank_max if successful, else None.
        Only activates when target year has dense high-confidence anchors
        bracketing the input marks.
        """
        if target_year not in self._appeared:
            return None

        # Only use direct interpolation for training years (not validation)
        if target_year == VALIDATION_YEAR and not self._use_validation:
            return None
        if target_year not in TRAINING_YEARS and target_year != VALIDATION_YEAR:
            return None

        # Get high-confidence data for the target year only
        year_data = self._marks_rank[
            (self._marks_rank["year"] == target_year)
            & (self._marks_rank["confidence"] == "high")
        ].copy()

        if len(year_data) < _DIRECT_INTERP_MIN_ANCHORS:
            return None

        year_data = year_data.sort_values("marks_min", ascending=True)
        marks_vals = year_data["marks_min"].values

        # Find bracketing anchors
        below = year_data[year_data["marks_min"] <= marks]
        above = year_data[year_data["marks_min"] >= marks]

        if below.empty or above.empty:
            return None  # Outside range of precise data

        lower = below.iloc[-1]  # highest marks <= input
        upper = above.iloc[0]   # lowest marks >= input

        # Check gap isn't too large
        gap = int(upper["marks_min"]) - int(lower["marks_min"])
        if gap > _DIRECT_INTERP_MAX_GAP * 2:
            return None  # Anchors too far apart

        # Check distance from input to nearest anchor
        dist_lower = marks - int(lower["marks_min"])
        dist_upper = int(upper["marks_min"]) - marks

        if min(dist_lower, dist_upper) > _DIRECT_INTERP_MAX_GAP:
            return None

        # Linear interpolation
        if gap == 0:
            # Exact match
            return {
                "rank_min": int(lower["rank_min"]),
                "rank_mid": (int(lower["rank_min"]) + int(lower["rank_max"])) // 2,
                "rank_max": int(lower["rank_max"]),
            }

        # Fraction from lower to upper (0=at lower marks, 1=at upper marks)
        # As marks increase toward upper, rank improves (gets lower)
        frac = dist_lower / gap

        # Interpolate: frac=1 means at upper (better rank), frac=0 at lower (worse rank)
        rank_min = int(lower["rank_min"]) * (1 - frac) + int(upper["rank_min"]) * frac
        rank_max = int(lower["rank_max"]) * (1 - frac) + int(upper["rank_max"]) * frac
        rank_mid = (rank_min + rank_max) / 2

        return {
            "rank_min": max(1, int(round(rank_min))),
            "rank_mid": max(1, int(round(rank_mid))),
            "rank_max": max(1, int(round(rank_max))),
        }

    def estimate(
        self,
        marks: int,
        target_year: int | None = None,
        category: str | None = None,
    ) -> RankEstimate:
        """Estimate AIR range for given NEET marks.

        Args:
            marks: NEET marks (0-720).
            target_year: Year for appeared_candidates scaling. Default: latest.
            category: Optional category for cutoff warning (not used for AIR).

        Returns:
            RankEstimate with best/median/conservative AIR and confidence.
        """
        # ── Validate ──
        if not isinstance(marks, (int, float)) or marks < MIN_MARKS or marks > MAX_MARKS:
            raise ValueError(
                f"Marks must be between {MIN_MARKS} and {MAX_MARKS}, got {marks}"
            )
        marks = int(marks)

        # ── Determine target appeared ──
        # Track whether user requested a future/unknown year
        _future_year = False
        if target_year and target_year in self._appeared:
            target_appeared = self._appeared[target_year]
        else:
            # Future year or unknown — use latest year's candidate count
            # but mark as future so we DON'T use direct interpolation
            # from any single year (which could be anomalous like 2025)
            _future_year = True
            target_year = max(self._appeared.keys())
            target_appeared = self._appeared[target_year]

        # ── Resolve target normalization params ──
        target_norm = self._norm_params.get(
            target_year,
            YearNormParams(target_year, MAX_MARKS, 0),
        )

        # ── FAST PATH: Direct interpolation if target year has dense data ──
        # Disabled for future/unknown years — can't assume any single year's
        # paper difficulty applies to the future.
        direct_result = None
        if not _future_year:
            direct_result = self._try_direct_interpolation(marks, target_year, target_appeared)

        # ── Interpolate each year with proximity weighting ──
        year_results: list[tuple[int, float, float, float, float]] = []
        # (year, pct_best, pct_mid, pct_worst, effective_weight)

        for yr, curve in self._curves.items():
            if yr == VALIDATION_YEAR and not self._use_validation:
                continue

            # Paper-difficulty normalization: map query marks to this
            # training year's scale before curve lookup.
            train_norm = self._norm_params.get(
                yr, YearNormParams(yr, MAX_MARKS, 0)
            )
            query_marks = normalize_marks(
                marks, self._normalization, target_norm, train_norm
            )

            pct_b = _interpolate_curve(query_marks, curve.marks_points, curve.pct_best)
            pct_m = _interpolate_curve(query_marks, curve.marks_points, curve.pct_mid)
            pct_w = _interpolate_curve(query_marks, curve.marks_points, curve.pct_worst)

            # Adaptive year weights: if target is a training year, boost it
            base_w = YEAR_WEIGHTS.get(yr, 0.05)
            if direct_result is not None and yr == target_year:
                # Target year gets dominant weight when direct data exists
                base_w = _TARGET_YEAR_BOOST_WEIGHT
            elif direct_result is not None:
                # Other years get reduced weight
                base_w = base_w * _OTHER_YEAR_REDUCTION

            # Proximity decay: distance in *normalized* marks space
            min_dist = float(np.min(np.abs(curve.marks_points - query_marks)))
            proximity_w = float(np.exp(-min_dist / _PROXIMITY_DECAY))
            effective_w = base_w * proximity_w

            year_results.append((yr, pct_b, pct_m, pct_w, effective_w))

        if not year_results:
            raise ValueError(
                "No training data available for interpolation. "
                "Check that marks_rank_points.csv has data for training years."
            )

        # ── Identify significant years (≥10% of best year's weight) ──
        max_w = max(r[4] for r in year_results)
        significant = [
            r for r in year_results
            if r[4] >= max_w * _SIGNIFICANT_WEIGHT_FRACTION
        ]
        if not significant:
            significant = year_results  # fallback: use all

        # ── Median: use direct interpolation if available, else weighted ──
        total_weight = sum(r[4] for r in significant)
        w_pct_mid = sum(r[2] * r[4] for r in significant) / total_weight

        if direct_result is not None:
            # Direct interpolation gives the most accurate median
            best_air = direct_result["rank_min"]
            median_air = direct_result["rank_mid"]
            conservative_air = direct_result["rank_max"]
        else:
            # ── Best/Conservative: envelope across significant years ──
            env_pct_best = min(r[1] for r in significant)
            env_pct_worst = max(r[3] for r in significant)

            # ── Convert percentile → AIR ──
            best_air = max(1, int(round(env_pct_best * target_appeared)))
            median_air = max(1, int(round(w_pct_mid * target_appeared)))
            conservative_air = max(1, int(round(env_pct_worst * target_appeared)))

        # Ensure ordering: best <= median <= conservative
        best_air = min(best_air, median_air)
        conservative_air = max(conservative_air, median_air)

        # ── Confidence scoring ──
        confidence = self._assess_confidence(marks, year_results)
        if direct_result is not None:
            confidence = "high"  # Direct interpolation is always high confidence

        # ── Nearest anchors ──
        nearest = self._find_nearest_anchors(marks)

        # ── Below-cutoff warning ──
        cutoff_warning = self._check_cutoff(marks, category, target_year)

        # ── Explanation ──
        explanation = self._build_explanation(
            marks, year_results, total_weight, target_year, target_appeared,
            confidence, direct_result,
        )

        # ── Method label ──
        method = "direct_interpolation" if direct_result else "weighted_percentile_interpolation"
        if self._normalization != NormalizationMode.NONE:
            method += f"_{self._normalization.value}"

        return RankEstimate(
            marks=marks,
            best_case_air=best_air,
            median_air=median_air,
            conservative_air=conservative_air,
            confidence=confidence,
            method=method,
            training_years=[yr for yr, *_ in year_results],
            validation_year=VALIDATION_YEAR,
            explanation=explanation,
            nearest_anchors=nearest,
            below_cutoff_warning=cutoff_warning,
            target_year=target_year,
            target_appeared=target_appeared,
        )

    def _assess_confidence(
        self,
        marks: int,
        year_results: list[tuple[int, float, float, float, float]],
    ) -> str:
        """Assess confidence of the estimate."""
        # Count significant years (not all years — proximity-weighted)
        max_w = max(r[4] for r in year_results) if year_results else 0
        n_significant = sum(
            1 for r in year_results
            if r[4] >= max_w * _SIGNIFICANT_WEIGHT_FRACTION
        )

        # Check distance to nearest anchor across all training years
        min_distance = self._min_anchor_distance(marks)

        # Cross-year variance in pct_mid (among significant years)
        sig = [
            r[2] for r in year_results
            if r[4] >= max_w * _SIGNIFICANT_WEIGHT_FRACTION
        ]
        pct_variance = float(np.var(sig)) if len(sig) > 1 else 0.0

        # Check if extrapolating beyond known range
        extrapolating = self._is_extrapolating(marks)

        # Scoring
        if extrapolating:
            return "low"
        if n_significant <= 1:
            return "low"
        if min_distance > 50:
            # Far from any anchor (>50 marks away)
            if pct_variance > 0.01:
                return "low"
            return "medium"
        if min_distance > 20:
            if pct_variance > 0.005:
                return "medium"
            return "medium"
        # Close to anchors, multiple years, low variance
        if n_significant >= 3 and pct_variance < 0.002:
            return "high"
        return "medium"

    def _min_anchor_distance(self, marks: int) -> float:
        """Find minimum distance to any training anchor (in marks)."""
        training = self._marks_rank[
            self._marks_rank["year"].isin(TRAINING_YEARS)
        ]
        if training.empty:
            return 999.0

        midpoints = (training["marks_min"] + training["marks_max"]) / 2.0
        distances = abs(midpoints - marks)
        return float(distances.min())

    def _is_extrapolating(self, marks: int) -> bool:
        """Check if marks is outside the range of ALL training curves."""
        for curve in self._curves.values():
            if curve.year == VALIDATION_YEAR:
                continue
            if curve.marks_min <= marks <= curve.marks_max:
                return False
        return True

    def _find_nearest_anchors(self, marks: int, n: int = 4) -> list[dict]:
        """Find the n nearest training anchors to the input marks."""
        training = self._marks_rank[
            self._marks_rank["year"].isin(TRAINING_YEARS)
        ]
        if training.empty:
            return []

        training = training.copy()
        training["marks_mid"] = (
            training["marks_min"] + training["marks_max"]
        ) / 2.0
        training["distance"] = abs(training["marks_mid"] - marks)
        nearest = training.nsmallest(n, "distance")

        result = []
        for _, row in nearest.iterrows():
            result.append({
                "year": int(row["year"]),
                "marks_min": int(row["marks_min"]),
                "marks_max": int(row["marks_max"]),
                "rank_min": int(row["rank_min"]),
                "rank_max": int(row["rank_max"]),
                "confidence": row["confidence"],
            })
        return result

    def _check_cutoff(
        self, marks: int, category: str | None, target_year: int | None
    ) -> str | None:
        """Check if marks is below qualifying cutoff for the category."""
        if category is None:
            # Check against UR (highest) cutoff for most recent year
            latest = max(self._cutoffs.keys())
            ur_cutoff = self._cutoffs.get(latest, {}).get("UR", 0)
            if marks < ur_cutoff:
                return (
                    f"Marks {marks} may be below the General/UR qualifying "
                    f"cutoff ({ur_cutoff} in {latest}). Candidate may not "
                    f"qualify for counselling depending on category and year."
                )
            return None

        # Check specific category
        cat_map = {"General": "UR", "EWS": "UR", "OBC": "OBC", "SC": "SC", "ST": "ST"}
        mapped = cat_map.get(category, category)

        # Check across years to determine if below cutoff
        below_years = []
        for yr, cutoffs in self._cutoffs.items():
            cutoff = cutoffs.get(mapped, cutoffs.get("UR", 0))
            if marks < cutoff:
                below_years.append(yr)

        if below_years:
            return (
                f"Marks {marks} is below the {category} qualifying cutoff "
                f"in year(s): {below_years}. Candidate may not qualify for "
                f"NEET counselling in those years."
            )
        return None

    def _build_explanation(
        self,
        marks: int,
        year_results: list[tuple[int, float, float, float, float]],
        total_weight: float,
        target_year: int | None,
        target_appeared: int,
        confidence: str,
        direct_result: dict | None = None,
    ) -> str:
        """Build human-readable explanation of the estimate."""
        lines = []

        if direct_result is not None:
            lines.append(
                f"DIRECT INTERPOLATION from {target_year} high-confidence data. "
                f"Rank range: {direct_result['rank_min']:,}-{direct_result['rank_max']:,} "
                f"(median: {direct_result['rank_mid']:,})."
            )
            lines.append(f"Target year: {target_year} ({target_appeared:,} candidates).")
            lines.append(f"Confidence: {confidence} (direct data match).")
            lines.append(
                "Note: Exact AIR cannot be predicted because tie-breaking "
                "depends on subject-wise scores."
            )
            return " ".join(lines)

        method_desc = "weighted percentile interpolation"
        if self._normalization != NormalizationMode.NONE:
            method_desc += f" with {self._normalization.value} paper-difficulty adjustment"
            target_h = self._highest.get(target_year, MAX_MARKS)
            lines.append(
                f"Paper-difficulty adjustment applied: target year "
                f"highest={target_h}, strategy={self._normalization.value}."
            )
        lines.append(
            f"Estimated AIR for {marks} marks using {method_desc} "
            f"across {len(year_results)} training year(s)."
        )
        lines.append(f"Target year: {target_year} ({target_appeared:,} candidates).")

        for yr, pb, pm, pw, w in year_results:
            norm_w = w / total_weight
            lines.append(
                f"  {yr}: pct_best={pb:.6f}, pct_mid={pm:.6f}, "
                f"pct_worst={pw:.6f} (weight={norm_w:.2f})"
            )

        lines.append(f"Confidence: {confidence}.")
        if confidence == "low":
            lines.append(
                "  Low confidence due to sparse anchors, extrapolation, "
                "or high cross-year variance."
            )

        lines.append(
            "Note: Exact AIR cannot be predicted because tie-breaking "
            "depends on subject-wise scores."
        )
        return " ".join(lines)


# ── Utility functions ──


def _enforce_decreasing(arr: np.ndarray) -> np.ndarray:
    """Enforce monotonically decreasing values (left to right = marks ascending).

    Higher marks (rightward) must map to lower percentile.
    Uses running minimum from right to left.
    """
    result = arr.copy()
    # Iterate from highest marks (right) to lowest (left)
    # pct at highest marks should be the minimum
    # Walk right to left: ensure result[i] >= result[i+1]
    for i in range(len(result) - 2, -1, -1):
        if result[i] < result[i + 1]:
            result[i] = result[i + 1]
    return result


def _interpolate_curve(
    marks: float, marks_points: np.ndarray, pct_values: np.ndarray
) -> float:
    """Interpolate percentile for given marks using piecewise linear.

    Handles extrapolation by clamping to boundary values.
    marks_points is sorted ascending; pct_values is decreasing.
    """
    if marks <= marks_points[0]:
        # Extrapolation below lowest anchor → worst percentile
        return float(pct_values[0])
    if marks >= marks_points[-1]:
        # Extrapolation above highest anchor → best percentile
        return float(pct_values[-1])

    # numpy interp: xp must be increasing (marks_points is ascending)
    # fp is the corresponding pct (decreasing)
    return float(np.interp(marks, marks_points, pct_values))


# ── Validation harness ──


def run_validation(
    estimator: RankEstimator | None = None,
    normalization: NormalizationMode | None = None,
) -> dict:
    """Run 2025 held-out validation.

    For each 2025 anchor, predict using 2020-2024 data only,
    then check if actual 2025 rank lies within predicted range.
    """
    if estimator is None:
        norm = normalization if normalization is not None else NormalizationMode.NONE
        estimator = RankEstimator(use_validation_data=False, normalization=norm)

    val_data = pd.read_csv(_MARKS_RANK_PATH)
    val_data = val_data[val_data["year"] == VALIDATION_YEAR]

    if val_data.empty:
        return {"error": "No 2025 validation data available"}

    # Get 2025 appeared candidates for proper scaling
    exam_years = pd.read_csv(_EXAM_YEARS_PATH)
    val_row = exam_years[exam_years["year"] == VALIDATION_YEAR]
    if val_row.empty:
        return {"error": "No 2025 exam_years entry"}
    val_appeared = int(val_row.iloc[0]["appeared_candidates"])

    results = []
    for _, row in val_data.iterrows():
        marks_mid = int((row["marks_min"] + row["marks_max"]) / 2)
        actual_rank_min = int(row["rank_min"])
        actual_rank_max = int(row["rank_max"])

        try:
            est = estimator.estimate(marks_mid, target_year=VALIDATION_YEAR)
        except (ValueError, Exception) as e:
            results.append({
                "marks": marks_mid,
                "error": str(e),
                "covered": False,
            })
            continue

        # Check if actual rank range overlaps with predicted range
        # "Covered" = actual rank lies within [best_case, conservative]
        covered = (
            est.best_case_air <= actual_rank_max
            and est.conservative_air >= actual_rank_min
        )

        # Error: distance from median prediction to actual midpoint
        actual_mid = (actual_rank_min + actual_rank_max) / 2
        abs_error = abs(est.median_air - actual_mid)
        pct_error = abs_error / actual_mid if actual_mid > 0 else 0

        results.append({
            "marks": marks_mid,
            "actual_rank_min": actual_rank_min,
            "actual_rank_max": actual_rank_max,
            "actual_mid": actual_mid,
            "predicted_best": est.best_case_air,
            "predicted_median": est.median_air,
            "predicted_conservative": est.conservative_air,
            "covered": covered,
            "abs_error": abs_error,
            "pct_error": pct_error,
            "confidence": est.confidence,
        })

    # Compute metrics
    valid_results = [r for r in results if "error" not in r]
    n = len(valid_results)
    if n == 0:
        return {"error": "No valid predictions", "results": results}

    coverage_rate = sum(1 for r in valid_results if r["covered"]) / n
    abs_errors = [r["abs_error"] for r in valid_results]
    pct_errors = [r["pct_error"] for r in valid_results]

    return {
        "n_validation_points": n,
        "coverage_rate": coverage_rate,
        "median_absolute_error": float(np.median(abs_errors)),
        "mean_absolute_error": float(np.mean(abs_errors)),
        "within_10_percent_band": sum(
            1 for e in pct_errors if e <= 0.10
        ) / n,
        "within_20_percent_band": sum(
            1 for e in pct_errors if e <= 0.20
        ) / n,
        "results": valid_results,
        "target": "coverage_rate >= 0.70",
        "pass": coverage_rate >= 0.70,
    }


def compare_normalization_strategies() -> dict[str, dict]:
    """Run validation with each normalization strategy and return comparison.

    Returns a dict keyed by strategy name with full validation results.
    Also adds ``high_marks_coverage`` (marks >= 550) and
    ``low_mid_marks_coverage`` (marks < 550) sub-metrics.
    """
    comparison: dict[str, dict] = {}
    for mode in NormalizationMode:
        result = run_validation(normalization=mode)
        # Add high/low-mid split
        valid = result.get("results", [])
        high = [r for r in valid if r["marks"] >= 550]
        low_mid = [r for r in valid if r["marks"] < 550]
        result["high_marks_coverage"] = (
            sum(1 for r in high if r["covered"]) / len(high)
            if high else 0.0
        )
        result["low_mid_marks_coverage"] = (
            sum(1 for r in low_mid if r["covered"]) / len(low_mid)
            if low_mid else 0.0
        )
        comparison[mode.value] = result
    return comparison
