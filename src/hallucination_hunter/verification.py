"""Natural Language Inference verification.

For each atomic claim extracted from an answer, determines whether the
source document supports, contradicts, or is silent on the claim. This
implements the grounding check at the heart of the faithfulness metric.
"""

from __future__ import annotations

from hallucination_hunter.models import VERDICT_SCORES, ClaimResult, Verdict
from hallucination_hunter.providers.base import LLMProvider, ResponseParseError

VERIFICATION_PROMPT = """You are a strict hallucination detector. Determine if the SOURCE supports, contradicts, or is silent on the CLAIM.

SOURCE:
{source}

CLAIM:
{claim}

Classification rules:
- ENTAIL: The source directly supports this claim (the claim is grounded in the source).
- CONTRADICT: The source says something different from this claim (factually conflicts).
- NEUTRAL: The source neither supports nor contradicts this claim. It is simply not mentioned.

IMPORTANT: A claim that is true in the real world but NOT in the source is NEUTRAL, not ENTAIL.
We are checking grounding to source, not factual accuracy.

Output ONLY valid JSON. No explanation. No markdown.

Format:
{{"verdict": "ENTAIL", "evidence": "exact quote from source"}}
or
{{"verdict": "CONTRADICT", "evidence": "exact quote from source that contradicts"}}
or
{{"verdict": "NEUTRAL", "evidence": ""}}"""


class NLIVerifier:
    """Verifies individual claims against a source document via LLM-as-Judge."""

    def __init__(self, provider: LLMProvider) -> None:
        self._provider = provider

    def verify(self, claim: str, source: str) -> ClaimResult:
        """Verify a single claim against the source document.

        Args:
            claim: The atomic factual claim to verify.
            source: The ground-truth source document.

        Returns:
            A ``ClaimResult`` containing the verdict, score, and evidence.
            On parse failure, returns a NEUTRAL verdict with an empty
            evidence string rather than raising.
        """
        prompt = VERIFICATION_PROMPT.format(source=source.strip(), claim=claim.strip())
        response_text = self._provider.call(prompt)

        try:
            parsed = self._provider.parse_json(response_text)
        except ResponseParseError:
            return self._fallback_result(claim)

        if not isinstance(parsed, dict):
            return self._fallback_result(claim)

        verdict_str = str(parsed.get("verdict", "NEUTRAL")).upper()
        evidence = str(parsed.get("evidence", ""))

        try:
            verdict = Verdict(verdict_str)
        except ValueError:
            verdict = Verdict.NEUTRAL

        return ClaimResult(
            claim=claim,
            verdict=verdict,
            score=VERDICT_SCORES[verdict],
            source_evidence=evidence,
        )

    def verify_all(self, claims: list[str], source: str) -> list[ClaimResult]:
        """Verify a sequence of claims against the same source."""
        return [self.verify(claim, source) for claim in claims]

    @staticmethod
    def _fallback_result(claim: str) -> ClaimResult:
        """Return a safe NEUTRAL result when verification fails."""
        return ClaimResult(
            claim=claim,
            verdict=Verdict.NEUTRAL,
            score=VERDICT_SCORES[Verdict.NEUTRAL],
            source_evidence="",
        )
