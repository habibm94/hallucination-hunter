"""Unit tests for claim extraction and NLI verification services."""

from __future__ import annotations

from hallucination_hunter.extraction import ClaimExtractor
from hallucination_hunter.models import Verdict
from hallucination_hunter.verification import NLIVerifier


class TestClaimExtractor:
    """Behaviour of the ClaimExtractor service."""

    def test_extracts_clean_array(self, make_fake_provider) -> None:
        provider = make_fake_provider(['["claim 1", "claim 2"]'])
        extractor = ClaimExtractor(provider)

        claims = extractor.extract("some answer text")

        assert claims == ["claim 1", "claim 2"]
        assert len(provider.calls) == 1

    def test_handles_markdown_wrapped_response(self, make_fake_provider) -> None:
        provider = make_fake_provider(['```json\n["a", "b"]\n```'])
        extractor = ClaimExtractor(provider)

        assert extractor.extract("text") == ["a", "b"]

    def test_returns_empty_for_empty_answer(self, make_fake_provider) -> None:
        provider = make_fake_provider([])
        extractor = ClaimExtractor(provider)

        assert extractor.extract("") == []
        assert extractor.extract("   ") == []
        assert provider.calls == []

    def test_handles_unparseable_response(self, make_fake_provider) -> None:
        provider = make_fake_provider(["not json"])
        extractor = ClaimExtractor(provider)

        assert extractor.extract("text") == []

    def test_filters_blank_claims(self, make_fake_provider) -> None:
        provider = make_fake_provider(['["claim 1", "", "  ", "claim 2"]'])
        extractor = ClaimExtractor(provider)

        assert extractor.extract("text") == ["claim 1", "claim 2"]

    def test_non_list_response_returns_empty(self, make_fake_provider) -> None:
        provider = make_fake_provider(['{"error": "unexpected"}'])
        extractor = ClaimExtractor(provider)

        assert extractor.extract("text") == []


class TestNLIVerifier:
    """Behaviour of the NLIVerifier service."""

    def test_entail_verdict(self, make_fake_provider) -> None:
        provider = make_fake_provider(
            ['{"verdict": "ENTAIL", "evidence": "Paris is the capital."}']
        )
        verifier = NLIVerifier(provider)

        result = verifier.verify("Paris is in France.", "France's capital is Paris.")

        assert result.verdict == Verdict.ENTAIL
        assert result.score == 1.0
        assert result.source_evidence == "Paris is the capital."

    def test_contradict_verdict(self, make_fake_provider) -> None:
        provider = make_fake_provider(
            ['{"verdict": "CONTRADICT", "evidence": "built in 1889"}']
        )
        verifier = NLIVerifier(provider)

        result = verifier.verify("Built in 1892.", "Built in 1889.")

        assert result.verdict == Verdict.CONTRADICT
        assert result.score == 0.0

    def test_neutral_verdict(self, make_fake_provider) -> None:
        provider = make_fake_provider(['{"verdict": "NEUTRAL", "evidence": ""}'])
        verifier = NLIVerifier(provider)

        result = verifier.verify("X has 7M visitors.", "X is in Paris.")

        assert result.verdict == Verdict.NEUTRAL
        assert result.score == 0.5

    def test_unknown_verdict_defaults_to_neutral(self, make_fake_provider) -> None:
        provider = make_fake_provider(
            ['{"verdict": "MAYBE", "evidence": "something"}']
        )
        verifier = NLIVerifier(provider)

        result = verifier.verify("claim", "source")

        assert result.verdict == Verdict.NEUTRAL

    def test_unparseable_response_defaults_to_neutral(self, make_fake_provider) -> None:
        provider = make_fake_provider(["not valid json"])
        verifier = NLIVerifier(provider)

        result = verifier.verify("claim", "source")

        assert result.verdict == Verdict.NEUTRAL
        assert result.source_evidence == ""

    def test_verify_all_processes_each_claim(self, make_fake_provider) -> None:
        provider = make_fake_provider(
            [
                '{"verdict": "ENTAIL", "evidence": "x"}',
                '{"verdict": "CONTRADICT", "evidence": "y"}',
            ]
        )
        verifier = NLIVerifier(provider)

        results = verifier.verify_all(["claim 1", "claim 2"], "source")

        assert len(results) == 2
        assert results[0].verdict == Verdict.ENTAIL
        assert results[1].verdict == Verdict.CONTRADICT
