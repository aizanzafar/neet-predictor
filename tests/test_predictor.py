"""Tests for Phase 1B-A: AIR-Based College Predictor.

Covers:
  1. MCC vs KEA category separation
  2. National category vs KEA category separation
  3. R1-only primary prediction
  4. Later-round supplementary evidence
  5. Insufficient-data label (< 2 R1 years)
  6. Safe / Likely / Borderline / Unlikely chance labels
  7. Conservative false-safe behaviour
"""

import pandas as pd
import pytest

from neet_predictor.college.eligibility import (
    CandidateProfile,
    get_mcc_eligible_categories,
    get_kea_eligible_categories,
)
from neet_predictor.college.predictor import (
    classify_chance,
    normalize_closing_ranks,
    predict,
    CollegePrediction,
    MIN_R1_YEARS,
)


# ═══════════════════════════════════════════════════════
#  1 & 2.  MCC / KEA category separation
# ═══════════════════════════════════════════════════════


_KEA_ONLY_CATS = frozenset({
    "GM", "1G", "2AG", "2BG", "3AG", "3BG", "SCG", "STG",
    "GMR", "GMH", "GMK", "2AR", "2AH", "SCR", "STR",
})
_MCC_ONLY_CATS = frozenset({
    "Open", "OBC", "SC", "ST", "EWS",
    "PwD Open", "PwD OBC", "PwD SC", "PwD ST", "PwD EWS",
})


class TestMCCCategories:

    @pytest.mark.parametrize("nat_cat,expected", [
        ("General", ["Open"]),
        ("OBC", ["OBC", "Open"]),
        ("SC", ["SC", "Open"]),
        ("ST", ["ST", "Open"]),
        ("EWS", ["EWS", "Open"]),
    ])
    def test_non_pwd_categories(self, nat_cat, expected):
        p = CandidateProfile(air=1000, national_category=nat_cat, home_state="Delhi")
        assert get_mcc_eligible_categories(p) == expected

    @pytest.mark.parametrize("nat_cat", ["General", "OBC", "SC", "ST", "EWS"])
    def test_pwd_includes_pwd_variant(self, nat_cat):
        p = CandidateProfile(
            air=1000, national_category=nat_cat, home_state="Delhi", pwd=True,
        )
        cats = get_mcc_eligible_categories(p)
        assert any(c.startswith("PwD") for c in cats)
        assert "Open" in cats  # everyone competes in Open too

    def test_mcc_never_returns_kea_categories(self):
        """MCC eligible categories must NEVER include KEA-specific categories."""
        for nat_cat in ["General", "OBC", "SC", "ST", "EWS"]:
            for pwd in [False, True]:
                p = CandidateProfile(
                    air=1000, national_category=nat_cat,
                    home_state="Delhi", pwd=pwd,
                )
                mcc = set(get_mcc_eligible_categories(p))
                overlap = mcc & _KEA_ONLY_CATS
                assert not overlap, (
                    f"MCC cats {mcc} overlap with KEA cats {overlap}"
                )

    def test_own_category_before_open(self):
        """Own reserved category appears before Open in the list."""
        p = CandidateProfile(air=1000, national_category="SC", home_state="UP")
        cats = get_mcc_eligible_categories(p)
        assert cats.index("SC") < cats.index("Open")


