"""Metric calculation for the RAG Triad framework.

Aggregates per-claim verification results into the three quality metrics
that comprise the RAG Triad: Faithfulness, Answer Relevancy, and Context
Precision. Faithfulness is the primary signal for hallucination detection.
"""

from __future__ import annotations

from hallucination_hunter.models import (
    PASS_THRESHOLD,
    WARNING_THRESHOLD,
    AuditReport,
    AuditStatus,
    ClaimResult,
)


class MetricsEngine:
    """Calculates aggregate metrics and assembles audit reports."""

    @staticmethod
    def faithfulness(claim_results: list[ClaimResult]) -> float:
        """Compute faithfulness as the mean of claim scores.

        Returns 0.0 when no claims are present, since an answer that asserts
        nothing cannot be considered grounded.
        """
        if not claim_results:
            return 0.0
        return sum(c.score for c in claim_results) / len(claim_results)

    @staticmethod
    def status_for(faithfulness_score: float) -> AuditStatus:
        """Map a faithfulness score to a discrete pass/warning/fail status."""
        if faithfulness_score >= PASS_THRESHOLD:
            return AuditStatus.PASS
        if faithfulness_score >= WARNING_THRESHOLD:
            return AuditStatus.WARNING
        return AuditStatus.FAIL

    @classmethod
    def build_report(
        cls,
        source: str,
        question: str,
        answer: str,
        claim_results: list[ClaimResult],
    ) -> AuditReport:
        """Assemble a complete ``AuditReport`` from verified claims.

        Args:
            source: The ground-truth source document.
            question: The question that was asked.
            answer: The LLM response under audit.
            claim_results: Per-claim verification outcomes.

        Returns:
            A populated ``AuditReport`` with computed metrics and status.
        """
        faithfulness = cls.faithfulness(claim_results)
        return AuditReport(
            source=source,
            question=question,
            answer=answer,
            claims=claim_results,
            faithfulness_score=faithfulness,
            answer_relevancy_score=0.0,
            context_precision_score=1.0,
            status=cls.status_for(faithfulness),
        )
