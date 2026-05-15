"""Atomic claim extraction.

Decomposes an LLM-generated answer into discrete, individually verifiable
factual claims. Each claim becomes the unit of evaluation in the downstream
verification stage.
"""

from __future__ import annotations

from hallucination_hunter.providers.base import LLMProvider, ResponseParseError

EXTRACTION_PROMPT = """You are a precise claim extractor. Break the given text into individual, atomic factual claims.

Rules:
- Each claim must be a single, verifiable statement.
- Do NOT combine two facts into one claim.
- Preserve the original meaning exactly. Do not rephrase or add information.
- If the text contains no verifiable claims, return an empty array.
- Output ONLY a valid JSON array of strings. No explanation, no preamble, no markdown.

TEXT:
{answer}

Output a JSON array like: ["claim 1", "claim 2", "claim 3"]"""


class ClaimExtractor:
    """Extracts atomic claims from an answer using an LLM provider."""

    def __init__(self, provider: LLMProvider) -> None:
        self._provider = provider

    def extract(self, answer: str) -> list[str]:
        """Extract atomic claims from the given answer.

        Args:
            answer: An LLM-generated response to decompose.

        Returns:
            A list of atomic claim strings. Empty if the answer has no
            verifiable claims or the response could not be parsed.
        """
        if not answer or not answer.strip():
            return []

        prompt = EXTRACTION_PROMPT.format(answer=answer.strip())
        response_text = self._provider.call(prompt)

        try:
            parsed = self._provider.parse_json(response_text)
        except ResponseParseError:
            return []

        if not isinstance(parsed, list):
            return []

        return [str(item).strip() for item in parsed if str(item).strip()]
