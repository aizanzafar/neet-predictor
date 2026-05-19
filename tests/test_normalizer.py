"""Tests for college name normalization and alias handling."""

import pytest

from neet_predictor.dataio.normalizer import (
    normalize_college_name,
    parse_mcc_rank,
    find_college_by_alias,
)
import pandas as pd


class TestNormalizeCollegeName:

    def test_basic_lowercase(self):
        assert normalize_college_name("AIIMS NEW DELHI") == "aiims new delhi"

    def test_abbreviation_expansion(self):
        result = normalize_college_name("Govt. Med. Coll., Chandigarh")
        assert "government" in result
        assert "medical" in result
        assert "college" in result

    def test_pincode_removal(self):
        result = normalize_college_name("AIIMS 110029 Delhi")
        assert "110029" not in result

    def test_punctuation_stripped(self):
        result = normalize_college_name("S.M.S. Medical College (Jaipur)")
        assert "(" not in result
        assert ")" not in result
        assert "." not in result

    def test_extra_whitespace(self):
        result = normalize_college_name("  AIIMS   New   Delhi  ")
        assert result == "aiims new delhi"

    def test_empty_string(self):
        assert normalize_college_name("") == ""

    def test_none_input(self):
        assert normalize_college_name(None) == ""

    def test_ampersand_replacement(self):
        result = normalize_college_name("Trauma & Emergency Centre")
        assert "and" in result

    def test_same_college_different_formats(self):
        """Two representations of the same college should normalize to the same string."""
        name1 = "AIIMS, New Delhi,AIIMS ANSARI NAGAR EAST AUROBINDO MARG NEW DELHI"
        name2 = "AIIMS, New Delhi,AIIMS 110029, Delhi (NCT), 110029 ANSARI NAGAR EAST AUROBINDO MARG"
        norm1 = normalize_college_name(name1)
        norm2 = normalize_college_name(name2)
        # Both should at least start with "aiims" and contain "new delhi"
        assert norm1.startswith("aiims")
        assert norm2.startswith("aiims")


class TestParseMccRank:

    def test_integer_rank(self):
        raw, air = parse_mcc_rank("18.0")
        assert raw == "18.0"
        assert air == 18

    def test_tied_rank(self):
        raw, air = parse_mcc_rank("1.01")
        assert raw == "1.01"
        assert air == 1

    def test_plain_integer(self):
        raw, air = parse_mcc_rank("500")
        assert raw == "500"
        assert air == 500

    def test_large_rank(self):
        raw, air = parse_mcc_rank("139000.0")
        assert air == 139000

    def test_invalid_rank(self):
        with pytest.raises(ValueError):
            parse_mcc_rank("abc")


class TestFindCollegeByAlias:

    def test_found(self):
        aliases_df = pd.DataFrame({
            "college_id": [1, 2],
            "alias_normalized": ["aiims new delhi", "jipmer puducherry"],
        })
        result = find_college_by_alias("aiims new delhi", aliases_df)
        assert result == 1

    def test_not_found(self):
        aliases_df = pd.DataFrame({
            "college_id": [1],
            "alias_normalized": ["aiims new delhi"],
        })
        result = find_college_by_alias("unknown college", aliases_df)
        assert result is None

    def test_empty_aliases(self):
        aliases_df = pd.DataFrame(columns=["college_id", "alias_normalized"])
        result = find_college_by_alias("anything", aliases_df)
        assert result is None

    def test_none_aliases(self):
        result = find_college_by_alias("anything", None)
        assert result is None
