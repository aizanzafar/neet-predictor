"""Tests for counsellor.llm_client — HTTP client infrastructure."""

import pytest
from unittest.mock import patch, MagicMock

from neet_predictor.counsellor.llm_client import LLMClient, LLMClientError, LLMResponse


class TestLLMClientInit:

    def test_missing_api_key_raises(self):
        """Client raises if no API key available."""
        with patch.dict("os.environ", {}, clear=True):
            with pytest.raises(LLMClientError, match="SIEMENS_API_KEY"):
                LLMClient(api_key="", endpoint="http://test")

    def test_explicit_api_key(self):
        """Client accepts explicit API key."""
        client = LLMClient(api_key="test-key", endpoint="http://test")
        assert client._api_key == "test-key"

    def test_model_properties(self):
        """Model properties return env values or defaults."""
        with patch.dict("os.environ", {
            "LLM_MODEL_PRIMARY": "test-model",
            "LLM_MODEL_NARRATIVE": "narrative-model",
            "LLM_MODEL_FALLBACK": "fallback-model",
        }):
            client = LLMClient(api_key="key", endpoint="http://test")
            assert client.primary_model == "test-model"
            assert client.narrative_model == "narrative-model"
            assert client.fallback_model == "fallback-model"


class TestLLMClientChat:

    @patch("neet_predictor.counsellor.llm_client.httpx.Client")
    def test_successful_call(self, mock_client_cls):
        """Successful API call returns LLMResponse."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Hello"}}],
            "usage": {"total_tokens": 50},
        }
        mock_response.raise_for_status = MagicMock()

        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client.post.return_value = mock_response
        mock_client_cls.return_value = mock_client

        client = LLMClient(api_key="test-key", endpoint="http://test/v1/chat")
        result = client.chat(system="sys", user="hi")

        assert isinstance(result, LLMResponse)
        assert result.content == "Hello"
        assert result.tokens_used == 50
        assert result.model is not None

    @patch("neet_predictor.counsellor.llm_client.httpx.Client")
    def test_client_error_no_retry(self, mock_client_cls):
        """4xx errors (except 429) don't retry."""
        import httpx

        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.text = "Bad request"
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Bad", request=MagicMock(), response=mock_response
        )

        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client.post.return_value = mock_response
        mock_client_cls.return_value = mock_client

        client = LLMClient(api_key="test-key", endpoint="http://test/v1/chat")
        with pytest.raises(LLMClientError, match="API error 400"):
            client.chat(system="sys", user="hi")


class TestLLMClientChatJSON:

    @patch("neet_predictor.counsellor.llm_client.httpx.Client")
    def test_json_parsing(self, mock_client_cls):
        """chat_json parses JSON response."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": '{"marks": 550, "category": "OBC"}'}}],
            "usage": {"total_tokens": 30},
        }
        mock_response.raise_for_status = MagicMock()

        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client.post.return_value = mock_response
        mock_client_cls.return_value = mock_client

        client = LLMClient(api_key="test-key", endpoint="http://test/v1/chat")
        result = client.chat_json(system="sys", user="hi")

        assert result == {"marks": 550, "category": "OBC"}

    @patch("neet_predictor.counsellor.llm_client.httpx.Client")
    def test_json_strips_markdown_fences(self, mock_client_cls):
        """chat_json strips ```json fences."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": '```json\n{"marks": 600}\n```'}}],
            "usage": {"total_tokens": 20},
        }
        mock_response.raise_for_status = MagicMock()

        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client.post.return_value = mock_response
        mock_client_cls.return_value = mock_client

        client = LLMClient(api_key="test-key", endpoint="http://test/v1/chat")
        result = client.chat_json(system="sys", user="hi")

        assert result == {"marks": 600}

    @patch("neet_predictor.counsellor.llm_client.httpx.Client")
    def test_invalid_json_raises(self, mock_client_cls):
        """Invalid JSON response raises LLMClientError."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Not valid JSON at all"}}],
            "usage": {"total_tokens": 10},
        }
        mock_response.raise_for_status = MagicMock()

        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client.post.return_value = mock_response
        mock_client_cls.return_value = mock_client

        client = LLMClient(api_key="test-key", endpoint="http://test/v1/chat")
        with pytest.raises(LLMClientError, match="not valid JSON"):
            client.chat_json(system="sys", user="hi")
