"""Tests for counsellor.prompts — static templates."""

import pytest

from neet_predictor.counsellor.prompts import (
    INTENT_PARSER_SYSTEM,
    REASONER_SYSTEM,
    format_intent_user_prompt,
    format_reasoner_system_prompt,
    format_reasoner_user_prompt,
)


class TestIntentParserPrompt:

    def test_system_contains_slot_definitions(self):
        """System prompt defines all extractable slots."""
        assert "marks" in INTENT_PARSER_SYSTEM
        assert "actual_air" in INTENT_PARSER_SYSTEM
        assert "national_category" in INTENT_PARSER_SYSTEM
        assert "home_state" in INTENT_PARSER_SYSTEM
        assert "karnataka_interest" in INTENT_PARSER_SYSTEM

    def test_system_requires_json_output(self):
        """System prompt requires JSON output."""
        assert "JSON" in INTENT_PARSER_SYSTEM

    def test_user_prompt_includes_query(self):
        """User prompt formats the query."""
        result = format_intent_user_prompt("I scored 550 marks")
        assert "I scored 550 marks" in result

    def test_system_has_rules(self):
        """System prompt has rules section."""
        assert "Rules" in INTENT_PARSER_SYSTEM or "NEVER" in INTENT_PARSER_SYSTEM


class TestReasonerPrompt:

    def test_system_contains_critical_rules(self):
        """Reasoner system prompt has all safety rules."""
        assert "NEVER invent college names" in REASONER_SYSTEM
        assert "NEVER upgrade chance labels" in REASONER_SYSTEM
        assert "NEVER use probability percentages" in REASONER_SYSTEM
        assert "guaranteed" in REASONER_SYSTEM.lower()
        assert "disclaimer" in REASONER_SYSTEM.lower()

    def test_system_has_knowledge_placeholder(self):
        """System prompt has knowledge_context placeholder."""
        assert "{knowledge_context}" in REASONER_SYSTEM

    def test_format_system_with_context(self):
        """format_reasoner_system_prompt injects knowledge."""
        ctx = "• OBC ranks are 1.3-1.8x General."
        result = format_reasoner_system_prompt(ctx)
        assert "OBC ranks are 1.3-1.8x" in result
        assert "{knowledge_context}" not in result

    def test_user_prompt_has_placeholders(self):
        """User prompt formats all sections."""
        result = format_reasoner_user_prompt(
            profile_summary="Marks: 550, OBC",
            scenario_data="### Primary\nSafe: 3, Likely: 5",
            comparison_notes="Best: Primary",
        )
        assert "Marks: 550" in result
        assert "Primary" in result
        assert "Best: Primary" in result

    def test_response_structure_defined(self):
        """System prompt defines expected response structure."""
        assert "Summary" in REASONER_SYSTEM
        assert "Top Recommendations" in REASONER_SYSTEM
        assert "Backup Options" in REASONER_SYSTEM
        assert "Risk Areas" in REASONER_SYSTEM
