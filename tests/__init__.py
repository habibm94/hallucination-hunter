"""Provider registry and factory.

Exposes a single ``create_provider`` factory that resolves a provider
name and returns the appropriate ``LLMProvider`` instance. New providers
are registered here without changes to the rest of the codebase.
"""

from __future__ import annotations

from hallucination_hunter.providers.base import (
    AuthenticationError,
    LLMProvider,
    ProviderError,
    RateLimitError,
    ResponseParseError,
)
from hallucination_hunter.providers.gemini import (
    DEFAULT_GEMINI_MODEL,
    GEMINI_MODELS,
    GeminiProvider,
)

# Registry maps provider name → constructor.
# Register new adapters here as they are implemented (Step 9).
_REGISTRY: dict[str, type[LLMProvider]] = {
    "gemini": GeminiProvider,
    # "openai": OpenAIProvider,
    # "anthropic": AnthropicProvider,
    # "grok": GrokProvider,
}

# Human-readable model menus consumed by the UI.
PROVIDER_MODELS: dict[str, dict[str, str]] = {
    "gemini": GEMINI_MODELS,
}

SUPPORTED_PROVIDERS: list[str] = list(_REGISTRY.keys())


def create_provider(provider: str, api_key: str, model: str) -> LLMProvider:
    """Instantiate an LLM provider adapter by name.

    Args:
        provider: Provider name (e.g. ``'gemini'``). Case-insensitive.
        api_key: API key for the chosen provider.
        model: Model identifier string (provider-specific).

    Returns:
        Configured ``LLMProvider`` ready to call.

    Raises:
        ValueError: If the provider name is not in the registry.
        AuthenticationError: If the API key is empty.
    """
    key = provider.lower().strip()
    if key not in _REGISTRY:
        available = ", ".join(sorted(_REGISTRY.keys()))
        raise ValueError(
            f"Unknown provider {provider!r}. Available: {available}"
        )
    return _REGISTRY[key](api_key=api_key, model=model)


__all__ = [
    "AuthenticationError",
    "LLMProvider",
    "ProviderError",
    "RateLimitError",
    "ResponseParseError",
    "PROVIDER_MODELS",
    "SUPPORTED_PROVIDERS",
    "create_provider",
]
