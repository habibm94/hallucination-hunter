"""Structured error system for Hallucination Hunter."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class ErrorCategory(str, Enum):
    AUTH = "AUTH"
    RATE = "RATE"
    INPUT = "INPUT"
    PARSE = "PARSE"
    NETWORK = "NETWORK"
    PROVIDER = "PROVIDER"
    SAFETY = "SAFETY"
    INTERNAL = "INTERNAL"


@dataclass(frozen=True)
class ErrorDetail:
    code: str
    category: ErrorCategory
    message: str
    suggestion: str
    retry_safe: bool = False
    context: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "code": self.code,
            "category": self.category.value,
            "message": self.message,
            "suggestion": self.suggestion,
            "retry_safe": self.retry_safe,
            "context": self.context,
        }

    def display_text(self) -> str:
        retry_hint = "Retry-safe: yes" if self.retry_safe else "Retry-safe: no"
        return (
            f"**{self.code}** - {self.message}\n\n"
            f"*Suggestion:* {self.suggestion}\n\n"
            f"*{retry_hint}*"
        )


class HallucinationHunterError(Exception):
    def __init__(self, detail: ErrorDetail) -> None:
        self.detail = detail
        super().__init__(f"[{detail.code}] {detail.message}")


class AuthError(HallucinationHunterError):
    pass


class RateLimitError(HallucinationHunterError):
    pass


class InputError(HallucinationHunterError):
    pass


class ParseError(HallucinationHunterError):
    pass


class NetworkError(HallucinationHunterError):
    pass


class ProviderError(HallucinationHunterError):
    pass


class SafetyError(HallucinationHunterError):
    pass


class InternalError(HallucinationHunterError):
    pass


_CATALOG: dict[str, tuple[ErrorCategory, str, str, bool]] = {
    "HH-AUTH-001": (
        ErrorCategory.AUTH,
        "Invalid or empty API key.",
        "Check the API key in Section A. Make sure you copied the full key.",
        False,
    ),
    "HH-AUTH-002": (
        ErrorCategory.AUTH,
        "API key was rejected by the provider.",
        "The key may be expired, revoked, or for a different account. "
        "Generate a new key in your provider dashboard.",
        False,
    ),
    "HH-RATE-001": (
        ErrorCategory.RATE,
        "Provider rate limit exceeded.",
        "Wait 30-60 seconds before retrying. If this persists, your "
        "account may have hit a daily quota.",
        True,
    ),
    "HH-RATE-002": (
        ErrorCategory.RATE,
        "Provider monthly quota exhausted.",
        "Upgrade your plan or wait for the quota to reset.",
        False,
    ),
    "HH-INPUT-001": (
        ErrorCategory.INPUT,
        "Source context is empty.",
        "Paste a document, article, or knowledge-base text into the "
        "Source Context field.",
        False,
    ),
    "HH-INPUT-002": (
        ErrorCategory.INPUT,
        "Input exceeds the maximum allowed length.",
        "Shorten the input. Limits: 10,000 chars (source), "
        "1,000 chars (question), 5,000 chars (answer).",
        False,
    ),
    "HH-INPUT-003": (
        ErrorCategory.INPUT,
        "Input appears to be gibberish (repeated characters or no "
        "recognisable content).",
        "Provide real text. Random characters or single repeated "
        "characters cannot be audited.",
        False,
    ),
    "HH-INPUT-004": (
        ErrorCategory.INPUT,
        "Question field is empty.",
        "Enter the question that was asked of the LLM.",
        False,
    ),
    "HH-INPUT-005": (
        ErrorCategory.INPUT,
        "Answer field is empty.",
        "Paste the LLM response you want to audit.",
        False,
    ),
    "HH-PARSE-001": (
        ErrorCategory.PARSE,
        "LLM returned malformed JSON.",
        "Retry the audit. If it persists, switch to a more capable model "
        "(e.g. gemini-2.5-pro instead of flash-lite).",
        True,
    ),
    "HH-PARSE-002": (
        ErrorCategory.PARSE,
        "Claim extraction returned no claims.",
        "The answer may be too short or non-factual (e.g. a refusal). "
        "Try an answer with concrete factual statements.",
        False,
    ),
    "HH-NETWORK-001": (
        ErrorCategory.NETWORK,
        "Could not reach the provider.",
        "Check your internet connection. If you are behind a corporate "
        "firewall, the provider's API may be blocked.",
        True,
    ),
    "HH-NETWORK-002": (
        ErrorCategory.NETWORK,
        "Provider request timed out.",
        "The provider is slow or under load. Wait 30 seconds and retry.",
        True,
    ),
    "HH-PROVIDER-001": (
        ErrorCategory.PROVIDER,
        "Provider is currently unavailable.",
        "Pick a different provider in Section A.",
        True,
    ),
    "HH-PROVIDER-002": (
        ErrorCategory.PROVIDER,
        "Selected model is not supported by this provider.",
        "Pick a different model from the dropdown.",
        False,
    ),
    "HH-SAFETY-001": (
        ErrorCategory.SAFETY,
        "Provider safety filter blocked the request.",
        "The source or answer triggered the provider's content filter. "
        "Try a different example or a different provider.",
        False,
    ),
    "HH-INTERNAL-001": (
        ErrorCategory.INTERNAL,
        "Unexpected error inside the pipeline.",
        "This is a bug. Open an issue on GitHub with the full error trace.",
        False,
    ),
}


def make_error(
    code: str,
    *,
    context: dict[str, Any] | None = None,
    message_override: str | None = None,
) -> ErrorDetail:
    if code not in _CATALOG:
        raise KeyError(
            f"Unknown error code {code!r}. Add it to errors._CATALOG."
        )
    category, default_message, suggestion, retry_safe = _CATALOG[code]
    return ErrorDetail(
        code=code,
        category=category,
        message=message_override or default_message,
        suggestion=suggestion,
        retry_safe=retry_safe,
        context=context or {},
    )


# ---------------------------------------------------------------------------
# Length limits
# ---------------------------------------------------------------------------
MAX_SOURCE_CHARS = 10_000
MAX_QUESTION_CHARS = 1_000
MAX_ANSWER_CHARS = 5_000

# Source must be substantive enough to ground claims (full sentence).
MIN_SOURCE_CHARS = 15

# Answer can be as short as a single character to accommodate MCQ
# answers (A/B/C/D) and short factual responses (yes/no, 42, etc).
MIN_ANSWER_CHARS = 1


def validate_source(text: str | None) -> ErrorDetail | None:
    """Source must be present, within length limits, and not gibberish."""
    if text is None or not text.strip():
        return make_error("HH-INPUT-001")
    if len(text) > MAX_SOURCE_CHARS:
        return make_error(
            "HH-INPUT-002",
            context={"field": "source", "length": len(text), "limit": MAX_SOURCE_CHARS},
        )
    if len(text.strip()) < MIN_SOURCE_CHARS:
        return make_error(
            "HH-INPUT-003",
            context={"field": "source", "reason": "too_short_to_ground"},
            message_override=(
                "Source context is too short to ground any claims. "
                "Provide at least a sentence of grounding material."
            ),
        )
    if _is_pure_gibberish(text):
        return make_error(
            "HH-INPUT-003",
            context={"field": "source", "sample": text[:80]},
        )
    return None


def validate_question(text: str | None) -> ErrorDetail | None:
    """Question must be present and within length limits."""
    if text is None or not text.strip():
        return make_error("HH-INPUT-004")
    if len(text) > MAX_QUESTION_CHARS:
        return make_error(
            "HH-INPUT-002",
            context={"field": "question", "length": len(text), "limit": MAX_QUESTION_CHARS},
        )
    return None


def validate_answer(text: str | None) -> ErrorDetail | None:
    """Answer must be present and within length limits.

    Accepts very short answers (MCQ: 'A', short: '42', 'yes').
    Only blocks empty answers and clear gibberish patterns.
    """
    if text is None or not text.strip():
        return make_error("HH-INPUT-005")
    if len(text) > MAX_ANSWER_CHARS:
        return make_error(
            "HH-INPUT-002",
            context={"field": "answer", "length": len(text), "limit": MAX_ANSWER_CHARS},
        )
    if len(text.strip()) < MIN_ANSWER_CHARS:
        return make_error(
            "HH-INPUT-003",
            context={"field": "answer", "reason": "too_short"},
        )
    if _is_pure_gibberish(text):
        return make_error(
            "HH-INPUT-003",
            context={"field": "answer", "sample": text[:80]},
        )
    return None


def _is_pure_gibberish(text: str) -> bool:
    """Return True only for clear gibberish.

    Does NOT trigger on short legitimate answers like '1972', 'yes', 'A'.
    """
    stripped = text.strip()
    if not stripped:
        return True

    no_space = stripped.replace(" ", "").replace("\n", "").replace("\t", "")
    if len(no_space) >= 4 and len(set(no_space)) <= 2:
        return True

    tokens = [t for t in stripped.split() if t]
    if len(tokens) >= 6:
        unique_ratio = len(set(tokens)) / len(tokens)
        if unique_ratio < 0.20:
            return True

    if not any(c.isalnum() for c in stripped):
        return True

    return False
