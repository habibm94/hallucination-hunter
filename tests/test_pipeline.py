"""Integration tests for the metrics engine and end-to-end pipeline."""

from __future__ import annotations

import pytest

from hallucination_hunter.errors import InputError
from hallucination_hunter.metrics import MetricsEngine
from hallucination_hunter.models import (
    VERDICT_SCORES,
    AuditStatus,
    ClaimResult,
    Verdict,
)
from hallucination_hunter.pipeline import HallucinationHunter


# A neutral taxonomy response used by tests that don't care about tags.
_NO_TAGS = '{"types": []}'


def _claim(verdict: Verdict) -> ClaimResult:
    """Helper: create a minimal ClaimResult for a given verdict."""
    return ClaimResult(claim="placeholder", verdict=verdict, score=VERDICT_SCORES[verdict])


# A grounding document long enough to pass the 15-char minimum-source rule
# imposed by validate_source(). Used by tests that feed substantive inputs.
_SUBSTANTIVE_SOURCE = (
    "The Eiffel Tower is a wrought iron lattice tower built on the Champ "
    "de Mars in Paris, France."
)


class TestMetricsEngine:
    """Faithfulness arithmetic and status threshold mapping."""

    def test_empty_claims_score_zero(self) -> None:
        assert MetricsEngine.faithfulness([]) == 0.0

    def test_all_entailed_score_one(self) -> None:
        assert MetricsEngine.faithfulness([_claim(Verdict.ENTAIL)] * 3) == 1.0

    def test_all_contradicted_score_zero(self) -> None:
        assert MetricsEngine.faithfulness([_claim(Verdict.CONTRADICT)] * 3) == 0.0

    def test_mixed_score_averages_correctly(self) -> None:
        claims = [
            _claim(Verdict.ENTAIL),      # 1.0
            _claim(Verdict.NEUTRAL),     # 0.5
            _claim(Verdict.CONTRADICT),  # 0.0
        ]
        assert MetricsEngine.faithfulness(claims) == pytest.approx(0.5)

    @pytest.mark.parametrize(
        ("score", "expected"),
        [
            (1.00, AuditStatus.PASS),
            (0.85, AuditStatus.PASS),
            (0.84, AuditStatus.WARNING),
            (0.50, AuditStatus.WARNING),
            (0.49, AuditStatus.FAIL),
            (0.00, AuditStatus.FAIL),
        ],
    )
    def test_status_thresholds(self, score: float, expected: AuditStatus) -> None:
        assert MetricsEngine.status_for(score) == expected

    def test_build_report_populates_all_fields(self) -> None:
        claims = [_claim(Verdict.ENTAIL), _claim(Verdict.ENTAIL)]
        report = MetricsEngine.build_report("src", "q", "a", claims)

        assert report.source == "src"
        assert report.question == "q"
        assert report.answer == "a"
        assert report.faithfulness_score == 1.0
        assert report.status == AuditStatus.PASS
        assert report.total_claims == 2


