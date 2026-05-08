"""Unit tests for the provider abstraction layer."""

from __future__ import annotations

import pytest

from hallucination_hunter.providers import (
    AuthenticationError,
    SUPPORTED_PROVIDERS,
    create_provider,
)
from hallucination_hunter.providers.base import LLMProvider, ResponseParseError


class TestProviderRegistry:
    """Behaviour of the provider factory and registry."""

    def test_gemini_is_registered(self) -> None:
        assert "gemini" in SUPPORTED_PROVIDERS

    def test_unknown_provider_raises_value_error(self) -> None:
        with pytest.raises(ValueError, match="Unknown provider"):
            create_provider("nonexistent", api_key="x", model="y")

    def test_known_provider_returns_provider_instance(self) -> None:
        provider = create_provider("gemini", api_key="test-key", model="gemini-2.5-flash-lite")
        assert isinstance(provider, LLMProvider)
        assert provider.name == "gemini"

    def test_provider_name_is_case_insensitive(self) -> None:
        provider = create_provider("GEMINI", api_key="test-key", model="gemini-2.5-flash-lite")
        assert provider.name == "gemini"


class TestJsonParsing:
    """The shared parse_json helper on the provider base class."""

    def test_parses_clean_json_object(self) -> None:
        result = LLMProvider.parse_json('{"verdict": "ENTAIL"}')
        assert result == {"verdict": "ENTAIL"}

    def test_parses_clean_json_array(self) -> None:
        result = LLMProvider.parse_json('["a", "b"]')
        assert result == ["a", "b"]

    def test_strips_markdown_code_fences(self) -> None:
        text = '```json\n{"verdict": "ENTAIL"}\n```'
        assert LLMProvider.parse_json(text) == {"verdict": "ENTAIL"}

    def test_strips_plain_code_fences(self) -> None:
        text = '```\n["a"]\n```'
        assert LLMProvider.parse_json(text) == ["a"]

    def test_extracts_json_from_surrounding_text(self) -> None:
        text = 'Here is the result: {"verdict": "NEUTRAL"} — done.'
        assert LLMProvider.parse_json(text) == {"verdict": "NEUTRAL"}

    def test_raises_on_completely_invalid_input(self) -> None:
        with pytest.raises(ResponseParseError):
            LLMProvider.parse_json("this is not json at all")


class TestAuthenticationGuard:
    """Provider construction rejects empty credentials."""

    def test_empty_api_key_raises_authentication_error(self) -> None:
        with pytest.raises(AuthenticationError):
            create_provider("gemini", api_key="", model="gemini-2.5-flash-lite")