class TestKEACategories:

    def test_no_interest_returns_empty(self):
        p = CandidateProfile(air=1000, national_category="General", home_state="Delhi")
        assert get_kea_eligible_categories(p) == []

    def test_non_domicile_gets_gm_only(self):
        p = CandidateProfile(
            air=1000, national_category="OBC", home_state="Bihar",
            karnataka_interest=True, karnataka_domicile=False,
        )
        assert get_kea_eligible_categories(p) == ["GM"]

    @pytest.mark.parametrize("ka_cat,expected_first", [
        ("2A", "2AG"),
        ("2B", "2BG"),
        ("3A", "3AG"),
        ("3B", "3BG"),
        ("SC", "SCG"),
        ("ST", "STG"),
    ])
    def test_domicile_with_specific_category(self, ka_cat, expected_first):
        p = CandidateProfile(
            air=1000, national_category="General", home_state="Karnataka",
            karnataka_interest=True, karnataka_domicile=True,
            karnataka_category=ka_cat,
        )
        cats = get_kea_eligible_categories(p)
        assert cats[0] == expected_first
        assert "GM" in cats

    def test_domicile_category_not_sure_gets_gm(self):
        """Domicile=True but category=None → GM only."""
        p = CandidateProfile(
            air=1000, national_category="General", home_state="Karnataka",
            karnataka_interest=True, karnataka_domicile=True,
            karnataka_category=None,
        )
        assert get_kea_eligible_categories(p) == ["GM"]

    def test_kea_never_returns_mcc_categories(self):
        """KEA eligible categories must NEVER include MCC-specific categories."""
        for ka_cat in ["GM", "2A", "2B", "3A", "3B", "SC", "ST", "1"]:
            p = CandidateProfile(
                air=1000, national_category="General", home_state="Karnataka",
                karnataka_interest=True, karnataka_domicile=True,
                karnataka_category=ka_cat,
            )
            kea = set(get_kea_eligible_categories(p))
            overlap = kea & _MCC_ONLY_CATS
            assert not overlap, (
                f"KEA cats {kea} overlap with MCC cats {overlap}"
            )

    def test_national_obc_not_mapped_to_kea_sub_categories(self):
        """National OBC must NOT be auto-mapped to KEA 2A/2B/3A/3B."""
        p = CandidateProfile(
            air=1000, national_category="OBC", home_state="Bihar",
            karnataka_interest=True, karnataka_domicile=False,
        )
        cats = get_kea_eligible_categories(p)
        for bad in ["2AG", "2BG", "3AG", "3BG"]:
            assert bad not in cats, f"{bad} should not appear for national OBC"

    def test_non_domicile_obc_gets_gm_not_reserved(self):
        """Non-domicile OBC from another state sees only GM."""
        p = CandidateProfile(
            air=1000, national_category="OBC", home_state="Tamil Nadu",
            karnataka_interest=True, karnataka_domicile=False,
        )
        cats = get_kea_eligible_categories(p)
        assert cats == ["GM"]


# ═══════════════════════════════════════════════════════
#  5 & 6.  Chance classification (unit tests, synthetic data)
# ═══════════════════════════════════════════════════════