class TestPipelineIntegration:
    """End-to-end pipeline tests using FakeProvider (no network calls).

    Pipeline call order per audit:
        1) ClaimExtractor   -> 1 LLM call (returns JSON array of claims)
        2) NLIVerifier      -> 1 call per claim (returns verdict + evidence)
        3) TaxonomyClassifier -> 1 call per non-ENTAIL claim (returns types)
                                 ENTAIL claims short-circuit (no LLM call)

    FakeProvider responses must be queued in exactly that order.
    """

    def test_fully_grounded_answer_passes(self, make_fake_provider) -> None:
        # 2 claims, both ENTAIL -> 1 extract + 2 verify + 0 taxonomy = 3 calls
        provider = make_fake_provider(
            [
                '["The Eiffel Tower is in Paris.", "It was built in 1889."]',
                '{"verdict": "ENTAIL", "evidence": "Eiffel Tower is in Paris"}',
                '{"verdict": "ENTAIL", "evidence": "constructed in 1889"}',
            ]
        )
        hunter = HallucinationHunter(_provider_instance=provider)

        report = hunter.audit(
            source="The Eiffel Tower is in Paris and was constructed in 1889.",
            question="Where and when was it built?",
            answer="The Eiffel Tower is in Paris and was built in 1889.",
        )

        assert report.status == AuditStatus.PASS
        assert report.faithfulness_score == 1.0
        assert report.supported_claims == 2
        assert report.contradicted_claims == 0
        # ENTAIL claims should have no hallucination tags.
        for claim in report.claims:
            assert claim.hallucination_tags == []

    def test_full_hallucination_fails(self, make_fake_provider) -> None:
        # 2 claims, both CONTRADICT -> 1 extract + 2 verify + 2 taxonomy = 5 calls
        provider = make_fake_provider(
            [
                '["Built in 1892.", "Located in London."]',
                '{"verdict": "CONTRADICT", "evidence": "built in 1889"}',
                '{"verdict": "CONTRADICT", "evidence": "in Paris"}',
                '{"types": [{"type": "TEMPORAL", "explanation": "1892 vs 1889"}, {"type": "INTRINSIC", "explanation": ""}]}',
                '{"types": [{"type": "ENTITY", "explanation": "London vs Paris"}, {"type": "INTRINSIC", "explanation": ""}]}',
            ]
        )
        hunter = HallucinationHunter(_provider_instance=provider)

        report = hunter.audit(
            source="The Eiffel Tower is in Paris and was built in 1889.",
            question="Where and when was it built?",
            answer="The Eiffel Tower was built in 1892 and is in London.",
        )

        assert report.status == AuditStatus.FAIL
        assert report.faithfulness_score == 0.0
        assert report.contradicted_claims == 2
        assert report.supported_claims == 0
        # Each contradicted claim should carry hallucination tags.
        assert all(len(c.hallucination_tags) > 0 for c in report.claims)

    def test_partial_grounding_produces_warning(self, make_fake_provider) -> None:
        # 3 claims: ENTAIL, ENTAIL, NEUTRAL
        # 1 extract + 3 verify + 1 taxonomy (only NEUTRAL classified) = 5 calls
        provider = make_fake_provider(
            [
                '["X is in Paris.", "X was built in 1889.", "X has 7M visitors."]',
                '{"verdict": "ENTAIL", "evidence": "in Paris"}',
                '{"verdict": "ENTAIL", "evidence": "built in 1889"}',
                '{"verdict": "NEUTRAL", "evidence": ""}',
                '{"types": [{"type": "EXTRINSIC", "explanation": ""}]}',
            ]
        )
        hunter = HallucinationHunter(_provider_instance=provider)

        report = hunter.audit(
            source="X is in Paris and was built in 1889.",
            question="Tell me about X.",
            answer="X is in Paris, built in 1889, and has 7M visitors.",
        )

        # (1.0 + 1.0 + 0.5) / 3 = 0.833
        assert report.faithfulness_score == pytest.approx(0.833, abs=0.001)
        assert report.status == AuditStatus.WARNING
        assert report.ungrounded_claims == 1

    def test_audit_batch_processes_multiple_examples(self, make_fake_provider) -> None:
        # Example 1: 1 claim, ENTAIL -> 1 extract + 1 verify + 0 taxonomy = 2 calls
        # Example 2: 1 claim, CONTRADICT -> 1 extract + 1 verify + 1 taxonomy = 3 calls
        provider = make_fake_provider(
            [
                '["claim A"]',
                '{"verdict": "ENTAIL", "evidence": "yes"}',
                '["claim B"]',
                '{"verdict": "CONTRADICT", "evidence": "no"}',
                '{"types": [{"type": "INTRINSIC", "explanation": ""}]}',
            ]
        )
        hunter = HallucinationHunter(_provider_instance=provider)

        examples = [
            {
                "source": "Bangladesh is a country in South Asia with capital Dhaka.",
                "question": "q1",
                "answer": "a1",
            },
            {
                "source": "The Bengali language is spoken by over 200 million people.",
                "question": "q2",
                "answer": "a2",
            },
        ]
        reports = hunter.audit_batch(examples)

        assert len(reports) == 2
        assert reports[0].status == AuditStatus.PASS
        assert reports[1].status == AuditStatus.FAIL

    def test_empty_answer_raises_input_error(self, make_fake_provider) -> None:
        """Empty answer should be caught by validate_answer() before the pipeline
        reaches claim extraction."""
        provider = make_fake_provider(["[]"])
        hunter = HallucinationHunter(_provider_instance=provider)

        with pytest.raises(InputError) as exc_info:
            hunter.audit(
                source=(
                    "This is a grounding document with enough text to pass the "
                    "minimum length validation rule."
                ),
                question="Any question?",
                answer="",
            )
        assert exc_info.value.detail.code == "HH-INPUT-005"
