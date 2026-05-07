"""
hallucination_hunter.py
=======================
Automated hallucination detection for LLM outputs.
Built on the RAG Triad framework: Faithfulness | Answer Relevancy | Context Precision.

Author: Habibullah Bin Mahmud
GitHub: https://github.com/habibm94/hallucination-hunter
"""

import json
import os
from dataclasses import dataclass, field
from typing import List, Optional
from enum import Enum


# ─────────────────────────────────────────────
# ENUMS & DATA MODELS
# ─────────────────────────────────────────────

class Verdict(str, Enum):
    ENTAIL = "ENTAIL"           # Source supports this claim → score: 1.0
    CONTRADICT = "CONTRADICT"   # Source contradicts this claim → score: 0.0
    NEUTRAL = "NEUTRAL"         # Source neither supports nor contradicts → score: 0.5


class AuditStatus(str, Enum):
    PASS = "PASS"               # Faithfulness ≥ 0.85
    WARNING = "WARNING"         # Faithfulness 0.5 – 0.84
    FAIL = "FAIL"               # Faithfulness < 0.5


VERDICT_SCORES = {
    Verdict.ENTAIL: 1.0,
    Verdict.NEUTRAL: 0.5,
    Verdict.CONTRADICT: 0.0,
}


@dataclass
class ClaimResult:
    """Result for a single atomic claim extracted from the LLM response."""
    claim: str
    verdict: Verdict
    score: float
    source_evidence: str = ""   # The part of source that supports/contradicts
    confidence: float = 1.0


@dataclass
class AuditReport:
    """Full hallucination audit report for one source/question/answer triplet."""
    source: str
    question: str
    answer: str
    claims: List[ClaimResult] = field(default_factory=list)
    faithfulness_score: float = 0.0
    answer_relevancy_score: float = 0.0
    context_precision_score: float = 0.0
    status: AuditStatus = AuditStatus.FAIL
    total_claims: int = 0
    supported_claims: int = 0
    contradicted_claims: int = 0
    ungrounded_claims: int = 0

    def to_dict(self) -> dict:
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


# ─────────────────────────────────────────────
# CLAIM EXTRACTOR
# ─────────────────────────────────────────────

class ClaimExtractor:
    """
    Breaks an LLM response into atomic factual claims.

    Strategy: Use an LLM (Judge model) with a carefully engineered prompt
    to decompose the response into the smallest verifiable units.

    Example:
        Input:  "The Eiffel Tower is in Paris and was built in 1889."
        Output: ["The Eiffel Tower is in Paris.", "The Eiffel Tower was built in 1889."]
    """

    EXTRACTION_PROMPT = """You are a precise claim extractor. Your job is to break a given text into individual, atomic factual claims.

Rules:
- Each claim must be a single, verifiable statement
- Do not combine two facts into one claim
- Preserve the original meaning exactly — do not rephrase or add information
- Output ONLY a valid JSON array of strings — no explanation, no preamble
- If the text contains no verifiable claims, return an empty array: []

Text to extract claims from:
{answer}

Output format example:
["The Eiffel Tower is in Paris.", "It was built in 1889.", "It stands 330 metres tall."]

Your output:"""

    def __init__(self, model: str = "gpt-4o"):
        self.model = model

    def extract(self, answer: str) -> List[str]:
        """
        Extract atomic claims from an LLM answer.

        Args:
            answer: The LLM-generated response to decompose.

        Returns:
            List of atomic claim strings.

        TODO (Phase 1):
            - Call LLM API with EXTRACTION_PROMPT
            - Parse JSON response
            - Return list of claim strings
        """
        # PLACEHOLDER — to be implemented in Phase 1
        raise NotImplementedError(
            "ClaimExtractor.extract() not yet implemented. "
            "See ROADMAP.md Phase 1 for implementation plan."
        )


# ─────────────────────────────────────────────
# NLI VERIFIER
# ─────────────────────────────────────────────

class NLIVerifier:
    """
    Verifies each atomic claim against the source document using Natural Language Inference.

    Uses an LLM-as-Judge approach:
    - ENTAIL: the source directly supports the claim
    - CONTRADICT: the source says something different
    - NEUTRAL: the source is silent on this claim (ungrounded)

    This is the core of the RAG Triad 'Faithfulness' metric.
    """

    VERIFICATION_PROMPT = """You are a strict hallucination detector. Given a SOURCE document and a CLAIM, determine if the source supports, contradicts, or is silent on the claim.

SOURCE:
{source}

CLAIM:
{claim}

Your task: Classify the relationship as one of:
- ENTAIL: The source directly supports this claim
- CONTRADICT: The source says something different from this claim
- NEUTRAL: The source neither supports nor contradicts this claim (it's simply not mentioned)

Output ONLY valid JSON — no explanation:
{{"verdict": "ENTAIL" | "CONTRADICT" | "NEUTRAL", "evidence": "exact quote from source that led to this verdict, or empty string if NEUTRAL"}}

Your output:"""

    def __init__(self, model: str = "gpt-4o"):
        self.model = model

    def verify(self, claim: str, source: str) -> ClaimResult:
        """
        Verify a single claim against the source document.

        Args:
            claim: Atomic factual claim to verify.
            source: Ground truth source document.

        Returns:
            ClaimResult with verdict and score.

        TODO (Phase 1):
            - Call LLM API with VERIFICATION_PROMPT
            - Parse JSON: {"verdict": "...", "evidence": "..."}
            - Map verdict to Verdict enum and score
            - Return ClaimResult
        """
        # PLACEHOLDER — to be implemented in Phase 1
        raise NotImplementedError(
            "NLIVerifier.verify() not yet implemented. "
            "See ROADMAP.md Phase 1 for implementation plan."
        )

    def verify_all(self, claims: List[str], source: str) -> List[ClaimResult]:
        """Verify a list of claims against the source."""
        return [self.verify(claim, source) for claim in claims]


