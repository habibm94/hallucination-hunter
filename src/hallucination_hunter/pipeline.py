"""Main evaluation pipeline.

``HallucinationHunter`` is the single entry point for all audits. It wires
together claim extraction, NLI verification, taxonomy classification, and
metrics into a defended pipeline where every stage handles its own errors
and emits structured codes on failure.
"""

from __future__ import annotations

import json
import os
from typing import Callable

from dotenv import load_dotenv

from hallucination_hunter.errors import (
    AuthError,
    HallucinationHunterError,
    InputError,
    InternalError,
    NetworkError,
    ParseError,
    ProviderError,
    RateLimitError,
    SafetyError,
    make_error,
    validate_answer,
    validate_question,
    validate_source,
)
from hallucination_hunter.extraction import ClaimExtractor
from hallucination_hunter.metrics import MetricsEngine
from hallucination_hunter.models import AuditReport, ClaimResult
from hallucination_hunter.providers import create_provider
from hallucination_hunter.providers.base import (
    AuthenticationError as ProviderAuthenticationError,
)
from hallucination_hunter.providers.base import (
    ProviderError as ProviderRuntimeError,
)
from hallucination_hunter.providers.base import (
    RateLimitError as ProviderRateLimitError,
)
from hallucination_hunter.providers.base import (
    ResponseParseError as ProviderParseError,
)
from hallucination_hunter.providers.gemini import DEFAULT_GEMINI_MODEL
from hallucination_hunter.taxonomy import TaxonomyClassifier
from hallucination_hunter.verification import NLIVerifier

load_dotenv()


