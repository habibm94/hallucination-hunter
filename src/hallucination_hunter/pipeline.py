"""Main evaluation pipeline.

``HallucinationHunter`` is the single entry point for all audits. It wires
together ``ClaimExtractor``, ``NLIVerifier``, and ``MetricsEngine`` and
exposes a clean API for single audits, batch audits, and file-based use.

Every stage is wrapped in defensive error handling: any exception that
escapes a stage is converted into a typed ``HallucinationHunterError``
with a stable code. Callers should catch ``HallucinationHunterError`` and
read ``err.detail`` for structured display.
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
from hallucination_hunter.models import AuditReport
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
from hallucination_hunter.verification import NLIVerifier

load_dotenv()


class HallucinationHunter:
    """Orchestrates the full RAG Triad evaluation pipeline.

    Wires together three stateless components:
        1. ``ClaimExtractor``  — breaks the answer into atomic claims.
        2. ``NLIVerifier``     — checks each claim against the source.
        3. ``MetricsEngine``   — computes faithfulness and builds the report.

    Args:
        api_key: Provider API key. Falls back to the ``GEMINI_API_KEY``
            environment variable when omitted.
        provider: Provider name string (default: ``'gemini'``).
        model: Model identifier (default: ``gemini-2.5-flash-lite``).
        _provider_instance: Internal use only — pre-built provider, used
            by the UI and tests to avoid re-instantiating.

    Raises:
        AuthError: If no API key can be resolved.
        ProviderError: If the provider name is not registered.
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
                # create_provider raises ValueError for unknown provider name
                raise ProviderError(
                    make_error(
                        "HH-PROVIDER-001",
                        context={"provider": provider, "underlying": str(e)},
                        message_override=str(e),
                    )
                ) from e

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
            Complete :class:`AuditReport` with per-claim results and scores.

        Raises:
            InputError: One of the inputs failed validation.
            AuthError: Provider rejected the API key.
            RateLimitError: Provider rate limit hit.
            NetworkError: Connection or timeout failure.
            ParseError: LLM returned malformed output.
            SafetyError: Provider safety filter blocked the request.
            ProviderError: Provider unavailable or model unsupported.
            InternalError: Unexpected pipeline failure (should not occur
                in normal operation).
        """

        def _progress(msg: str) -> None:
            if progress_callback:
                try:
                    progress_callback(msg)
                except Exception:
                    # Never let a UI callback failure break the pipeline.
                    pass

        # ------- Stage 0: input validation (no LLM calls) -------
        for validator, value, label in (
            (validate_source, source, "source"),
            (validate_question, question, "question"),
            (validate_answer, answer, "answer"),
        ):
            err = validator(value)
            if err is not None:
                raise InputError(err)

        # ------- Stage 1: claim extraction -------
        _progress("Extracting claims…")
        try:
            claims = self._extractor.extract(answer)
        except HallucinationHunterError:
            raise  # already structured
        except Exception as e:
            raise self._wrap_provider_exception(e, stage="extraction") from e

        if not claims:
            raise ParseError(
                make_error(
                    "HH-PARSE-002",
                    context={"answer_length": len(answer)},
                )
            )

        # ------- Stage 2: NLI verification -------
        _progress(f"Verifying {len(claims)} claim(s)…")
        try:
            results = self._verifier.verify_all(claims, source)
        except HallucinationHunterError:
            raise
        except Exception as e:
            raise self._wrap_provider_exception(e, stage="verification") from e

        # ------- Stage 3: metrics (pure compute, no LLM) -------
        _progress("Calculating metrics…")
        try:
            return self._scorer.build_report(source, question, answer, results)
        except Exception as e:
            raise InternalError(
                make_error(
                    "HH-INTERNAL-001",
                    context={"stage": "metrics", "underlying": str(e)},
                )
            ) from e

    def audit_pair(
        self,
        source: str,
        question: str,
        answer_a: str,
        answer_b: str,
        progress_callback: Callable[[str], None] | None = None,
    ) -> tuple[AuditReport, AuditReport]:
        """Run two audits on the same source/question with different answers.

        Args:
            source: Ground-truth document.
            question: The question posed to the LLM.
            answer_a: First LLM response.
            answer_b: Second LLM response.
            progress_callback: Optional status callback.

        Returns:
            Tuple of ``(report_a, report_b)``.
        """

        def _cb_a(msg: str) -> None:
            if progress_callback:
                progress_callback(f"[A] {msg}")

        def _cb_b(msg: str) -> None:
            if progress_callback:
                progress_callback(f"[B] {msg}")

        report_a = self.audit(source, question, answer_a, progress_callback=_cb_a)
        report_b = self.audit(source, question, answer_b, progress_callback=_cb_b)
        return report_a, report_b

    def audit_batch(
        self,
        examples: list[dict],
        progress_callback: Callable[[int, int, str], None] | None = None,
    ) -> list[AuditReport]:
        """Audit a list of examples sequentially.

        Args:
            examples: List of dicts with keys ``source``, ``question``,
                ``answer``. An optional ``id`` key is used for logging.
            progress_callback: Called as ``(index, total, label)`` after
                each audit completes.

        Returns:
            List of :class:`AuditReport` objects in input order.

        Raises:
            HallucinationHunterError: Re-raised from the first failing
                example. Use ``audit_batch_safe`` for partial-success
                semantics (added in v1.5).
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
                try:
                    progress_callback(i, total, label)
                except Exception:
                    pass
        return reports

    def audit_from_file(self, path: str) -> list[AuditReport]:
        """Load a JSON batch file and audit all examples.

        The file must be a JSON array where each element contains at
        minimum the keys ``source``, ``question``, and ``answer``.

        Args:
            path: Path to a ``.json`` batch file.

        Returns:
            List of :class:`AuditReport` objects.
        """
        with open(path, encoding="utf-8") as fh:
            examples = json.load(fh)
        return self.audit_batch(examples)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _wrap_provider_exception(
        exc: Exception, *, stage: str
    ) -> HallucinationHunterError:
        """Map any exception from a provider/extractor/verifier call onto
        a typed :class:`HallucinationHunterError` with a stable code."""

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
            # Generic provider error — try to detect network/safety from message
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
            if any(
                t in msg for t in ("safety", "blocked", "harm", "filter")
            ):
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

        # Last resort: anything else is a bug.
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