"""Provider abstraction layer.

Defines the contract every LLM provider adapter must satisfy.
The evaluation pipeline (extractor, verifier) depends only on this
interface, never on a concrete provider — enabling drop-in replacement
of Gemini, OpenAI, Anthropic, or Grok without touching business logic.
"""

from __future__ import annotations

import json
import re
from abc import ABC, abstractmethod
from typing import Any


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------


class ProviderError(Exception):
    """Base exception for all provider-related failures."""


class AuthenticationError(ProviderError):
    """Raised when API credentials are missing or rejected."""


class RateLimitError(ProviderError):
    """Raised when the provider's quota is exhausted after retries."""


class ResponseParseError(ProviderError):
    """Raised when the provider's response cannot be decoded as JSON."""


# ---------------------------------------------------------------------------
# Abstract base
# ---------------------------------------------------------------------------


class LLMProvider(ABC):
    """Abstract base class for LLM provider adapters.

    Subclasses must implement ``call`` to perform the actual HTTP request
    to their provider's API. The ``parse_json`` utility is shared so that
    all providers benefit from the same resilient JSON extraction logic.

    Args:
        api_key: Provider API key. Must be non-empty.
        model: Model identifier string (provider-specific).
    """

    def __init__(self, api_key: str, model: str) -> None:
        if not api_key or not api_key.strip():
            raise AuthenticationError("A non-empty API key is required.")
        self.api_key = api_key
        self.model = model

    @abstractmethod
    def call(self, prompt: str) -> str:
        """Send a prompt to the provider and return the raw text response.

        The response is expected to be valid JSON. Implementations are
        responsible for retry logic and rate-limit handling.

        Args:
            prompt: Complete prompt string.

        Returns:
            Model's text output.

        Raises:
            AuthenticationError: If credentials are rejected by the API.
            RateLimitError: If rate limits are exhausted after all retries.
            ProviderError: For all other provider-side errors.
        """

    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable provider identifier, e.g. ``'gemini'``."""

    @staticmethod
    def parse_json(text: str) -> Any:
        """Extract and parse JSON from a model response.

        Handles the most common LLM output quirks:
        - Markdown code fences (```json ... ```)
        - Leading / trailing whitespace or prose preamble
        - JSON object or array embedded in surrounding text

        Args:
            text: Raw text response from the model.

        Returns:
            Parsed JSON value (dict, list, or primitive).

        Raises:
            ResponseParseError: If no valid JSON can be extracted.
        """
        cleaned = text.strip()
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
        cleaned = re.sub(r"\s*```$", "", cleaned)

        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            pass

        # Second attempt: extract the first JSON object or array in the text.
        match = re.search(r"(\{.*\}|\[.*\])", cleaned, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1))
            except json.JSONDecodeError:
                pass

        raise ResponseParseError(
            f"Could not parse JSON from model response: {text[:300]!r}"
        )
