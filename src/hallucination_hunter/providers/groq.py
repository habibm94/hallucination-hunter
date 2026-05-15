"""Groq provider adapter for Hallucination Hunter.

Uses the OpenAI-compatible API at https://api.groq.com/openai/v1.
Groq offers generous free-tier rate limits (30 req/min, 14,400/day).
Sign up at https://console.groq.com — no credit card required.
"""

from __future__ import annotations

import time

import openai as _openai

from hallucination_hunter.providers.base import (
    AuthenticationError,
    LLMProvider,
    ProviderError,
    RateLimitError,
)

GROQ_MODELS: dict[str, str] = {
    "llama-3.3-70b-versatile": "Llama 3.3 70B · free tier",
    "llama3-70b-8192": "Llama 3 70B · free tier",
}
DEFAULT_GROQ_MODEL = "llama-3.3-70b-versatile"

_GROQ_BASE_URL = "https://api.groq.com/openai/v1"


class GroqProvider(LLMProvider):
    """LLM provider backed by the Groq inference API."""

    def __init__(self, api_key: str, model: str = DEFAULT_GROQ_MODEL) -> None:
        super().__init__(api_key=api_key, model=model)
        self._client = _openai.OpenAI(api_key=api_key, base_url=_GROQ_BASE_URL)

    @property
    def name(self) -> str:
        return "groq"

    def call(self, prompt: str) -> str:
        for attempt in range(3):
            try:
                response = self._client.chat.completions.create(
                    model=self.model,
                    temperature=0.0,
                    response_format={"type": "json_object"},
                    messages=[{"role": "user", "content": prompt}],
                )
                time.sleep(0.3)
                return response.choices[0].message.content
            except _openai.AuthenticationError as exc:
                raise AuthenticationError(
                    "Groq authentication failed. Check your API key."
                ) from exc
            except _openai.RateLimitError as exc:
                if attempt < 2:
                    time.sleep((2 ** attempt) * 5)
                    continue
                raise RateLimitError("Groq rate limit persisted.") from exc
            except Exception as exc:
                raise ProviderError(f"Groq call failed: {exc}") from exc
        raise ProviderError("Unexpected exit.")

