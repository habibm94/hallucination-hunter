"""Provider registry for Hallucination Hunter.

Exposes a unified ``create_provider`` factory and metadata dicts for all
supported LLM back-ends.
"""

from hallucination_hunter.providers.anthropic import (
    ANTHROPIC_MODELS,
    DEFAULT_ANTHROPIC_MODEL,
    AnthropicProvider,
)
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
from hallucination_hunter.providers.grok import (
    DEFAULT_GROK_MODEL,
    GROK_MODELS,
    GrokProvider,
)
from hallucination_hunter.providers.groq import (
    DEFAULT_GROQ_MODEL,
    GROQ_MODELS,
    GroqProvider,
)
from hallucination_hunter.providers.openai import (
    DEFAULT_OPENAI_MODEL,
    OPENAI_MODELS,
    OpenAIProvider,
)

_REGISTRY: dict[str, type[LLMProvider]] = {
    "gemini": GeminiProvider,
    "openai": OpenAIProvider,
    "anthropic": AnthropicProvider,
    "grok": GrokProvider,
    "groq": GroqProvider,
}

PROVIDER_MODELS: dict[str, dict[str, str]] = {
    "gemini": GEMINI_MODELS,
    "openai": OPENAI_MODELS,
    "anthropic": ANTHROPIC_MODELS,
    "grok": GROK_MODELS,
    "groq": GROQ_MODELS,
}

PROVIDER_STATUS: dict[str, str] = {
    "gemini": "available",
    "openai": "available",
    "anthropic": "available",
    "grok": "available",
    "groq": "available",
}

SUPPORTED_PROVIDERS: list[str] = list(_REGISTRY.keys())


def create_provider(provider: str, api_key: str, model: str) -> LLMProvider:
    """Instantiate and return the requested provider adapter."""
    key = provider.lower().strip()
    if key not in _REGISTRY:
        available = ", ".join(sorted(_REGISTRY.keys()))
        raise ValueError(f"Unknown provider {provider!r}. Available: {available}")
    return _REGISTRY[key](api_key=api_key, model=model)


__all__ = [
    "ANTHROPIC_MODELS",
    "AuthenticationError",
    "DEFAULT_ANTHROPIC_MODEL",
    "DEFAULT_GEMINI_MODEL",
    "DEFAULT_GROK_MODEL",
    "DEFAULT_GROQ_MODEL",
    "DEFAULT_OPENAI_MODEL",
    "GEMINI_MODELS",
    "GROK_MODELS",
    "GROQ_MODELS",
    "LLMProvider",
    "OPENAI_MODELS",
    "PROVIDER_MODELS",
    "PROVIDER_STATUS",
    "ProviderError",
    "RateLimitError",
    "ResponseParseError",
    "SUPPORTED_PROVIDERS",
    "create_provider",
]
