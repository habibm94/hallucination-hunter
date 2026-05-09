"""Grok (xAI) provider adapter for Hallucination Hunter.

Grok exposes an OpenAI-compatible API at https://api.x.ai/v1, so this
adapter re-uses the ``openai`` Python SDK with a custom ``base_url``.

xAI offers a free usage tier — sign up and manage keys at
https://console.x.ai
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

GROK_MODELS: dict[str, str] = {
    "grok-3-mini": "Fast · pay-per-use",
    "grok-3": "Powerful · pay-per-use",
}
DEFAULT_GROK_MODEL = "grok-3-mini"


class GrokProvider(LLMProvider):
    """LLM provider backed by the xAI Grok API (OpenAI-compatible)."""

    def __init__(self, api_key: str, model: str = DEFAULT_GROK_MODEL) -> None:
        """Initialise the Grok provider.

        Args:
            api_key: A valid xAI API key (obtain at https://console.x.ai).
            model: Model identifier. Defaults to ``grok-3-mini``.

        Raises:
            AuthenticationError: If *api_key* is empty.
        """
        super().__init__(api_key=api_key, model=model)
        self._client = _openai.OpenAI(
            api_key=api_key,
            base_url="https://api.x.ai/v1",
        )

    @property
    def name(self) -> str:
        """Return the canonical provider name."""
        return "grok"

    def call(self, prompt: str) -> str:
        """Send *prompt* to the xAI Grok API and return the response text.

        The request enforces ``temperature=0.0`` and JSON-object output
        mode. Transient rate-limit errors are retried up to three times
        with exponential back-off (5 s, 10 s, 20 s).

        Args:
            prompt: The user-role message to send.

        Returns:
            The assistant's response as a raw string.

        Raises:
            AuthenticationError: If the API key is invalid.
            RateLimitError: If the rate limit persists after retries.
            ProviderError: For all other API failures.
        """
        for attempt in range(3):
            try:
                response = self._client.chat.completions.create(
                    model=self.model,
                    temperature=0.0,
                    response_format={"type": "json_object"},
                    messages=[{"role": "user", "content": prompt}],
                )
                time.sleep(0.5)
                return response.choices[0].message.content
            except _openai.AuthenticationError as exc:
                raise AuthenticationError(
                    "Grok authentication failed. Check your xAI API key."
                ) from exc
            except _openai.RateLimitError as exc:
                if attempt < 2:
                    time.sleep((2 ** attempt) * 5)
                    continue
                raise RateLimitError("Rate limit persisted.") from exc
            except Exception as exc:
                raise ProviderError(f"Grok call failed: {exc}") from exc
        raise ProviderError("Unexpected exit.")
