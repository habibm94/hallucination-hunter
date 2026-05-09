"""Unit tests for OpenAI, Anthropic, and Grok provider adapters.

All tests are fully offline — they patch SDK client construction so no
real API keys, network calls, or httpx connections are required.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from hallucination_hunter.providers import (
    PROVIDER_MODELS,
    PROVIDER_STATUS,
    SUPPORTED_PROVIDERS,
)
from hallucination_hunter.providers.anthropic import (
    DEFAULT_ANTHROPIC_MODEL,
    AnthropicProvider,
)
from hallucination_hunter.providers.base import (
    AuthenticationError,
    ProviderError,
    RateLimitError,
)
from hallucination_hunter.providers.grok import DEFAULT_GROK_MODEL, GrokProvider
from hallucination_hunter.providers.openai import DEFAULT_OPENAI_MODEL, OpenAIProvider


# ─── Registry tests ────────────────────────────────────────────────────────────


class TestUpdatedRegistry:
    """The provider registry now includes all four providers."""

    def test_all_four_providers_registered(self) -> None:
        assert set(SUPPORTED_PROVIDERS) == {"gemini", "openai", "anthropic", "grok"}

    def test_all_providers_have_model_menus(self) -> None:
        for name in SUPPORTED_PROVIDERS:
            assert name in PROVIDER_MODELS
            assert len(PROVIDER_MODELS[name]) >= 1

    def test_all_providers_have_status(self) -> None:
        for name in SUPPORTED_PROVIDERS:
            assert name in PROVIDER_STATUS
            assert PROVIDER_STATUS[name] in ("available", "coming_soon")

    def test_all_providers_marked_available(self) -> None:
        for name in SUPPORTED_PROVIDERS:
            assert PROVIDER_STATUS[name] == "available"


# ─── OpenAI adapter tests ──────────────────────────────────────────────────────


class TestOpenAIProvider:
    """Behaviour of OpenAIProvider — client construction is patched."""

    def test_empty_key_raises_authentication_error(self) -> None:
        with pytest.raises(AuthenticationError):
            OpenAIProvider(api_key="")

    def test_name_is_openai(self) -> None:
        with patch("hallucination_hunter.providers.openai._openai.OpenAI"):
            provider = OpenAIProvider(api_key="test-key")
        assert provider.name == "openai"

    def test_default_model(self) -> None:
        with patch("hallucination_hunter.providers.openai._openai.OpenAI"):
            provider = OpenAIProvider(api_key="test-key")
        assert provider.model == DEFAULT_OPENAI_MODEL

    def test_successful_call_returns_content(self) -> None:
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value.choices[
            0
        ].message.content = '{"verdict": "ENTAIL"}'

        with patch("hallucination_hunter.providers.openai._openai.OpenAI", return_value=mock_client):
            provider = OpenAIProvider(api_key="test-key")

        with patch("time.sleep"):
            result = provider.call("test prompt")

        assert result == '{"verdict": "ENTAIL"}'

    def test_authentication_error_is_mapped(self) -> None:
        import openai as _openai

        mock_client = MagicMock()
        mock_client.chat.completions.create.side_effect = _openai.AuthenticationError(
            "bad key", response=MagicMock(), body={}
        )

        with patch("hallucination_hunter.providers.openai._openai.OpenAI", return_value=mock_client):
            provider = OpenAIProvider(api_key="bad-key")

        with pytest.raises(AuthenticationError):
            provider.call("prompt")

    def test_rate_limit_error_retries_then_raises(self) -> None:
        import openai as _openai

        mock_client = MagicMock()
        mock_client.chat.completions.create.side_effect = _openai.RateLimitError(
            "rate limit", response=MagicMock(), body={}
        )

        with patch("hallucination_hunter.providers.openai._openai.OpenAI", return_value=mock_client):
            provider = OpenAIProvider(api_key="test-key")

        with patch("time.sleep"), pytest.raises(RateLimitError):
            provider.call("prompt")

    def test_generic_exception_wrapped_as_provider_error(self) -> None:
        mock_client = MagicMock()
        mock_client.chat.completions.create.side_effect = RuntimeError("network error")

        with patch("hallucination_hunter.providers.openai._openai.OpenAI", return_value=mock_client):
            provider = OpenAIProvider(api_key="test-key")

        with pytest.raises(ProviderError):
            provider.call("prompt")


# ─── Anthropic adapter tests ───────────────────────────────────────────────────


class TestAnthropicProvider:
    """Behaviour of AnthropicProvider — client construction is patched."""

    def test_empty_key_raises_authentication_error(self) -> None:
        with pytest.raises(AuthenticationError):
            AnthropicProvider(api_key="")

    def test_name_is_anthropic(self) -> None:
        with patch("hallucination_hunter.providers.anthropic._anthropic.Anthropic"):
            provider = AnthropicProvider(api_key="test-key")
        assert provider.name == "anthropic"

    def test_default_model(self) -> None:
        with patch("hallucination_hunter.providers.anthropic._anthropic.Anthropic"):
            provider = AnthropicProvider(api_key="test-key")
        assert provider.model == DEFAULT_ANTHROPIC_MODEL

    def test_json_suffix_appended_to_prompt(self) -> None:
        mock_client = MagicMock()
        mock_client.messages.create.return_value.content[0].text = '{"verdict": "NEUTRAL"}'
        captured = []

        def capture(**kwargs):
            captured.append(kwargs["messages"][0]["content"])
            return mock_client.messages.create.return_value

        mock_client.messages.create.side_effect = capture

        with patch(
            "hallucination_hunter.providers.anthropic._anthropic.Anthropic",
            return_value=mock_client,
        ):
            provider = AnthropicProvider(api_key="test-key")

        with patch("time.sleep"):
            provider.call("original prompt")

        assert "original prompt" in captured[0]
        assert "JSON only" in captured[0]

    def test_successful_call_returns_content(self) -> None:
        mock_client = MagicMock()
        mock_client.messages.create.return_value.content[0].text = '{"verdict": "CONTRADICT"}'

        with patch(
            "hallucination_hunter.providers.anthropic._anthropic.Anthropic",
            return_value=mock_client,
        ):
            provider = AnthropicProvider(api_key="test-key")

        with patch("time.sleep"):
            result = provider.call("test prompt")

        assert result == '{"verdict": "CONTRADICT"}'

    def test_rate_limit_error_retries_then_raises(self) -> None:
        import anthropic as _anthropic

        mock_client = MagicMock()
        mock_client.messages.create.side_effect = _anthropic.RateLimitError(
            message="rate limit", response=MagicMock(), body={}
        )

        with patch(
            "hallucination_hunter.providers.anthropic._anthropic.Anthropic",
            return_value=mock_client,
        ):
            provider = AnthropicProvider(api_key="test-key")

        with patch("time.sleep"), pytest.raises(RateLimitError):
            provider.call("prompt")

    def test_generic_exception_wrapped_as_provider_error(self) -> None:
        mock_client = MagicMock()
        mock_client.messages.create.side_effect = RuntimeError("timeout")

        with patch(
            "hallucination_hunter.providers.anthropic._anthropic.Anthropic",
            return_value=mock_client,
        ):
            provider = AnthropicProvider(api_key="test-key")

        with pytest.raises(ProviderError):
            provider.call("prompt")


# ─── Grok adapter tests ────────────────────────────────────────────────────────


class TestGrokProvider:
    """Behaviour of GrokProvider — client construction is patched."""

    def test_empty_key_raises_authentication_error(self) -> None:
        with pytest.raises(AuthenticationError):
            GrokProvider(api_key="")

    def test_name_is_grok(self) -> None:
        with patch("hallucination_hunter.providers.grok._openai.OpenAI"):
            provider = GrokProvider(api_key="test-key")
        assert provider.name == "grok"

    def test_default_model(self) -> None:
        with patch("hallucination_hunter.providers.grok._openai.OpenAI"):
            provider = GrokProvider(api_key="test-key")
        assert provider.model == DEFAULT_GROK_MODEL

    def test_successful_call_returns_content(self) -> None:
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value.choices[
            0
        ].message.content = '{"verdict": "ENTAIL"}'

        with patch("hallucination_hunter.providers.grok._openai.OpenAI", return_value=mock_client):
            provider = GrokProvider(api_key="test-key")

        with patch("time.sleep"):
            result = provider.call("test prompt")

        assert result == '{"verdict": "ENTAIL"}'

    def test_rate_limit_error_retries_then_raises(self) -> None:
        import openai as _openai

        mock_client = MagicMock()
        mock_client.chat.completions.create.side_effect = _openai.RateLimitError(
            "rate limit", response=MagicMock(), body={}
        )

        with patch("hallucination_hunter.providers.grok._openai.OpenAI", return_value=mock_client):
            provider = GrokProvider(api_key="test-key")

        with patch("time.sleep"), pytest.raises(RateLimitError):
            provider.call("prompt")

    def test_generic_exception_wrapped_as_provider_error(self) -> None:
        mock_client = MagicMock()
        mock_client.chat.completions.create.side_effect = RuntimeError("connection error")

        with patch("hallucination_hunter.providers.grok._openai.OpenAI", return_value=mock_client):
            provider = GrokProvider(api_key="test-key")

        with pytest.raises(ProviderError):
            provider.call("prompt")
