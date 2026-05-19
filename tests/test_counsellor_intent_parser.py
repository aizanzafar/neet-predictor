"""Tests for counsellor.intent_parser — LLM-based slot extraction."""

import pytest
from unittest.mock import patch, MagicMock

from neet_predictor.counsellor.intent_parser import parse_intent, _safe_int, _safe_str, _safe_bool
from neet_predictor.counsellor.llm_client import LLMClient
from neet_predictor.counsellor.models import StudentIntent


class TestParseIntent:

    def _mock_client(self, json_response: dict):
        """Create a mock LLMClient that returns given JSON."""
        client = MagicMock(spec=LLMClient)
        client.primary_model = "test-model"
        client.chat_json.return_value = json_response
        return client

    def test_full_extraction(self):
        """All slots extracted correctly."""
        client = self._mock_client({
            "marks": 550,
            "actual_air": None,
            "national_category": "OBC",
            "home_state": "Bihar",
            "karnataka_interest": False,
            "karnataka_domicile": None,
            "karnataka_category": None,
            "course_pref": "MBBS",
            "college_type_pref": "any",
            "confidence": 0.9,
            "ambiguities": [],
        })
        result = parse_intent("I scored 550, OBC from Bihar", client)
        assert isinstance(result, StudentIntent)
        assert result.marks == 550
        assert result.national_category == "OBC"
        assert result.home_state == "Bihar"
        assert result.course_pref == "MBBS"
        assert result.raw_query == "I scored 550, OBC from Bihar"

    def test_marks_only(self):
        """Only marks extracted."""
        client = self._mock_client({
            "marks": 600,
            "actual_air": None,
            "national_category": "General",
            "home_state": None,
            "karnataka_interest": None,
            "karnataka_domicile": None,
            "karnataka_category": None,
            "course_pref": None,
            "college_type_pref": None,
            "confidence": 0.7,
            "ambiguities": ["home_state unclear"],
        })
        result = parse_intent("600 marks general", client)
        assert result.marks == 600
        assert result.national_category == "General"
        assert result.home_state is None
        assert "home_state" in result.missing_slots

    def test_air_extraction(self):
        """AIR extracted when stated."""
        client = self._mock_client({
            "marks": None,
            "actual_air": 12000,
            "national_category": "SC",
            "home_state": "UP",
            "karnataka_interest": False,
            "karnataka_domicile": None,
            "karnataka_category": None,
            "course_pref": "MBBS+BDS",
            "college_type_pref": None,
            "ambiguities": [],
        })
        result = parse_intent("AIR 12000 SC from UP, want BDS too", client)
        assert result.actual_air == 12000
        assert result.marks is None
        assert result.bds_backup is True

    def test_karnataka_interest(self):
        """Karnataka interest detected."""
        client = self._mock_client({
            "marks": 520,
            "actual_air": None,
            "national_category": "OBC",
            "home_state": "Karnataka",
            "karnataka_interest": True,
            "karnataka_domicile": True,
            "karnataka_category": "2A",
            "course_pref": "MBBS",
            "college_type_pref": None,
            "ambiguities": [],
        })
        result = parse_intent("520 marks OBC Karnataka domicile 2A", client)
        assert result.karnataka_interest is True
        assert result.karnataka_domicile is True
        assert result.karnataka_category == "2A"

    def test_missing_critical_slots_flagged(self):
        """Missing marks+AIR and category flagged in missing_slots."""
        client = self._mock_client({
            "marks": None,
            "actual_air": None,
            "national_category": None,
            "home_state": "Delhi",
            "karnataka_interest": None,
            "karnataka_domicile": None,
            "karnataka_category": None,
            "course_pref": None,
            "college_type_pref": None,
            "ambiguities": ["what category?"],
        })
        result = parse_intent("What colleges in Delhi?", client)
        assert "marks_or_air" in result.missing_slots
        assert "national_category" in result.missing_slots

    def test_defaults_applied(self):
        """Null course_pref defaults to MBBS, college_type to any."""
        client = self._mock_client({
            "marks": 500,
            "actual_air": None,
            "national_category": "General",
            "home_state": None,
            "karnataka_interest": None,
            "karnataka_domicile": None,
            "karnataka_category": None,
            "course_pref": None,
            "college_type_pref": None,
            "ambiguities": [],
        })
        result = parse_intent("500 marks general", client)
        assert result.course_pref == "MBBS"
        assert result.college_type_pref == "any"


class TestSafeConversions:

    def test_safe_int(self):
        assert _safe_int(550) == 550
        assert _safe_int("550") == 550
        assert _safe_int(None) is None
        assert _safe_int("abc") is None
        assert _safe_int(550.7) == 550

    def test_safe_str(self):
        assert _safe_str("Bihar") == "Bihar"
        assert _safe_str(None) is None
        assert _safe_str("") is None
        assert _safe_str(123) == "123"

    def test_safe_bool(self):
        assert _safe_bool(True) is True
        assert _safe_bool(False) is False
        assert _safe_bool(None) is None
        assert _safe_bool("true") is True
        assert _safe_bool("false") is False
        assert _safe_bool(1) is True
