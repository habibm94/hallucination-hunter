"""OpenAI provider adapter for Hallucination Hunter.

Uses the official OpenAI Python SDK to interact with GPT-series models.
Obtain an API key at https://platform.openai.com/api-keys

Supports JSON-mode output enforcement and exponential backoff
on rate-limit errors.
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

OPENAI_MODELS: dict[str, str] = {
    "gpt-4o-mini": "Fast · pay-per-use",
    "gpt-4o": "Powerful · pay-per-use",
}
DEFAULT_OPENAI_MODEL = "gpt-4o-mini"


class OpenAIProvider(LLMProvider):
    """LLM provider backed by the OpenAI chat-completions API."""

    def __init__(self, api_key: str, model: str = DEFAULT_OPENAI_MODEL) -> None:
        """Initialise the OpenAI provider.

        Args:
            api_key: A valid OpenAI API key.
            model: Model identifier. Defaults to ``gpt-4o-mini``.

        Raises:
            AuthenticationError: If *api_key* is empty.
        """
        super().__init__(api_key=api_key, model=model)
        self._client = _openai.OpenAI(api_key=api_key)

    @property
    def name(self) -> str:
        """Return the canonical provider name."""
        return "openai"

    def call(self, prompt: str) -> str:
        """Send *prompt* to the OpenAI API and return the response text.

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
                    "OpenAI authentication failed. Check your API key."
                ) from exc
            except _openai.RateLimitError as exc:
                if attempt < 2:
                    time.sleep((2 ** attempt) * 5)
                    continue
                raise RateLimitError("Rate limit persisted.") from exc
            except Exception as exc:
                raise ProviderError(f"OpenAI call failed: {exc}") from exc
        raise ProviderError("Unexpected exit.")