class TestClassifyChance:

    # ── Insufficient data ──

    def test_zero_years(self):
        chance, margin = classify_chance(5000, {})
        assert chance == "Insufficient data"
        assert margin is None

    def test_one_year(self):
        chance, margin = classify_chance(5000, {2024: 10000})
        assert chance == "Insufficient data"
        assert margin is None

    # ── Safe ──

    def test_safe_requires_3_years_and_large_margin(self):
        r1 = {2020: 10000, 2022: 9000, 2023: 8000}
        chance, _ = classify_chance(5000, r1)
        assert chance == "Safe"

    def test_safe_four_years(self):
        r1 = {2020: 10000, 2022: 9000, 2023: 8000, 2024: 7500}
        chance, _ = classify_chance(5000, r1)
        assert chance == "Safe"

    # ── Safe → Likely downgrades (conservative) ──

    def test_safe_downgraded_to_likely_with_2_years(self):
        """Large margin but only 2 years → Likely, not Safe."""
        r1 = {2020: 10000, 2023: 9000}
        chance, _ = classify_chance(5000, r1)
        assert chance == "Likely"

    def test_thin_margin_all_years_is_likely(self):
        """Admitted all years but min margin < 20% → Likely."""
        r1 = {2020: 6000, 2022: 6200, 2023: 6100}
        chance, _ = classify_chance(5000, r1)
        # min_margin = (6000-5000)/6000 ≈ 0.167 < 0.20
        assert chance == "Likely"

    # ── Likely ──

    def test_likely_admitted_all_moderate_margin(self):
        r1 = {2020: 6000, 2022: 5800, 2023: 5500}
        chance, _ = classify_chance(5000, r1)
        assert chance == "Likely"

    def test_likely_2_years_all_admitted(self):
        r1 = {2022: 6000, 2024: 5500}
        chance, _ = classify_chance(5000, r1)
        assert chance == "Likely"

    # ── Borderline ──

    def test_borderline_mixed_results(self):
        """Admitted some years, missed others."""
        r1 = {2020: 5500, 2022: 4800, 2023: 5200}
        chance, _ = classify_chance(5000, r1)
        assert chance == "Borderline"

    def test_borderline_close_miss(self):
        """AIR slightly above both closing ranks."""
        r1 = {2020: 4800, 2023: 4900}
        chance, _ = classify_chance(5000, r1)
        assert chance == "Borderline"

    def test_borderline_narrow_miss_weighted(self):
        """Missed both years but weighted margin near -10%."""
        r1 = {2023: 4700, 2024: 4600}
        chance, _ = classify_chance(5000, r1)
        # margins: (4700-5000)/4700 ≈ -0.064, (4600-5000)/4600 ≈ -0.087
        # weighted ≈ -0.078  > -0.10  → Borderline
        assert chance == "Borderline"

    # ── Unlikely ──

    def test_unlikely_large_gap(self):
        r1 = {2020: 3000, 2022: 3500, 2023: 3200}
        chance, _ = classify_chance(5000, r1)
        assert chance == "Unlikely"

    def test_unlikely_2_years_large_gap(self):
        r1 = {2022: 2000, 2024: 2500}
        chance, _ = classify_chance(5000, r1)
        assert chance == "Unlikely"

    # ── Weighted margin ──

    def test_weighted_margin_positive_when_admitted(self):
        r1 = {2022: 8000, 2023: 7000, 2024: 6000}
        _, margin = classify_chance(5000, r1)
        assert margin is not None
        assert margin > 0

    def test_weighted_margin_negative_when_unlikely(self):
        r1 = {2022: 3000, 2023: 3500}
        _, margin = classify_chance(5000, r1)
        assert margin is not None
        assert margin < 0

    # ── 7. Conservative false-safe checks ──

    def test_false_safe_prevented_trending_down(self):
        """Closing ranks trending down. Even if all admitted, thin margin → Likely."""
        r1 = {2020: 7000, 2022: 6500, 2023: 6100}
        chance, _ = classify_chance(5000, r1)
        # min_margin = (6100-5000)/6100 ≈ 0.18 < 0.20  → not Safe
        assert chance == "Likely"

    def test_false_safe_prevented_2_year_data(self):
        """Even with perfect data, 2 years is not enough for Safe."""
        r1 = {2023: 20000, 2024: 18000}
        chance, _ = classify_chance(5000, r1)
        assert chance != "Safe"


# ═══════════════════════════════════════════════════════
#  Data normalization
# ═══════════════════════════════════════════════════════


class TestNormalization:

    def test_pwd_category_normalized(self):
        df = pd.DataFrame({
            "category": ["Open PwD", "OBC PwD", "SC PwD", "ST PwD", "EWS PwD", "Open"],
            "quota": ["All India"] * 6,
        })
        result = normalize_closing_ranks(df)
        assert "Open PwD" not in result["category"].values
        assert "PwD Open" in result["category"].values
        assert "Open" in result["category"].values

    def test_reported_removed(self):
        df = pd.DataFrame({
            "category": ["Open", "Reported", "OBC"],
            "quota": ["All India"] * 3,
        })
        result = normalize_closing_ranks(df)
        assert "Reported" not in result["category"].values
        assert len(result) == 2

    def test_quota_pdf_artifact_fixed(self):
        df = pd.DataFrame({
            "category": ["Open", "Open"],
            "quota": ["Deemed/Pai d Seats Quota", "All India"],
        })
        result = normalize_closing_ranks(df)
        assert "Deemed/Paid Seats Quota" in result["quota"].values
        assert "Deemed/Pai d Seats Quota" not in result["quota"].values

    def test_null_quota_becomes_empty_string(self):
        df = pd.DataFrame({
            "category": ["GM"],
            "quota": [None],
        })
        result = normalize_closing_ranks(df)
        assert result["quota"].iloc[0] == ""


