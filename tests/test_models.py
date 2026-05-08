"""Unit tests for hallucination_hunter.models.

Tests the domain data structures: Verdict, AuditStatus, ClaimResult,
AuditReport. No LLM calls are made here.
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from hallucination_hunter.models import (
    AuditReport,
    AuditStatus,
    ClaimResult,
    Verdict,
    VERDICT_SCORES,
)


class TestVerdictScores:
    def test_entail_is_one(self):
        assert VERDICT_SCORES[Verdict.ENTAIL] == 1.0

    def test_contradict_is_zero(self):
        assert VERDICT_SCORES[Verdict.CONTRADICT] == 0.0

    def test_neutral_is_half(self):
        assert VERDICT_SCORES[Verdict.NEUTRAL] == 0.5

    def test_all_verdicts_present(self):
        for v in Verdict:
            assert v in VERDICT_SCORES


class TestClaimResult:
    def test_valid_construction(self):
        r = ClaimResult(claim="x", verdict=Verdict.ENTAIL, score=1.0)
        assert r.score == 1.0

    def test_empty_claim_raises(self):
        with pytest.raises(ValidationError):
            ClaimResult(claim="", verdict=Verdict.ENTAIL, score=1.0)

    def test_score_above_one_raises(self):
        with pytest.raises(ValidationError):
            ClaimResult(claim="x", verdict=Verdict.ENTAIL, score=1.1)

    def test_score_below_zero_raises(self):
        with pytest.raises(ValidationError):
            ClaimResult(claim="x", verdict=Verdict.CONTRADICT, score=-0.1)

    def test_default_evidence_empty(self):
        r = ClaimResult(claim="x", verdict=Verdict.NEUTRAL, score=0.5)
        assert r.source_evidence == ""

    def test_immutable(self):
        r = ClaimResult(claim="x", verdict=Verdict.NEUTRAL, score=0.5)
        with pytest.raises(Exception):
            r.claim = "y"  # type: ignore[misc]


class TestAuditReportProperties:
    def test_counts(self, entail_result, contradict_result, neutral_result):
        report = AuditReport(
            source="s", question="q", answer="a",
            claims=[entail_result, contradict_result, neutral_result],
            faithfulness_score=0.5,
            status=AuditStatus.WARNING,
        )
        assert report.total_claims == 3
        assert report.supported_claims == 1
        assert report.contradicted_claims == 1
        assert report.ungrounded_claims == 1

    def test_to_dict_has_required_keys(self, entail_result):
        report = AuditReport(
            source="s", question="q", answer="a",
            claims=[entail_result],
            faithfulness_score=1.0,
            status=AuditStatus.PASS,
        )
        d = report.to_dict()
        for key in ("status", "faithfulness_score", "summary", "claims"):
            assert key in d

    def test_to_dict_rounds_to_three_decimals(self):
        report = AuditReport(
            source="s", question="q", answer="a",
            faithfulness_score=0.666666,
            status=AuditStatus.WARNING,
        )
        assert report.to_dict()["faithfulness_score"] == 0.667

    def test_empty_claims(self):
        report = AuditReport(
            source="s", question="q", answer="a",
            faithfulness_score=0.0,
            status=AuditStatus.FAIL,
        )
        assert report.total_claims == 0
        assert report.to_dict()["claims"] == []
