"""Tests for counsellor.orchestrator — end-to-end pipeline (mocked LLM)."""

import pytest
from unittest.mock import patch, MagicMock

from neet_predictor.counsellor.models import (
    ClarificationNeeded,
    StudentIntent,
    ValidatedResponse,
)
from neet_predictor.counsellor.orchestrator import run_counsellor, run_counsellor_with_intent
from neet_predictor.counsellor.llm_client import LLMClient, LLMResponse


def _make_intent(**overrides):
    defaults = dict(
        marks=550,
        actual_air=None,
        national_category="OBC",
        home_state="Bihar",
        pwd=False,
        karnataka_interest=False,
        karnataka_domicile=None,
        karnataka_category=None,
        course_pref="MBBS",
        college_type_pref="any",
        bds_backup=False,
        target_year=None,
        missing_slots=(),
        uncertain_slots=(),
        ambiguity_notes=(),
        raw_query="test query",
    )
    defaults.update(overrides)
    return StudentIntent(**defaults)


def _mock_client():
    """Create a mock LLMClient for orchestrator tests."""
    client = MagicMock(spec=LLMClient)
    client.primary_model = "deepseek-v4-flash"
    client.narrative_model = "gpt-oss-120b"
    client.fallback_model = "qwen-3.6-27b"

    # Intent parser JSON response
    client.chat_json.return_value = {
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
    }

    # Reasoner narrative response
    client.chat.return_value = LLMResponse(
        content=(
            "### Summary\n"
            "You have good chances at several colleges.\n\n"
            "### Top Recommendations\n"
            "Consider government medical colleges in your estimated rank range.\n\n"
            "### Backup Options\n"
            "Deemed universities are also viable.\n\n"
            "### Risk Areas\n"
            "- Marks-to-rank conversion has uncertainty.\n\n"
            "### Important Notes\n"
            "- This is not an admission guarantee. Verify from official sources.\n"
            "- Rank is estimated/experimental."
        ),
        model="gpt-oss-120b",
        tokens_used=800,
        latency_ms=1500.0,
        raw={},
    )
    return client


class TestRunCounsellor:

    def test_full_pipeline_returns_validated_response(self):
        """Full pipeline with mocked LLM returns ValidatedResponse."""
        client = _mock_client()
        result = run_counsellor("550 marks OBC Bihar", client=client)
        assert isinstance(result, ValidatedResponse)
        assert result.scenarios is not None
        assert len(result.limitations) > 0

    def test_pipeline_calls_intent_parser(self):
        """Pipeline calls chat_json for intent parsing."""
        client = _mock_client()
        run_counsellor("test query", client=client)
        client.chat_json.assert_called_once()

    def test_pipeline_calls_reasoner(self):
        """Pipeline calls chat for narrative generation."""
        client = _mock_client()
        run_counsellor("test query", client=client)
        client.chat.assert_called_once()

    def test_processing_time_recorded(self):
        """Processing time is non-zero."""
        client = _mock_client()
        result = run_counsellor("test query", client=client)
        assert isinstance(result, ValidatedResponse)
        assert result.processing_time_ms > 0


class TestRunCounsellorWithIntent:

    def test_skips_intent_parser(self):
        """run_counsellor_with_intent doesn't call chat_json."""
        client = _mock_client()
        intent = _make_intent()
        result = run_counsellor_with_intent(intent, client=client)
        # Should NOT call intent parser
        client.chat_json.assert_not_called()
        # Should call reasoner
        client.chat.assert_called_once()
        assert isinstance(result, ValidatedResponse)

    def test_clarification_if_missing_slots(self):
        """Returns ClarificationNeeded if critical slots missing."""
        client = _mock_client()
        intent = _make_intent(marks=None, actual_air=None)
        result = run_counsellor_with_intent(intent, client=client)
        assert isinstance(result, ClarificationNeeded)

    def test_valid_intent_returns_response(self):
        """Valid intent produces full response."""
        client = _mock_client()
        intent = _make_intent(marks=550, national_category="OBC")
        result = run_counsellor_with_intent(intent, client=client)
        assert isinstance(result, ValidatedResponse)
        assert result.scenarios is not None
        assert len(result.scenarios.comparison_table) >= 1


class TestClarificationFlow:

    def test_missing_category_returns_clarification(self):
        """Missing category triggers clarification in full pipeline."""
        client = MagicMock(spec=LLMClient)
        client.primary_model = "deepseek-v4-flash"
        client.chat_json.return_value = {
            "marks": 550,
            "actual_air": None,
            "national_category": None,  # Missing!
            "home_state": "Bihar",
            "karnataka_interest": None,
            "karnataka_domicile": None,
            "karnataka_category": None,
            "course_pref": None,
            "college_type_pref": None,
            "ambiguities": [],
        }
        result = run_counsellor("550 marks from Bihar", client=client)
        assert isinstance(result, ClarificationNeeded)
        assert any("category" in q.lower() for q in result.questions)
        # Reasoner should NOT be called
        client.chat.assert_not_called()