class HallucinationHunter:
    """Orchestrates the full RAG Triad evaluation pipeline."""

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
            try:
                resolved_key = api_key or os.getenv("GEMINI_API_KEY", "")
                self._llm = create_provider(provider, resolved_key, model)
            except ProviderAuthenticationError as e:
                raise AuthError(
                    make_error(
                        "HH-AUTH-001",
                        context={"provider": provider, "underlying": str(e)},
                    )
                ) from e
            except ValueError as e:
                raise ProviderError(
                    make_error(
                        "HH-PROVIDER-001",
                        context={"provider": provider, "underlying": str(e)},
                        message_override=str(e),
                    )
                ) from e

        self._extractor = ClaimExtractor(self._llm)
        self._verifier = NLIVerifier(self._llm)
        self._classifier = TaxonomyClassifier(self._llm)
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
        """Run a complete hallucination audit on a single triplet."""

        def _progress(msg: str) -> None:
            if progress_callback:
                try:
                    progress_callback(msg)
                except Exception:
                    pass

        # Stage 0: input validation
        for validator, value in (
            (validate_source, source),
            (validate_question, question),
            (validate_answer, answer),
        ):
            err = validator(value)
            if err is not None:
                raise InputError(err)

        # Stage 1: claim extraction
        _progress("Extracting claims...")
        try:
            claims = self._extractor.extract(answer)
        except HallucinationHunterError:
            raise
        except Exception as e:
            raise self._wrap_provider_exception(e, stage="extraction") from e

        if not claims:
            raise ParseError(
                make_error(
                    "HH-PARSE-002",
                    context={"answer_length": len(answer)},
                )
            )

        # Stage 2: NLI verification
        _progress(f"Verifying {len(claims)} claim(s)...")
        try:
            verified_results = self._verifier.verify_all(claims, source)
        except HallucinationHunterError:
            raise
        except Exception as e:
            raise self._wrap_provider_exception(e, stage="verification") from e

        # Stage 2.5: taxonomy classification
        # Classify only claims that are not fully entailed (saves API calls).
        _progress(f"Classifying hallucination types...")
        try:
            results_with_tags = self._classify_tags(verified_results, source)
        except HallucinationHunterError:
            raise
        except Exception as e:
            raise self._wrap_provider_exception(e, stage="taxonomy") from e

        # Stage 3: metrics
        _progress("Calculating metrics...")
        try:
            return self._scorer.build_report(
                source, question, answer, results_with_tags
            )
        except Exception as e:
            raise InternalError(
                make_error(
                    "HH-INTERNAL-001",
                    context={"stage": "metrics", "underlying": str(e)},
                )
            ) from e

    def _classify_tags(
        self,
        verified_results: list[ClaimResult],
        source: str,
    ) -> list[ClaimResult]:
        """Run taxonomy classification and return new ClaimResults with tags.

        ClaimResult is frozen (Pydantic), so we rebuild each instance with
        the tags attached.
        """
        rebuilt: list[ClaimResult] = []
        for cr in verified_results:
            tags = self._classifier.classify(cr.claim, cr.verdict, source)
            rebuilt.append(
                ClaimResult(
                    claim=cr.claim,
                    verdict=cr.verdict,
                    score=cr.score,
                    source_evidence=cr.source_evidence,
                    hallucination_tags=tags,
                )
            )
        return rebuilt

    def audit_pair(
        self,
        source: str,
        question: str,
        answer_a: str,
        answer_b: str,
        progress_callback: Callable[[str], None] | None = None,
    ) -> tuple[AuditReport, AuditReport]:
        """A/B audit: same source and question, two answers, two reports.

        Args:
            source: Ground-truth document.
            question: Question posed to both answers.
            answer_a: First LLM response to audit.
            answer_b: Second LLM response to audit.
            progress_callback: Receives progress messages prefixed with
                '[A]' or '[B]' to identify which answer is being processed.

        Returns:
            Tuple (report_a, report_b).
        """
        def _a_progress(msg: str) -> None:
            if progress_callback:
                try:
                    progress_callback(f"[A] {msg}")
                except Exception:
                    pass

        def _b_progress(msg: str) -> None:
            if progress_callback:
                try:
                    progress_callback(f"[B] {msg}")
                except Exception:
                    pass

        report_a = self.audit(source, question, answer_a, _a_progress)
        report_b = self.audit(source, question, answer_b, _b_progress)
        return report_a, report_b

    def audit_batch(
        self,
        examples: list[dict],
        progress_callback: Callable[[int, int, str], None] | None = None,
    ) -> list[AuditReport]:
        """Audit a list of examples sequentially."""
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
                try:
                    progress_callback(i, total, label)
                except Exception:
                    pass
        return reports

    def audit_from_file(self, path: str) -> list[AuditReport]:
        """Load a JSON batch file and audit all examples."""
        with open(path, encoding="utf-8") as fh:
            examples = json.load(fh)
        return self.audit_batch(examples)

    @staticmethod
    def _wrap_provider_exception(
        exc: Exception, *, stage: str
    ) -> HallucinationHunterError:
        """Map any exception onto a typed HallucinationHunterError."""

        if isinstance(exc, ProviderAuthenticationError):
            return AuthError(
                make_error(
                    "HH-AUTH-002",
                    context={"stage": stage, "underlying": str(exc)},
                )
            )
        if isinstance(exc, ProviderRateLimitError):
            return RateLimitError(
                make_error(
                    "HH-RATE-001",
                    context={"stage": stage, "underlying": str(exc)},
                )
            )
        if isinstance(exc, ProviderParseError):
            return ParseError(
                make_error(
                    "HH-PARSE-001",
                    context={"stage": stage, "underlying": str(exc)},
                )
            )
        if isinstance(exc, ProviderRuntimeError):
            msg = str(exc).lower()
            if any(t in msg for t in ("timeout", "timed out", "deadline")):
                return NetworkError(
                    make_error(
                        "HH-NETWORK-002",
                        context={"stage": stage, "underlying": str(exc)},
                    )
                )
            if any(
                t in msg for t in ("connection", "unreachable", "dns", "network")
            ):
                return NetworkError(
                    make_error(
                        "HH-NETWORK-001",
                        context={"stage": stage, "underlying": str(exc)},
                    )
                )
            if any(t in msg for t in ("safety", "blocked", "harm", "filter")):
                return SafetyError(
                    make_error(
                        "HH-SAFETY-001",
                        context={"stage": stage, "underlying": str(exc)},
                    )
                )
            return ProviderError(
                make_error(
                    "HH-PROVIDER-001",
                    context={"stage": stage, "underlying": str(exc)},
                    message_override=str(exc),
                )
            )

        return InternalError(
            make_error(
                "HH-INTERNAL-001",
                context={
                    "stage": stage,
                    "exc_type": type(exc).__name__,
                    "underlying": str(exc),
                },
            )
        )