# ─────────────────────────────────────────────
# METRICS ENGINE
# ─────────────────────────────────────────────

class MetricsEngine:
    """
    Calculates the three RAG Triad metrics from verified claims.

    Faithfulness:
        supported_claims / total_claims
        Measures whether the LLM response is grounded in the source.

    Answer Relevancy:
        Does the answer actually address the question?
        Measured by LLM-as-Judge.

    Context Precision:
        Was the right context retrieved to begin with?
        In Phase 1: assumed to be 1.0 (user provides context manually).
        In Phase 2: will measure retriever quality.
    """

    def calculate_faithfulness(self, claim_results: List[ClaimResult]) -> float:
        """
        Faithfulness = sum(scores) / len(claims)

        ENTAIL → 1.0
        NEUTRAL → 0.5
        CONTRADICT → 0.0
        """
        if not claim_results:
            return 0.0
        total_score = sum(c.score for c in claim_results)
        return total_score / len(claim_results)

    def calculate_status(self, faithfulness: float) -> AuditStatus:
        """Map faithfulness score to a human-readable status."""
        if faithfulness >= 0.85:
            return AuditStatus.PASS
        elif faithfulness >= 0.50:
            return AuditStatus.WARNING
        else:
            return AuditStatus.FAIL

    def build_report(
        self,
        source: str,
        question: str,
        answer: str,
        claim_results: List[ClaimResult],
    ) -> AuditReport:
        """Assemble the full AuditReport from claim results."""
        faithfulness = self.calculate_faithfulness(claim_results)
        status = self.calculate_status(faithfulness)

        report = AuditReport(
            source=source,
            question=question,
            answer=answer,
            claims=claim_results,
            faithfulness_score=faithfulness,
            answer_relevancy_score=0.0,   # TODO: implement in Phase 1
            context_precision_score=1.0,  # assumed for Phase 1
            status=status,
            total_claims=len(claim_results),
            supported_claims=sum(1 for c in claim_results if c.verdict == Verdict.ENTAIL),
            contradicted_claims=sum(1 for c in claim_results if c.verdict == Verdict.CONTRADICT),
            ungrounded_claims=sum(1 for c in claim_results if c.verdict == Verdict.NEUTRAL),
        )
        return report


# ─────────────────────────────────────────────
# MAIN PIPELINE
# ─────────────────────────────────────────────

class HallucinationHunter:
    """
    Main pipeline: source + question + answer → AuditReport.

    Orchestrates:
        ClaimExtractor → NLIVerifier → MetricsEngine → AuditReport
    """

    def __init__(self, model: str = "gpt-4o"):
        self.extractor = ClaimExtractor(model=model)
        self.verifier = NLIVerifier(model=model)
        self.scorer = MetricsEngine()

    def audit(self, source: str, question: str, answer: str) -> AuditReport:
        """
        Run the full hallucination audit pipeline.

        Args:
            source: Ground truth document.
            question: The question that was asked of the LLM.
            answer: The LLM's response to audit.

        Returns:
            AuditReport with faithfulness score, claim breakdown, and status.
        """
        # Step 1: Extract atomic claims
        claims = self.extractor.extract(answer)

        # Step 2: Verify each claim against source
        claim_results = self.verifier.verify_all(claims, source)

        # Step 3: Calculate metrics and build report
        report = self.scorer.build_report(source, question, answer, claim_results)

        return report

    def audit_from_json(self, filepath: str) -> List[AuditReport]:
        """Run audit on a batch of examples from a JSON file."""
        with open(filepath, "r", encoding="utf-8") as f:
            examples = json.load(f)

        reports = []
        for ex in examples:
            report = self.audit(
                source=ex["source"],
                question=ex["question"],
                answer=ex["answer"],
            )
            reports.append(report)
        return reports


# ─────────────────────────────────────────────
# CLI ENTRY POINT
# ─────────────────────────────────────────────

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Hallucination Hunter — LLM Audit Tool")
    parser.add_argument("--input", type=str, help="Path to JSON input file")
    parser.add_argument("--source", type=str, help="Source document (ground truth)")
    parser.add_argument("--question", type=str, help="Question asked of LLM")
    parser.add_argument("--answer", type=str, help="LLM answer to audit")
    parser.add_argument("--model", type=str, default="gpt-4o", help="Judge model to use")
    args = parser.parse_args()

    hunter = HallucinationHunter(model=args.model)

    if args.input:
        print(f"\n🔍 Hallucination Hunter — Batch Audit\nInput: {args.input}\n")
        reports = hunter.audit_from_json(args.input)
        for i, report in enumerate(reports, 1):
            print(f"[{i}] Status: {report.status.value} | Faithfulness: {report.faithfulness_score:.2f}")
    elif args.source and args.question and args.answer:
        print("\n🔍 Hallucination Hunter — Single Audit\n")
        report = hunter.audit(args.source, args.question, args.answer)
        print(json.dumps(report.to_dict(), indent=2))
    else:
        print("Usage:")
        print("  python hallucination_hunter.py --input examples/golden_dataset.json")
        print("  python hallucination_hunter.py --source 'Source text' --question 'Q' --answer 'A'")