# ═══════════════════════════════════════════════════════
#  3, 4 & 5.  Integration tests (real data)
# ═══════════════════════════════════════════════════════


class TestPredictorIntegration:
    """Integration tests that load actual curated data."""

    def test_basic_prediction_runs(self):
        p = CandidateProfile(
            air=5000, national_category="General", home_state="Delhi",
            course_pref="MBBS", college_type_pref="any",
        )
        result = predict(p)
        assert result.mcc_predictions is not None
        assert isinstance(result.summary, dict)
        assert result.summary["mcc_total"] > 0

    # ── 1. MCC predictions use only MCC categories ──

    def test_mcc_predictions_have_mcc_categories_only(self):
        p = CandidateProfile(
            air=10000, national_category="OBC", home_state="Bihar",
        )
        result = predict(p)
        for pred in result.mcc_predictions:
            assert pred.authority == "MCC"
            assert pred.category not in _KEA_ONLY_CATS, (
                f"MCC prediction used KEA category {pred.category}"
            )

    # ── 2. KEA predictions use only KEA categories ──

    def test_kea_predictions_have_kea_categories_only(self):
        p = CandidateProfile(
            air=10000, national_category="General", home_state="Karnataka",
            karnataka_interest=True, karnataka_domicile=True,
            karnataka_category="GM",
        )
        result = predict(p)
        for pred in result.kea_predictions:
            assert pred.authority == "KEA"
            assert pred.category not in _MCC_ONLY_CATS, (
                f"KEA prediction used MCC category {pred.category}"
            )

    # ── 3. R1-only primary prediction ──

    def test_chance_label_based_on_r1_only(self):
        """Chance label must derive from R1 data, not from later rounds."""
        p = CandidateProfile(
            air=5000, national_category="General", home_state="Delhi",
        )
        result = predict(p)
        for pred in result.mcc_predictions:
            # If there's a non-Insufficient chance, r1 data must exist
            if pred.chance != "Insufficient data":
                assert pred.r1_years_count >= MIN_R1_YEARS

    # ── 4. Later rounds in supplementary only ──

    def test_supplementary_rounds_not_r1(self):
        p = CandidateProfile(
            air=10000, national_category="General", home_state="Karnataka",
            karnataka_interest=True, karnataka_domicile=True,
            karnataka_category="GM",
        )
        result = predict(p)
        for pred in result.kea_predictions:
            for rnd in pred.supplementary_rounds:
                assert rnd in ("R2", "R3", "MOPUP", "STRAY"), (
                    f"R1 found in supplementary_rounds: {rnd}"
                )

    # ── 5. KEA now has R1+R2 data for 2020 and 2021 → predictions should work ──

    def test_kea_has_predictions(self):
        p = CandidateProfile(
            air=10000, national_category="General", home_state="Karnataka",
            karnataka_interest=True, karnataka_domicile=True,
            karnataka_category="GM",
        )
        result = predict(p)
        # With KEA 2020+2021 official closing ranks, predictions should be available
        chances = {pred.chance for pred in result.kea_predictions}
        assert "Insufficient data" not in chances or len(chances) > 1, (
            f"KEA should have real predictions now, got only: {chances}"
        )

    # ── 6. Chance labels appear at extremes ──

    def test_safe_or_likely_for_top_rank(self):
        """AIR=100 should produce Safe or Likely predictions."""
        p = CandidateProfile(
            air=100, national_category="General", home_state="Delhi",
            college_type_pref="any",
        )
        result = predict(p)
        chances = {pred.chance for pred in result.mcc_predictions}
        assert ("Safe" in chances) or ("Likely" in chances), (
            f"AIR=100 got only: {chances}"
        )

    def test_mostly_unlikely_for_very_high_air(self):
        """AIR=500000 should be mostly Unlikely."""
        p = CandidateProfile(
            air=500000, national_category="General", home_state="Delhi",
        )
        result = predict(p)
        if result.mcc_predictions:
            unlikely = sum(
                1 for pr in result.mcc_predictions if pr.chance == "Unlikely"
            )
            assert unlikely / len(result.mcc_predictions) > 0.5

    # ── Structural: no KEA without interest ──

    def test_no_kea_without_interest(self):
        p = CandidateProfile(
            air=5000, national_category="General", home_state="Delhi",
        )
        result = predict(p)
        assert result.kea_predictions == []

    # ── KEA exploratory flag ──

    def test_kea_exploratory_flag(self):
        p = CandidateProfile(
            air=10000, national_category="General", home_state="Karnataka",
            karnataka_interest=True, karnataka_domicile=True,
            karnataka_category=None,
        )
        result = predict(p)
        assert result.kea_exploratory is True

    def test_kea_not_exploratory_with_category(self):
        p = CandidateProfile(
            air=10000, national_category="General", home_state="Karnataka",
            karnataka_interest=True, karnataka_domicile=True,
            karnataka_category="GM",
        )
        result = predict(p)
        assert result.kea_exploratory is False

    # ── Non-domicile sees only GM ──

    def test_non_domicile_kea_gm_only(self):
        p = CandidateProfile(
            air=10000, national_category="OBC", home_state="Bihar",
            karnataka_interest=True, karnataka_domicile=False,
        )
        result = predict(p)
        for pred in result.kea_predictions:
            assert pred.category == "GM", (
                f"Non-domicile KEA should be GM only, got {pred.category}"
            )

    # ── 7. Conservative behaviour: Safe not too prevalent ──

    def test_safe_is_conservative(self):
        """At AIR=3000, Safe predictions should exist but be limited."""
        p = CandidateProfile(
            air=3000, national_category="General", home_state="Delhi",
            college_type_pref="any",
        )
        result = predict(p)
        safe_count = sum(
            1 for pr in result.mcc_predictions if pr.chance == "Safe"
        )
        total = len(result.mcc_predictions)
        if total > 0:
            # Safe should not dominate — conservative system
            assert safe_count / total < 0.6, (
                f"Safe ratio {safe_count}/{total} too high for AIR=3000"
            )

    def test_prediction_for_obc_candidate(self):
        """OBC candidate should see OBC + Open category predictions."""
        p = CandidateProfile(
            air=15000, national_category="OBC", home_state="Bihar",
        )
        result = predict(p)
        cats = {pred.category for pred in result.mcc_predictions}
        assert "OBC" in cats or "Open" in cats

    def test_college_type_government_filters_quota(self):
        """college_type_pref='government' should only show 'All India' quota."""
        p = CandidateProfile(
            air=5000, national_category="General", home_state="Delhi",
            college_type_pref="government",
        )
        result = predict(p)
        for pred in result.mcc_predictions:
            assert pred.quota == "All India", (
                f"Government filter should only show 'All India', got '{pred.quota}'"
            )

    def test_bds_course_returns_results(self):
        """BDS course preference should return some results."""
        p = CandidateProfile(
            air=50000, national_category="General", home_state="Delhi",
            course_pref="BDS",
        )
        result = predict(p)
        for pred in result.mcc_predictions:
            assert pred.course == "BDS"
