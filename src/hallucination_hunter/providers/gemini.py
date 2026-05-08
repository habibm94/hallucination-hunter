"""Google Gemini provider adapter.

Wraps the ``google-generativeai`` SDK with retry logic, rate-limit
back-off, and JSON-mode enforcement. This is the default provider
for development (free tier, no credit card required).

Free-tier limits as of 2026 (subject to change — verify at
https://aistudio.google.com/app/apikey):
    gemini-2.5-flash-lite : 15 RPM, 1 000 RPD
    gemini-2.5-flash      : 10 RPM,   250 RPD
    gemini-2.5-pro        :  5 RPM,   100 RPD
"""

from __future__ import annotations

import time

import google.generativeai as genai

from hallucination_hunter.providers.base import (
    AuthenticationError,
    LLMProvider,
    ProviderError,
    RateLimitError,
)

# Supported model identifiers for Gemini free tier.
GEMINI_MODELS: dict[str, str] = {
    "gemini-2.5-flash-lite": "Gemini 2.5 Flash-Lite (free · 1 000 RPD)",
    "gemini-2.5-flash": "Gemini 2.5 Flash (free · 250 RPD)",
    "gemini-2.5-pro": "Gemini 2.5 Pro (free · 100 RPD)",
}

DEFAULT_GEMINI_MODEL = "gemini-2.5-flash-lite"

# Minimum delay between consecutive requests (free-tier safety margin).
_REQUEST_DELAY_SECONDS = 0.5

# Exponential back-off base for rate-limit retries.
_RETRY_BASE_SECONDS = 5
_MAX_RETRIES = 3


class GeminiProvider(LLMProvider):
    """Adapter for the Google Gemini API.

    Configures the SDK with the supplied key, forces JSON output mode
    (``response_mime_type='application/json'``), and sets temperature to
    0 for deterministic evaluation responses.

    Args:
        api_key: Gemini API key (obtain free at aistudio.google.com).
        model: Gemini model identifier. Defaults to ``gemini-2.5-flash-lite``.
    """

    def __init__(self, api_key: str, model: str = DEFAULT_GEMINI_MODEL) -> None:
        super().__init__(api_key, model)
        try:
            genai.configure(api_key=self.api_key)
            self._model = genai.GenerativeModel(
                model,
                generation_config={
                    "temperature": 0.0,
                    "response_mime_type": "application/json",
                },
            )
        except Exception as exc:
            raise AuthenticationError(
                f"Gemini SDK initialisation failed: {exc}"
            ) from exc

    @property
    def name(self) -> str:
        return "gemini"

    def call(self, prompt: str) -> str:
        """Send a prompt to Gemini with exponential back-off on rate errors.

        Args:
            prompt: Complete prompt string.

        Returns:
            Model's text response (expected to be valid JSON).

        Raises:
            RateLimitError: After ``_MAX_RETRIES`` rate-limit responses.
            ProviderError: For other API failures.
        """
        for attempt in range(_MAX_RETRIES):
            try:
                response = self._model.generate_content(prompt)
                time.sleep(_REQUEST_DELAY_SECONDS)
                return response.text
            except Exception as exc:
                message = str(exc).lower()
                if any(token in message for token in ("429", "rate", "quota", "resource_exhausted")):
                    if attempt == _MAX_RETRIES - 1:
                        raise RateLimitError(
                            "Gemini rate limit exhausted after "
                            f"{_MAX_RETRIES} retries."
                        ) from exc
                    wait = _RETRY_BASE_SECONDS * (2 ** attempt)
                    time.sleep(wait)
                    continue
                raise ProviderError(f"Gemini API error: {exc}") from exc

        raise ProviderError("Unexpected exit from retry loop.")
