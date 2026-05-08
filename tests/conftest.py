"""Shared pytest fixtures for the Hallucination Hunter test suite.

All LLM-dependent tests use ``FakeProvider`` so they run fully offline,
deterministically, and at zero API cost. ``FakeProvider`` returns scripted
responses in the order they are supplied, making multi-call test flows easy
to control and inspect.
"""

from __future__ import annotations

from collections.abc import Iterator

import pytest

from hallucination_hunter.models import VERDICT_SCORES, ClaimResult, Verdict
from hallucination_hunter.providers.base import LLMProvider


class FakeProvider(LLMProvider):
    """Deterministic LLM provider for unit testing.

    Accepts a list of response strings and returns them in order, one per
    ``call()`` invocation. Tracks every prompt received so tests can assert
    on what was sent to the provider.

    Args:
        responses: Ordered list of JSON strings to return on successive calls.

    Raises:
        RuntimeError: If ``call()`` is invoked after all responses are consumed.
    """

    def __init__(self, responses: list[str]) -> None:
        self.__dict__["api_key"] = "test-key"
        self.__dict__["model"] = "fake-model"
        self._responses = list(responses)
        self.calls: list[str] = []

    @property
    def name(self) -> str:
        return "fake"

    def call(self, prompt: str) -> str:
        self.calls.append(prompt)
        if not self._responses:
            raise RuntimeError(
                "FakeProvider has no more scripted responses. "
                "Add another response string to the list passed to make_fake_provider()."
            )
        return self._responses.pop(0)


@pytest.fixture
def make_fake_provider() -> Iterator[type[FakeProvider]]:
    """Factory fixture that returns the FakeProvider class.

    Usage in tests::

        def test_something(make_fake_provider):
            provider = make_fake_provider(['["claim 1"]', '{"verdict": "ENTAIL", "evidence": "x"}'])
            extractor = ClaimExtractor(provider)
            ...
    """
    yield FakeProvider


@pytest.fixture
def entail_result() -> ClaimResult:
    """A ClaimResult with ENTAIL verdict for use in model tests."""
    return ClaimResult(
        claim="The Eiffel Tower is in Paris.",
        verdict=Verdict.ENTAIL,
        score=VERDICT_SCORES[Verdict.ENTAIL],
        source_evidence="located in Paris, France",
    )


@pytest.fixture
def contradict_result() -> ClaimResult:
    """A ClaimResult with CONTRADICT verdict for use in model tests."""
    return ClaimResult(
        claim="The Eiffel Tower was built in 1900.",
        verdict=Verdict.CONTRADICT,
        score=VERDICT_SCORES[Verdict.CONTRADICT],
        source_evidence="constructed in 1889",
    )


@pytest.fixture
def neutral_result() -> ClaimResult:
    """A ClaimResult with NEUTRAL verdict for use in model tests."""
    return ClaimResult(
        claim="The Eiffel Tower has a restaurant.",
        verdict=Verdict.NEUTRAL,
        score=VERDICT_SCORES[Verdict.NEUTRAL],
        source_evidence="",
    )