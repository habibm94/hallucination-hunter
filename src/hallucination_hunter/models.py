"""Domain models for hallucination audit reports.

All models use Pydantic v2 for runtime validation and serialisation.
These types are the shared vocabulary of the entire evaluation pipeline —
providers, core logic, CLI, and UI all import from this module.
"""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class Verdict(str, Enum):
    """NLI classification of a single claim against its source document.

    Attributes:
        ENTAIL: The source directly supports the claim.
        CONTRADICT: The source factually conflicts with the claim.
        NEUTRAL: The source is silent on the claim (ungrounded assertion).
    """

    ENTAIL = "ENTAIL"
    CONTRADICT = "CONTRADICT"
    NEUTRAL = "NEUTRAL"


class AuditStatus(str, Enum):
    """Overall faithfulness classification for a complete audit.

    Thresholds:
        PASS    >= 0.85
        WARNING >= 0.50
        FAIL     < 0.50
    """

    PASS = "PASS"
    WARNING = "WARNING"
    FAIL = "FAIL"


VERDICT_SCORES: dict[Verdict, float] = {
    Verdict.ENTAIL: 1.0,
    Verdict.NEUTRAL: 0.5,
    Verdict.CONTRADICT: 0.0,
}

PASS_THRESHOLD = 0.85
WARNING_THRESHOLD = 0.50


class ClaimResult(BaseModel):
    """Verification result for a single atomic claim.

    Attributes:
        claim: The atomic factual statement extracted from the LLM response.
        verdict: NLI classification against the source document.
        score: Numeric score derived from the verdict (0.0, 0.5, or 1.0).
        source_evidence: Quoted passage from the source that led to the verdict.
    """

    model_config = ConfigDict(frozen=True)

    claim: str = Field(..., min_length=1)
    verdict: Verdict
    score: float = Field(..., ge=0.0, le=1.0)
    source_evidence: str = ""


class AuditReport(BaseModel):
    """Complete hallucination audit for a single source / question / answer triplet.

    Aggregates per-claim results into the three RAG Triad metrics:
        - Faithfulness: fraction of claims supported by the source.
        - Answer Relevancy: whether the answer addresses the question (Step 6+).
        - Context Precision: whether the source was the right context (Step 7+).

    Use ``to_dict()`` for JSON-serialisable output.
    """

    model_config = ConfigDict(frozen=True)

    source: str
    question: str
    answer: str
    claims: list[ClaimResult] = Field(default_factory=list)
    faithfulness_score: float = Field(default=0.0, ge=0.0, le=1.0)
    answer_relevancy_score: float = Field(default=0.0, ge=0.0, le=1.0)
    context_precision_score: float = Field(default=1.0, ge=0.0, le=1.0)
    status: AuditStatus = AuditStatus.FAIL

    @property
    def total_claims(self) -> int:
        """Total number of atomic claims extracted from the answer."""
        return len(self.claims)

    @property
    def supported_claims(self) -> int:
        """Claims fully supported by the source (ENTAIL)."""
        return sum(1 for c in self.claims if c.verdict == Verdict.ENTAIL)

    @property
    def contradicted_claims(self) -> int:
        """Claims directly contradicted by the source."""
        return sum(1 for c in self.claims if c.verdict == Verdict.CONTRADICT)

    @property
    def ungrounded_claims(self) -> int:
        """Claims not addressed by the source (NEUTRAL)."""
        return sum(1 for c in self.claims if c.verdict == Verdict.NEUTRAL)

    def to_dict(self) -> dict[str, Any]:
        """Serialise the report to a JSON-compatible dictionary."""
        return {
            "status": self.status.value,
            "faithfulness_score": round(self.faithfulness_score, 3),
            "answer_relevancy_score": round(self.answer_relevancy_score, 3),
            "context_precision_score": round(self.context_precision_score, 3),
            "summary": {
                "total_claims": self.total_claims,
                "supported": self.supported_claims,
                "contradicted": self.contradicted_claims,
                "ungrounded": self.ungrounded_claims,
            },
            "claims": [
                {
                    "claim": c.claim,
                    "verdict": c.verdict.value,
                    "score": c.score,
                    "source_evidence": c.source_evidence,
                }
                for c in self.claims
            ],
        }
