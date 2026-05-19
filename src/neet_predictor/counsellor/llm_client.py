"""LLM client — model-agnostic HTTP client for Siemens API.

Handles retries, model routing, and response parsing.
No domain logic — pure infrastructure.
"""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass
from typing import Any

import httpx
from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class LLMResponse:
    """Response from an LLM call."""

    content: str
    model: str
    tokens_used: int
    latency_ms: float
    raw: dict[str, Any]


class LLMClientError(Exception):
    """Raised when LLM call fails after retries."""

    pass


class LLMClient:
    """HTTP client for Siemens LLM API with retry and model fallback."""

    def __init__(
        self,
        *,
        api_key: str | None = None,
        endpoint: str | None = None,
        timeout: float = 30.0,
        max_retries: int = 2,
    ):
        self._api_key = api_key or os.getenv("SIEMENS_API_KEY", "")
        self._endpoint = endpoint or os.getenv(
            "SIEMENS_API_ENDPOINT", "https://api.siemens.ai/v1/chat/completions"
        )
        self._timeout = timeout
        self._max_retries = max_retries

        if not self._api_key:
            raise LLMClientError("SIEMENS_API_KEY not set in environment or .env")

    def chat(
        self,
        *,
        system: str,
        user: str,
        model: str | None = None,
        temperature: float = 0.3,
        max_tokens: int = 2048,
    ) -> LLMResponse:
        """Send a chat completion request.

        Args:
            system: System prompt
            user: User prompt
            model: Model name (defaults to LLM_MODEL_PRIMARY from env)
            temperature: Sampling temperature
            max_tokens: Max output tokens

        Returns:
            LLMResponse with content and metadata

        Raises:
            LLMClientError: If all retries fail
        """
        if model is None:
            model = os.getenv("LLM_MODEL_PRIMARY", "deepseek-v4-flash")

        messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ]

        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }

        last_error: Exception | None = None

        for attempt in range(self._max_retries + 1):
            try:
                start = time.perf_counter()
                with httpx.Client(timeout=self._timeout) as client:
                    response = client.post(
                        self._endpoint,
                        json=payload,
                        headers=headers,
                    )
                latency_ms = (time.perf_counter() - start) * 1000

                if response.status_code == 429:
                    # Rate limited — wait and retry
                    wait = min(2 ** attempt, 8)
                    time.sleep(wait)
                    last_error = LLMClientError(f"Rate limited (429) on attempt {attempt + 1}")
                    continue

                if response.status_code >= 500:
                    # Server error — retry
                    wait = min(2 ** attempt, 8)
                    time.sleep(wait)
                    last_error = LLMClientError(
                        f"Server error ({response.status_code}) on attempt {attempt + 1}"
                    )
                    continue

                response.raise_for_status()
                data = response.json()

                content = data["choices"][0]["message"]["content"]
                tokens = data.get("usage", {}).get("total_tokens", 0)

                return LLMResponse(
                    content=content,
                    model=model,
                    tokens_used=tokens,
                    latency_ms=latency_ms,
                    raw=data,
                )

            except httpx.TimeoutException as e:
                last_error = e
                continue
            except httpx.HTTPStatusError as e:
                last_error = e
                if e.response.status_code < 500:
                    # Client error — don't retry
                    raise LLMClientError(
                        f"API error {e.response.status_code}: {e.response.text}"
                    ) from e
                continue
            except (json.JSONDecodeError, KeyError) as e:
                raise LLMClientError(f"Malformed API response: {e}") from e

        raise LLMClientError(
            f"All {self._max_retries + 1} attempts failed. Last error: {last_error}"
        )

    def chat_json(
        self,
        *,
        system: str,
        user: str,
        model: str | None = None,
        temperature: float = 0.1,
        max_tokens: int = 1024,
    ) -> dict[str, Any]:
        """Chat and parse response as JSON.

        Strips markdown fences if present. Raises LLMClientError if
        response is not valid JSON.
        """
        resp = self.chat(
            system=system,
            user=user,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
        )

        text = resp.content.strip()
        # Strip markdown code fences
        if text.startswith("```"):
            lines = text.split("\n")
            # Remove first and last line (fences)
            lines = [l for l in lines[1:] if not l.strip().startswith("```")]
            text = "\n".join(lines)

        try:
            parsed = json.loads(text)
        except json.JSONDecodeError as e:
            raise LLMClientError(
                f"LLM response is not valid JSON: {e}\nRaw: {resp.content[:500]}"
            ) from e

        return parsed

    @property
    def primary_model(self) -> str:
        return os.getenv("LLM_MODEL_PRIMARY", "deepseek-v4-flash")

    @property
    def narrative_model(self) -> str:
        return os.getenv("LLM_MODEL_NARRATIVE", "gpt-oss-120b")

    @property
    def fallback_model(self) -> str:
        return os.getenv("LLM_MODEL_FALLBACK", "qwen-3.6-27b")
