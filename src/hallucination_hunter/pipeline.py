"""Main evaluation pipeline.

``HallucinationHunter`` is the single entry point for all audits.
It wires together ``ClaimExtractor``, ``NLIVerifier``, and ``MetricsEngine``
and exposes a clean API for single audits, batch audits, and file-based use.
"""

from __future__ import annotations

import json
import os
from typing import Callable

from dotenv import load_dotenv

from hallucination_hunter.extraction import ClaimExtractor
from hallucination_hunter.metrics import MetricsEngine
from hallucination_hunter.models import AuditReport
from hallucination_hunter.providers import create_provider
from hallucination_hunter.providers.gemini import DEFAULT_GEMINI_MODEL
from hallucination_hunter.verification import NLIVerifier

load_dotenv()


class HallucinationHunter:
    """Orchestrates the full RAG Triad evaluation pipeline.

    Wires together three stateless components:
        1. ``ClaimExtractor``  — breaks the answer into atomic claims.
        2. ``NLIVerifier``     — checks each claim against the source.
        3. ``MetricsEngine``   — computes faithfulness and builds the report.

    The class is provider-agnostic: any provider name registered in
    ``hallucination_hunter.providers`` is accepted.

    Args:
        api_key: Provider API key. Falls back to the ``GEMINI_API_KEY``
            environment variable when omitted.
        provider: Provider name string (default: ``'gemini'``).
        model: Model identifier (default: ``gemini-2.5-flash-lite``).

    Raises:
        AuthenticationError: If no API key can be resolved.
        ValueError: If the provider name is not registered.

    Example::

        hunter = HallucinationHunter()
        report = hunter.audit(source="...", question="...", answer="...")
        print(report.faithfulness_score)
    """

    def __init__(
        self,
        api_key: str | None = None,
        provider: str = "gemini",
        model: str = DEFAULT_GEMINI_MODEL,
        _provider_instance=None,
    ) -> None:
        if _provider_instance is not None:
            self._llm = _provider_instance
        else:
            resolved_key = api_key or os.getenv("GEMINI_API_KEY", "")
            self._llm = create_provider(provider, resolved_key, model)
        self._extractor = ClaimExtractor(self._llm)
        self._verifier = NLIVerifier(self._llm)
        self._scorer = MetricsEngine()
        self.provider_name = provider
        self.model_name = model

    def audit(
        self,
        source: str,
        question: str,
        answer: str,
        progress_callback: Callable[[str], None] | None = None,
    ) -> AuditReport:
        """Run a complete hallucination audit on a single triplet.

        Args:
            source: Ground-truth document provided to the LLM.
            question: The question posed to the LLM.
            answer: The LLM response to audit.
            progress_callback: Optional callable receiving short status
                strings, used for UI progress indicators.

        Returns:
            Complete ``AuditReport`` with per-claim results and scores.
        """

        def _progress(msg: str) -> None:
            if progress_callback:
                progress_callback(msg)

        _progress("Extracting claims …")
        claims = self._extractor.extract(answer)

        _progress(f"Verifying {len(claims)} claim(s) …")
        results = self._verifier.verify_all(claims, source)

        _progress("Calculating metrics …")
        return self._scorer.build_report(source, question, answer, results)

    def audit_batch(
        self,
        examples: list[dict],
        progress_callback: Callable[[int, int, str], None] | None = None,
    ) -> list[AuditReport]:
        """Audit a list of examples.

        Args:
            examples: List of dicts with keys ``source``, ``question``,
                ``answer``. An optional ``id`` key is used for logging.
            progress_callback: Called as ``(index, total, label)`` after
                each audit completes.

        Returns:
            List of ``AuditReport`` objects in input order.
        """
        reports = []
        total = len(examples)
        for i, ex in enumerate(examples, 1):
            label = ex.get("id", f"case_{i}")
            report = self.audit(
                source=ex["source"],
                question=ex["question"],
                answer=ex["answer"],
            )
            reports.append(report)
            if progress_callback:
                progress_callback(i, total, label)
        return reports

    def audit_from_file(self, path: str) -> list[AuditReport]:
        """Load a JSON batch file and audit all examples.

        The file must be a JSON array where each element contains at
        minimum the keys ``source``, ``question``, and ``answer``.

        Args:
            path: Path to a ``.json`` batch file.

        Returns:
            List of ``AuditReport`` objects.
        """
        with open(path, encoding="utf-8") as fh:
            examples = json.load(fh)
        return self.audit_batch(examples)
