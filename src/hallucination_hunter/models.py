"""Domain models for hallucination audit reports.

All models use Pydantic v2 for runtime validation and serialisation.
These types are the shared vocabulary of the entire evaluation pipeline.
"""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class Verdict(str, Enum):
    """NLI classification of a single claim against its source document."""

    ENTAIL = "ENTAIL"
    CONTRADICT = "CONTRADICT"
    NEUTRAL = "NEUTRAL"


class AuditStatus(str, Enum):
    """Overall faithfulness classification for a complete audit."""

    PASS = "PASS"
    WARNING = "WARNING"
    FAIL = "FAIL"


class HallucinationType(str, Enum):
    """Claim-level hallucination categories.

    A single claim may carry multiple types simultaneously.
    """

    INTRINSIC = "INTRINSIC"
    EXTRINSIC = "EXTRINSIC"
    ENTITY = "ENTITY"
    TEMPORAL = "TEMPORAL"
    NUMERIC = "NUMERIC"
    CITATION = "CITATION"
    LOGICAL = "LOGICAL"


DETAIL_TYPES: frozenset[HallucinationType] = frozenset({
    HallucinationType.ENTITY,
    HallucinationType.TEMPORAL,
    HallucinationType.NUMERIC,
    HallucinationType.CITATION,
})


VERDICT_SCORES: dict[Verdict, float] = {
    Verdict.ENTAIL: 1.0,
    Verdict.NEUTRAL: 0.5,
    Verdict.CONTRADICT: 0.0,
}

PASS_THRESHOLD = 0.85
WARNING_THRESHOLD = 0.50


class HallucinationTag(BaseModel):
    """A single hallucination type instance attached to a claim."""

    model_config = ConfigDict(frozen=True)

    type: HallucinationType
    explanation: str = ""


class ClaimResult(BaseModel):
    """Verification result for a single atomic claim."""

    model_config = ConfigDict(frozen=True)

    claim: str = Field(..., min_length=1)
    verdict: Verdict
    score: float = Field(..., ge=0.0, le=1.0)
    source_evidence: str = ""
    hallucination_tags: list[HallucinationTag] = Field(default_factory=list)


class AuditReport(BaseModel):
    """Complete hallucination audit for a single source/question/answer triplet."""

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
        return len(self.claims)

    @property
    def supported_claims(self) -> int:
        return sum(1 for c in self.claims if c.verdict == Verdict.ENTAIL)

    @property
    def contradicted_claims(self) -> int:
        return sum(1 for c in self.claims if c.verdict == Verdict.CONTRADICT)

    @property
    def ungrounded_claims(self) -> int:
        return sum(1 for c in self.claims if c.verdict == Verdict.NEUTRAL)

    def hallucination_summary(self) -> dict[HallucinationType, list[str]]:
        """Aggregate hallucination tags across all claims."""
        summary: dict[HallucinationType, list[str]] = {
            t: [] for t in HallucinationType
        }
        for claim in self.claims:
            for tag in claim.hallucination_tags:
                summary[tag.type].append(tag.explanation)
        return summary

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
            "hallucinations": {
                t.value: explanations
                for t, explanations in self.hallucination_summary().items()
            },
            "claims": [
                {
                    "claim": c.claim,
                    "verdict": c.verdict.value,
                    "score": c.score,
                    "source_evidence": c.source_evidence,
                    "hallucination_tags": [
                        {"type": tag.type.value, "explanation": tag.explanation}
                        for tag in c.hallucination_tags
                    ],
                }
                for c in self.claims
            ],
        }
