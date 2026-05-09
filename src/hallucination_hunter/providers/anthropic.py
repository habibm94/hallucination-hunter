"""Anthropic provider adapter for Hallucination Hunter.

Uses the official Anthropic Python SDK to interact with Claude models.
Obtain an API key at https://console.anthropic.com/settings/keys

Anthropic's messages API does not offer a native JSON output mode, so
a JSON-enforcement suffix is appended to every prompt automatically.
"""

from __future__ import annotations

import time

import anthropic as _anthropic

from hallucination_hunter.providers.base import (
    AuthenticationError,
    LLMProvider,
    ProviderError,
    RateLimitError,
)

ANTHROPIC_MODELS: dict[str, str] = {
    "claude-haiku-4-5": "Fast · pay-per-use",
    "claude-sonnet-4-6": "Balanced · pay-per-use",
}
DEFAULT_ANTHROPIC_MODEL = "claude-haiku-4-5"

_JSON_SUFFIX = (
    "\n\nRespond with valid JSON only. No explanation, no markdown, no preamble."
)


class AnthropicProvider(LLMProvider):
    """LLM provider backed by the Anthropic messages API."""

    def __init__(self, api_key: str, model: str = DEFAULT_ANTHROPIC_MODEL) -> None:
        """Initialise the Anthropic provider.

        Args:
            api_key: A valid Anthropic API key.
            model: Model identifier. Defaults to ``claude-haiku-4-5``.

        Raises:
            AuthenticationError: If *api_key* is empty.
        """
        super().__init__(api_key=api_key, model=model)
        self._client = _anthropic.Anthropic(api_key=api_key)

    @property
    def name(self) -> str:
        """Return the canonical provider name."""
        return "anthropic"

    def call(self, prompt: str) -> str:
        """Send *prompt* to the Anthropic API and return the response text.

        A JSON-enforcement suffix is appended to every prompt because the
        Anthropic API has no native JSON output mode. The request uses
        ``temperature=0.0`` and ``max_tokens=1024``.

        Transient rate-limit errors are retried up to three times with
        exponential back-off (5 s, 10 s, 20 s).

        Args:
            prompt: The user-role message to send.

        Returns:
            The assistant's response as a raw string.

        Raises:
            AuthenticationError: If the API key is invalid.
            RateLimitError: If the rate limit persists after retries.
            ProviderError: For all other API failures.
        """
        full_prompt = prompt + _JSON_SUFFIX

        for attempt in range(3):
            try:
                response = self._client.messages.create(
                    model=self.model,
                    max_tokens=1024,
                    temperature=0.0,
                    messages=[{"role": "user", "content": full_prompt}],
                )
                time.sleep(0.5)
                return response.content[0].text
            except _anthropic.AuthenticationError as exc:
                raise AuthenticationError(
                    "Anthropic authentication failed. Check your API key."
                ) from exc
            except _anthropic.RateLimitError as exc:
                if attempt < 2:
                    time.sleep((2 ** attempt) * 5)
                    continue
                raise RateLimitError("Rate limit persisted.") from exc
            except Exception as exc:
                raise ProviderError(f"Anthropic call failed: {exc}") from exc
        raise ProviderError("Unexpected exit.")
